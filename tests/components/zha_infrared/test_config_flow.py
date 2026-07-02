"""Tests for the ZHA Infrared config flow."""

from unittest.mock import patch

from homeassistant.components.zha_infrared.const import (
    CONF_DEVICE,
    CONF_ENDPOINT_ID,
    CONF_IEEE,
    DOMAIN,
)
from homeassistant.components.zha_infrared.helpers import SupportedDevice
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_user_flow_aborts_without_zha(hass: HomeAssistant) -> None:
    """Abort when ZHA is not configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_zha"


async def test_user_flow_aborts_without_supported_devices(hass: HomeAssistant) -> None:
    """Abort when no TS1201-like devices are discovered."""
    MockConfigEntry(domain="zha", data={}).add_to_hass(hass)

    with patch(
        "homeassistant.components.zha_infrared.config_flow.get_supported_devices",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_supported_devices"


async def test_user_flow_create_entry(hass: HomeAssistant) -> None:
    """Create a config entry for a discovered TS1201-like device."""
    MockConfigEntry(domain="zha", data={}).add_to_hass(hass)
    device = SupportedDevice(
        key="8c:65:a3:ff:fe:92:63:ce:1",
        label="Living Room TS1201",
        ieee="8c:65:a3:ff:fe:92:63:ce",
        endpoint_id=1,
    )

    with (
        patch(
            "homeassistant.components.zha_infrared.config_flow.get_supported_devices",
            return_value=[device],
        ),
        patch(
            "homeassistant.components.zha_infrared.config_flow.get_supported_device_by_key",
            return_value=device,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_DEVICE: device.key},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room TS1201 IR"
    assert result["data"] == {
        CONF_IEEE: "8c:65:a3:ff:fe:92:63:ce",
        CONF_ENDPOINT_ID: 1,
    }


async def test_user_flow_aborts_when_already_configured(hass: HomeAssistant) -> None:
    """Abort when the selected device unique id is already configured."""
    MockConfigEntry(domain="zha", data={}).add_to_hass(hass)
    device = SupportedDevice(
        key="8c:65:a3:ff:fe:92:63:ce:1",
        label="Living Room TS1201",
        ieee="8c:65:a3:ff:fe:92:63:ce",
        endpoint_id=1,
    )
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{device.ieee}-{device.endpoint_id}",
        data={CONF_IEEE: device.ieee, CONF_ENDPOINT_ID: device.endpoint_id},
    ).add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.zha_infrared.config_flow.get_supported_devices",
            return_value=[device],
        ),
        patch(
            "homeassistant.components.zha_infrared.config_flow.get_supported_device_by_key",
            return_value=device,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_DEVICE: device.key},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
