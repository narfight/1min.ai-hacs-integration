from __future__ import annotations

import logging
import time
from typing import Literal

from homeassistant.components import conversation
from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
    default_agent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .api import OneMinAIClient, OneMinAIError
from .const import (
    CONF_HISTORY_LIMIT,
    CONF_LOCAL_CONTROL,
    CONF_MAX_WORD,
    CONF_MODEL,
    CONF_NUM_OF_SITE,
    CONF_SYSTEM_PROMPT,
    CONF_WEB_SEARCH,
    CONVERSATION_CACHE_TTL,
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_LOCAL_CONTROL,
    DEFAULT_MAX_WORD,
    DEFAULT_MODEL,
    DEFAULT_NUM_OF_SITE,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_WEB_SEARCH,
    DOMAIN,
    MAX_CONVERSATION_CACHE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the conversation entity."""
    client: OneMinAIClient = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OneMinAIConversationEntity(entry, client)])


class OneMinAIConversationEntity(ConversationEntity):
    """1min.ai conversation agent entity with local home control."""

    _attr_has_entity_name = True
    _attr_name = None
    # Déclare que cet agent peut contrôler la maison : c'est ce flag qui
    # fait disparaître le message "Cet assistant ne peut pas contrôler
    # votre maison."
    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(self, entry: ConfigEntry, client: OneMinAIClient) -> None:
        """Initialize the agent."""
        self._entry = entry
        self._client = client
        self._attr_unique_id = entry.entry_id
        # HA conversation_id -> (1min.ai conversation uuid, last_used_timestamp)
        self._remote_conversations: dict[str, tuple[str | None, float]] = {}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """The underlying LLMs are multilingual."""
        return MATCH_ALL

    def _cleanup_conversation_cache(self) -> None:
        """Remove expired and excess conversations from cache."""
        now = time.time()
        # Remove TTL-expired entries
        expired = [
            conv_id
            for conv_id, (_, timestamp) in self._remote_conversations.items()
            if now - timestamp > CONVERSATION_CACHE_TTL
        ]
        for conv_id in expired:
            del self._remote_conversations[conv_id]
            _LOGGER.debug("Expired conversation from cache: %s", conv_id)

        # Remove oldest if cache exceeds max size
        if len(self._remote_conversations) > MAX_CONVERSATION_CACHE:
            oldest = min(
                self._remote_conversations.items(),
                key=lambda x: x[1][1],
            )
            del self._remote_conversations[oldest[0]]
            _LOGGER.warning(
                "Conversation cache exceeded %d entries, removed oldest",
                MAX_CONVERSATION_CACHE,
            )

    async def async_added_to_hass(self) -> None:
        """Register the agent when added."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self._entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister the agent when removed."""
        conversation.async_unset_agent(self.hass, self._entry)
        await super().async_will_remove_from_hass()

    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        """Process a sentence from Assist.

        Stratégie "local d'abord" :
        1. On tente de résoudre la phrase avec l'agent local de Home
           Assistant (intents Assist : allumer/éteindre, scènes, etc.).
           Si une intention domotique est reconnue, elle est exécutée
           et sa réponse est renvoyée.
        2. Sinon, la phrase est envoyée à 1min.ai comme conversation
           libre.
        """
        options = self._entry.options

        if options.get(CONF_LOCAL_CONTROL, DEFAULT_LOCAL_CONTROL):
            try:
                local_result = await self._async_try_local_intents(user_input)
                if local_result is not None:
                    return local_result
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning(
                    "Local intent processing failed: %s, falling back to LLM",
                    err,
                    exc_info=False,
                )

        return await self._async_process_llm(user_input)

    async def _async_try_local_intents(
        self, user_input: ConversationInput
    ) -> ConversationResult | None:
        """Try to handle the sentence with the built-in Assist agent.

        Returns None when no local intent matched, so the caller falls
        back to the LLM.
        """
        try:
            agent = default_agent.async_get_default_agent(self.hass)
            result = await agent.async_process(user_input)
        except (RuntimeError, ValueError, KeyError) as err:
            _LOGGER.debug(
                "Local intent processing failed (%s), falling back to LLM: %s",
                type(err).__name__,
                err,
            )
            return None

        response = result.response
        if (
            response.response_type == intent.IntentResponseType.ERROR
            and response.error_code
            == intent.IntentResponseErrorCode.NO_INTENT_MATCH
        ):
            # Rien de domotique reconnu -> on laisse le LLM répondre
            return None

        _LOGGER.debug("Handled locally by Assist intents: %s", user_input.text)
        return result

    async def _async_process_llm(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        """Send the sentence to 1min.ai."""
        options = self._entry.options
        model = options.get(CONF_MODEL, DEFAULT_MODEL)
        system_prompt = options.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT)

        # Reuse or create HA-side conversation id
        if user_input.conversation_id:
            conversation_id = user_input.conversation_id
        else:
            conversation_id = ulid.ulid_now()

        # Clean up expired/excess conversations
        self._cleanup_conversation_cache()

        # Reuse or create the remote 1min.ai conversation for history
        is_new = conversation_id not in self._remote_conversations
        if is_new:
            remote_id = await self._client.create_conversation(
                f"Home Assistant {conversation_id[:8]}"
            )
            self._remote_conversations[conversation_id] = (remote_id, time.time())
            _LOGGER.debug("Created new conversation: %s", conversation_id)
        else:
            # Update timestamp on existing conversation
            remote_id, _ = self._remote_conversations[conversation_id]
            self._remote_conversations[conversation_id] = (remote_id, time.time())
            _LOGGER.debug("Reusing conversation: %s", conversation_id)

        # Prepend the system prompt on the first turn only
        prompt = user_input.text
        if is_new and system_prompt:
            prompt = f"[System instructions: {system_prompt}]\n\n{prompt}"

        intent_response = intent.IntentResponse(language=user_input.language)
        try:
            answer = await self._client.chat(
                prompt=prompt,
                model=model,
                conversation_id=remote_id,
                web_search=options.get(CONF_WEB_SEARCH, DEFAULT_WEB_SEARCH),
                num_of_site=int(
                    options.get(CONF_NUM_OF_SITE, DEFAULT_NUM_OF_SITE)
                ),
                max_word=int(options.get(CONF_MAX_WORD, DEFAULT_MAX_WORD)),
                history_limit=int(
                    options.get(CONF_HISTORY_LIMIT, DEFAULT_HISTORY_LIMIT)
                ),
            )
        except OneMinAIError as err:
            _LOGGER.error("1min.ai request failed: %s", err)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Erreur 1min.ai : {err}",
            )
            return ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        intent_response.async_set_speech(answer)
        return ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )