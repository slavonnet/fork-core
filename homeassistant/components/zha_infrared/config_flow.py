"""Config flow for ZHA Infrared."""

from typing import Any, override

import voluptuous as vol

from homeassistant.components.zha.const import DOMAIN as ZHA_DOMAIN
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import SelectOptionDict, SelectSelector, SelectSelectorConfig

from .const import CONF_DEVICE, CONF_ENDPOINT_ID, CONF_IEEE, DOMAIN
from .helpers import get_supported_device_by_key, get_supported_devices


class ZhaInfraredConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for ZHA Infrared."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step."""
        if not self.hass.config_entries.async_entries(ZHA_DOMAIN):
            return self.async_abort(reason="no_zha")

        supported_devices = get_supported_devices(self.hass)
        if not supported_devices:
            return self.async_abort(reason="no_supported_devices")

        errors: dict[str, str] = {}
        if user_input is not None:
            selected_device = get_supported_device_by_key(
                self.hass, user_input[CONF_DEVICE]
            )
            if selected_device is None:
                errors["base"] = "device_not_found"
            else:
                await self.async_set_unique_id(
                    f"{selected_device.ieee}-{selected_device.endpoint_id}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{selected_device.label} IR",
                    data={
                        CONF_IEEE: selected_device.ieee,
                        CONF_ENDPOINT_ID: selected_device.endpoint_id,
                    },
                )

        options = [
            SelectOptionDict(value=device.key, label=device.label)
            for device in supported_devices
        ]
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE): SelectSelector(
                        SelectSelectorConfig(options=options)
                    )
                }
            ),
            errors=errors,
        )
