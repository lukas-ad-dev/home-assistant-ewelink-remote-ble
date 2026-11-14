"""Constants for eWeLink Remote BLE."""

DOMAIN = "ewelink_remote_ble"
EVENT_BUTTON = "ewelink_remote_ble.button"
CONF_SUBTYPE = "subtype"
CONF_REMOTE_ID = "remote_id"
CONF_DEVICE_TYPE = "device_type"

DATA_CONFIGURED_DEVICES = "configured_devices"
DATA_CONFIRMATION_WAITERS = "confirmation_waiters"
DATA_DISCOVERY_TIMESTAMPS = "discovery_timestamps"
DATA_ENTRIES = "entries"
DATA_SCANNER_CANCEL = "scanner_cancel"

BUTTON_TYPES = tuple(f"button_{number}" for number in range(1, 7))
TRIGGER_SUBTYPES = (
    "single",
    "double",
    "hold_start",
    "hold_repeat",
    "hold_release",
)
