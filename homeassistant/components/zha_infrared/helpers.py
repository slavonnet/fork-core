"""Helper utilities for ZHA Infrared."""

from base64 import b64encode
from dataclasses import dataclass
import struct
from typing import Any

from zigpy.types.named import EUI64

from homeassistant.components.zha.helpers import get_zha_gateway_proxy
from homeassistant.core import HomeAssistant

from .const import TS1201_MODEL, TUYA_CLUSTER_IR_CONTROL, TUYA_CLUSTER_IR_TRANSMIT


@dataclass(slots=True)
class SupportedDevice:
    """A supported TS1201-like IR bridge device."""

    name: str
    ieee: str
    endpoint_id: int


def encode_raw_to_tuya_base64(timings: list[int]) -> str:
    """Encode signed raw timings to the Tuya TS1201 base64 payload format."""
    payload = bytearray()
    for timing in timings:
        # Tuya payload uses uint16 durations; values beyond uint16 are saturated.
        duration = min(abs(timing), 0xFFFF)
        payload.extend(struct.pack("<H", duration))
    return b64encode(payload).decode("ascii")


def get_supported_devices(hass: HomeAssistant) -> list[SupportedDevice]:
    """Return TS1201-like devices discovered by ZHA."""
    try:
        gateway_proxy = get_zha_gateway_proxy(hass)
    except ValueError:
        return []

    devices: list[SupportedDevice] = []
    for proxy in gateway_proxy.device_proxies.values():
        device = proxy.device
        model = device.model or ""
        name = device.name or f"Device {device.ieee}"
        ieee = str(device.ieee)

        for endpoint_id, endpoint in device.device.endpoints.items():
            if endpoint_id == 0:
                continue
            if not _is_ts1201_like(model, endpoint):
                continue

            devices.append(
                SupportedDevice(
                    name=name,
                    ieee=ieee,
                    endpoint_id=endpoint_id,
                )
            )

    return sorted(
        devices, key=lambda item: (item.name.casefold(), item.ieee, item.endpoint_id)
    )


def get_ir_control_cluster(
    hass: HomeAssistant, ieee: str, endpoint_id: int
) -> Any | None:
    """Resolve the TS1201 IR control cluster for a configured endpoint."""
    try:
        gateway_proxy = get_zha_gateway_proxy(hass)
    except ValueError:
        return None

    device_proxy = gateway_proxy.get_device_proxy(EUI64.convert(ieee))
    if device_proxy is None:
        return None

    endpoint = device_proxy.device.device.endpoints.get(endpoint_id)
    if endpoint is None:
        return None

    return endpoint.in_clusters.get(TUYA_CLUSTER_IR_CONTROL)


def _is_ts1201_like(model: str, endpoint: Any) -> bool:
    """Check whether endpoint clusters match TS1201 IR transport pattern."""
    if model == TS1201_MODEL:
        return True
    return (
        TUYA_CLUSTER_IR_CONTROL in endpoint.in_clusters
        and TUYA_CLUSTER_IR_TRANSMIT in endpoint.in_clusters
    )
