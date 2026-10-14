"""Config flow for the Helios KWL EC 300 integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from ._core import AuthenticationError, HeliosError, Info
from .const import (
    CONF_PARTY_DURATION,
    CONF_PARTY_FAN_STAGE,
    CONF_SCAN_INTERVAL,
    DEFAULT_PARTY_DURATION_MINUTES,
    DEFAULT_PARTY_FAN_STAGE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ValidationResult:
    """Resolved metadata from a successful connection validation."""

    title: str
    unique_id: str


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> ValidationResult:
    """Validate user input by connecting to the device."""
    del hass
    api = Info(
        host=data[CONF_HOST],
        password=data[CONF_PASSWORD],
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    snapshot = await api.validate_connection()
    identity = snapshot.identity

    unique_id = (
        identity.unique_id
        if identity is not None and identity.unique_id is not None
        else str(data[CONF_HOST]).lower()
    )
    if identity is not None and identity.model is not None:
        title = f"{identity.model} ({data[CONF_HOST]})"
    else:
        title = str(data[CONF_HOST])

    return ValidationResult(title=title, unique_id=unique_id)


class HeliosConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Helios ventilation unit."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                validation = await validate_input(self.hass, user_input)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except HeliosError:
                errors["base"] = "cannot_connect"
            except Exception:  # pragma: no cover - defensive guard for HA logs
                _LOGGER.exception("Unexpected exception during Helios config flow")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(validation.unique_id)
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    }
                )
                return self.async_create_entry(
                    title=validation.title,
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                    options={
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_PARTY_DURATION: user_input[CONF_PARTY_DURATION],
                        CONF_PARTY_FAN_STAGE: user_input[CONF_PARTY_FAN_STAGE],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default="helios.local"): str,
                    vol.Required(CONF_PASSWORD, default="!helios!"): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL_SECONDS,
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                    vol.Required(
                        CONF_PARTY_DURATION,
                        default=DEFAULT_PARTY_DURATION_MINUTES,
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=180)),
                    vol.Required(
                        CONF_PARTY_FAN_STAGE,
                        default=DEFAULT_PARTY_FAN_STAGE,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
                }
            ),
            errors=errors,
        )
