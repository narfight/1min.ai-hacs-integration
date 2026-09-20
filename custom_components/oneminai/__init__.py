from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OneMinAIAuthError, OneMinAIClient, OneMinAIError
from .const import (
    ATTR_CONVERSATION_ID,
    ATTR_IMAGES,
    ATTR_MODEL,
    ATTR_PROMPT,
    ATTR_WEB_SEARCH,
    CONF_API_KEY,
    CONF_MODEL,
    DEFAULT_MODEL,
    DOMAIN,
    SERVICE_ASK,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CONVERSATION]

SERVICE_ASK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PROMPT): cv.string,
        vol.Optional(ATTR_MODEL): cv.string,
        vol.Optional(ATTR_WEB_SEARCH, default=False): cv.boolean,
        vol.Optional(ATTR_IMAGES): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_CONVERSATION_ID): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 1min.ai from a config entry."""
    session = async_get_clientsession(hass)
    client = OneMinAIClient(session, entry.data[CONF_API_KEY])

    try:
        await client.validate(entry.options.get(CONF_MODEL, DEFAULT_MODEL))
    except OneMinAIAuthError as err:
        raise ConfigEntryAuthFailed("Invalid 1min.ai API key") from err
    except OneMinAIError as err:
        _LOGGER.warning("Could not validate 1min.ai on startup: %s", err)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def handle_ask(call: ServiceCall) -> ServiceResponse:
        """Handle the oneminai.ask service."""
        try:
            answer = await client.chat(
                prompt=call.data[ATTR_PROMPT],
                model=call.data.get(
                    ATTR_MODEL, entry.options.get(CONF_MODEL, DEFAULT_MODEL)
                ),
                web_search=call.data.get(ATTR_WEB_SEARCH, False),
                images=call.data.get(ATTR_IMAGES),
                conversation_id=call.data.get(ATTR_CONVERSATION_ID),
            )
        except OneMinAIError as err:
            raise HomeAssistantError(f"1min.ai error: {err}") from err
        return {"response": answer}

    hass.services.async_register(
        DOMAIN,
        SERVICE_ASK,
        handle_ask,
        schema=SERVICE_ASK_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_ASK)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)