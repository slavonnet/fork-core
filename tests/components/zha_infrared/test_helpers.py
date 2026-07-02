"""Tests for ZHA Infrared helpers."""

from homeassistant.components.zha_infrared.helpers import encode_raw_to_tuya_base64


def test_encode_raw_to_tuya_base64_saturates_and_encodes() -> None:
    """Test raw timing conversion to TS1201 base64 payload."""
    assert encode_raw_to_tuya_base64([100, -200, 70000]) == "ZADIAP//"
