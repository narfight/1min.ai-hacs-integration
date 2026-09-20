from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import OneMinAIAuthError, OneMinAIClient, OneMinAIError
from .const import (
    CONF_API_KEY,
    CONF_HISTORY_LIMIT,
    CONF_LOCAL_CONTROL,
    CONF_MAX_WORD,
    CONF_MODEL,
    CONF_NUM_OF_SITE,
    CONF_REQUEST_TIMEOUT,
    CONF_SYSTEM_PROMPT,
    CONF_WEB_SEARCH,
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_LOCAL_CONTROL,
    DEFAULT_MAX_WORD,
    DEFAULT_MODEL,
    DEFAULT_NUM_OF_SITE,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_WEB_SEARCH,
    DOMAIN,
    SUPPORTED_MODELS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
    }
)


class OneMinAIConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 1min.ai."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = OneMinAIClient(session, user_input[CONF_API_KEY])
            try:
                await client.validate(DEFAULT_MODEL)
            except OneMinAIAuthError:
                errors["base"] = "invalid_auth"
            except OneMinAIError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="1min.ai",
                    data=user_input,
                    options={
                        CONF_MODEL: DEFAULT_MODEL,
                        CONF_SYSTEM_PROMPT: DEFAULT_SYSTEM_PROMPT,
                        CONF_WEB_SEARCH: DEFAULT_WEB_SEARCH,
                        CONF_NUM_OF_SITE: DEFAULT_NUM_OF_SITE,
                        CONF_MAX_WORD: DEFAULT_MAX_WORD,
                        CONF_HISTORY_LIMIT: DEFAULT_HISTORY_LIMIT,
                        CONF_LOCAL_CONTROL: DEFAULT_LOCAL_CONTROL,
                        CONF_REQUEST_TIMEOUT: DEFAULT_REQUEST_TIMEOUT,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return OneMinAIOptionsFlow()


class OneMinAIOptionsFlow(OptionsFlow):
    """Handle options for 1min.ai."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MODEL,
                    default=options.get(CONF_MODEL, DEFAULT_MODEL),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=SUPPORTED_MODELS,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_SYSTEM_PROMPT,
                    default=options.get(
                        CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT
                    ),
                ): TextSelector(TextSelectorConfig(multiline=True)),
                vol.Required(
                    CONF_LOCAL_CONTROL,
                    default=options.get(
                        CONF_LOCAL_CONTROL, DEFAULT_LOCAL_CONTROL
                    ),
                ): BooleanSelector(),
                vol.Required(
                    CONF_WEB_SEARCH,
                    default=options.get(CONF_WEB_SEARCH, DEFAULT_WEB_SEARCH),
                ): BooleanSelector(),
                vol.Required(
                    CONF_NUM_OF_SITE,
                    default=options.get(CONF_NUM_OF_SITE, DEFAULT_NUM_OF_SITE),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=10, mode=NumberSelectorMode.SLIDER
                    )
                ),
                vol.Required(
                    CONF_MAX_WORD,
                    default=options.get(CONF_MAX_WORD, DEFAULT_MAX_WORD),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=100, max=5000, step=100, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_HISTORY_LIMIT,
                    default=options.get(
                        CONF_HISTORY_LIMIT, DEFAULT_HISTORY_LIMIT
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=50, mode=NumberSelectorMode.SLIDER
                    )
                ),
                vol.Required(
                    CONF_REQUEST_TIMEOUT,
                    default=options.get(
                        CONF_REQUEST_TIMEOUT, DEFAULT_REQUEST_TIMEOUT
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=10, max=120, step=10, mode=NumberSelectorMode.BOX
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)