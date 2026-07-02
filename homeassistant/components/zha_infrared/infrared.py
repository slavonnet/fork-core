"""Infrared platform for ZHA TS1201-like hubs."""

from typing import override

from homeassistant.components.infrared import InfraredCommand, InfraredEmitterEntity
from homeassistant.components.zha.const import DOMAIN as ZHA_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_ENDPOINT_ID,
    CONF_IEEE,
    DOMAIN,
    TUYA_IR_SEND_COMMAND_ID,
)
from .helpers import encode_raw_to_tuya_base64, get_ir_control_cluster

PARALLEL_UPDATES = 1


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up ZHA infrared entity from a config entry."""
    async_add_entities(
        [
            ZhaInfraredEmitterEntity(
                ieee=entry.data[CONF_IEEE],
                endpoint_id=entry.data[CONF_ENDPOINT_ID],
            )
        ]
    )


class ZhaInfraredEmitterEntity(InfraredEmitterEntity):
    """Proxy infrared emitter backed by a ZHA TS1201-like hub."""

    _attr_has_entity_name = True
    _attr_translation_key = "infrared_emitter"

    def __init__(self, ieee: str, endpoint_id: int) -> None:
        """Initialize the emitter entity."""
        self._ieee = ieee
        self._endpoint_id = endpoint_id
        self._attr_unique_id = f"{ieee}-{endpoint_id}-infrared-emitter"

    @property
    def available(self) -> bool:
        """Return whether the underlying ZHA device is currently available."""
        cluster = get_ir_control_cluster(self.hass, self._ieee, self._endpoint_id)
        if cluster is None:
            return False
        return cluster.endpoint.device.available

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Associate this entity with the underlying ZHA device."""
        return {
            "identifiers": {(ZHA_DOMAIN, self._ieee)},
            "connections": {(dr.CONNECTION_ZIGBEE, self._ieee)},
        }

    @override
    async def async_send_command(self, command: InfraredCommand) -> None:
        """Send an infrared command over TS1201 Tuya cluster transport."""
        cluster = get_ir_control_cluster(self.hass, self._ieee, self._endpoint_id)
        if cluster is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="ir_cluster_missing",
            )

        payload = encode_raw_to_tuya_base64(command.get_raw_timings())
        try:
            await cluster.command(TUYA_IR_SEND_COMMAND_ID, payload, expect_reply=True)
        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="send_command_failed",
                translation_placeholders={"error": str(err)},
            ) from err
