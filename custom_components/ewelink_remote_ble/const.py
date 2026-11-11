"""Constants for eWeLink Remote BLE."""

DOMAIN = "ewelink_remote_ble"
EVENT_BUTTON = "ewelink_remote_ble.button"
CONF_SUBTYPE = "subtype"
SIGNAL_DEVICE_DISCOVERED = f"{DOMAIN}_device_discovered"

BUTTON_TYPES = tuple(f"button_{number}" for number in range(1, 7))
TRIGGER_SUBTYPES = (
    "single",
    "double",
    "hold_start",
    "hold_repeat",
    "hold_release",
)
