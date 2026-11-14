"""Decode SONOFF eWeLink-Remote BLE advertisements in Home Assistant."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_call_later

from .const import (
    CONF_DEVICE_TYPE,
    CONF_REMOTE_ID,
    DATA_CONFIGURED_DEVICES,
    DATA_CONFIRMATION_WAITERS,
    DATA_DISCOVERY_TIMESTAMPS,
    DATA_ENTRIES,
    DATA_SCANNER_CANCEL,
    DOMAIN,
    EVENT_BUTTON,
)

_LOGGER = logging.getLogger(__name__)

# Publicly documented by the Tasmota-eWeLinkRemote project.
_XOR_TABLE = (
    15,
    57,
    190,
    95,
    39,
    5,
    190,
    249,
    102,
    181,
    116,
    13,
    4,
    134,
    210,
    97,
    85,
    187,
    252,
    22,
    52,
    64,
    126,
    29,
    56,
    110,
    228,
    6,
    170,
    121,
    50,
    149,
    102,
    181,
    116,
    13,
    219,
    140,
    233,
    1,
    42,
)
_ACTIONS = ("single", "double", "hold")
_TYPES = {0x46: "S-MATE2", 0x47: "R5"}

# R5 hold packets can be more than 1.2 seconds apart through remote BLE proxies.
_HOLD_RELEASE_DELAY = 1.6
PLATFORMS = [Platform.EVENT]
_DISCOVERY_THROTTLE = 30.0


def _decode(raw: bytes) -> dict[str, Any] | None:
    """Return a decoded eWeLink-Remote advertisement or None."""
    if len(raw) < 31:
        return None
    if raw[4:9] != bytes((0x05, 0xFF, 0xFF, 0xEE, 0x1B)):
        return None

    device_type = _TYPES.get(raw[13])
    if device_type is None:
        return None

    seed = raw[20]
    decrypted = bytes(
        raw[21 + index] ^ (_XOR_TABLE[index] ^ seed) for index in range(10)
    )
    action_index = decrypted[2]
    if action_index >= len(_ACTIONS):
        return None

    button = decrypted[1] + 1
    max_buttons = 6 if device_type == "R5" else 3
    if not 1 <= button <= max_buttons:
        return None

    return {
        "device_id": raw[16:20].hex().upper(),
        "device_type": device_type,
        "button": button,
        "action": _ACTIONS[action_index],
        "counter": decrypted[8],
    }


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration domain before a config entry is loaded."""
    runtime = hass.data.setdefault(DOMAIN, {})
    runtime.setdefault(DATA_CONFIGURED_DEVICES, {})
    runtime.setdefault(DATA_CONFIRMATION_WAITERS, {})
    runtime.setdefault(DATA_DISCOVERY_TIMESTAMPS, {})
    runtime.setdefault(DATA_ENTRIES, {})
    return True


async def _async_start_discovery(
    hass: HomeAssistant, remote_id: str, device_type: str
) -> None:
    """Start a user-confirmed flow for a newly heard remote."""
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={CONF_REMOTE_ID: remote_id, CONF_DEVICE_TYPE: device_type},
    )


@callback
def _async_register_scanner(hass: HomeAssistant) -> Callable[[], None]:
    """Register the shared passive BLE listener."""
    recent: dict[tuple[str, int, int, str], float] = {}
    active_holds: dict[tuple[str, int], tuple[float, Callable[[], None]]] = {}
    device_registry = dr.async_get(hass)
    runtime = hass.data[DOMAIN]

    @callback
    def handle_ble_event(
        service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        if change != BluetoothChange.ADVERTISEMENT:
            return

        raw = getattr(service_info, "raw", None)
        if not raw or (decoded := _decode(raw)) is None:
            return

        now = time.monotonic()
        key = (
            decoded["device_id"],
            decoded["counter"],
            decoded["button"],
            decoded["action"],
        )
        if now - recent.get(key, 0.0) < 2.0:
            return
        recent[key] = now
        if len(recent) > 128:
            cutoff = now - 60.0
            for old_key, seen in list(recent.items()):
                if seen < cutoff:
                    recent.pop(old_key, None)

        remote_id = decoded["device_id"]
        configured = runtime[DATA_CONFIGURED_DEVICES].get(remote_id)
        if configured is None:
            if decoded["device_type"] != "R5":
                return

            waiter: asyncio.Future[dict[str, Any]] | None = runtime[
                DATA_CONFIRMATION_WAITERS
            ].get(remote_id)
            if waiter is not None and not waiter.done():
                waiter.set_result(decoded)
                return

            last_discovery = runtime[DATA_DISCOVERY_TIMESTAMPS].get(remote_id, 0.0)
            if now - last_discovery >= _DISCOVERY_THROTTLE:
                runtime[DATA_DISCOVERY_TIMESTAMPS][remote_id] = now
                hass.async_create_task(
                    _async_start_discovery(hass, remote_id, decoded["device_type"]),
                    f"Discover eWeLink Remote BLE {remote_id}",
                )
            return

        device_type, owner_entry_id = configured
        device = device_registry.async_get_device_by_identifier(
            (DOMAIN, remote_id), owner_entry_id
        )
        if device is None:
            device = device_registry.async_get_or_create(
                config_entry_id=owner_entry_id,
                identifiers={(DOMAIN, remote_id)},
                manufacturer="SONOFF",
                model=device_type,
                name=f"SONOFF SwitchMan {device_type} {remote_id[-4:]}",
            )

        event_data = {
            **decoded,
            "ha_device_id": device.id,
            "address": service_info.address,
            "rssi": service_info.rssi,
            "source": service_info.source,
        }
        if decoded["action"] == "hold":
            hold_key = (decoded["device_id"], decoded["button"])
            previous = active_holds.get(hold_key)
            event_data["phase"] = "start" if previous is None else "repeat"
            if previous is not None:
                previous[1]()

            last_seen = now
            release_data = {**event_data, "phase": "release", "synthetic": True}

            @callback
            def fire_release(_now) -> None:
                current = active_holds.get(hold_key)
                if current is None or current[0] != last_seen:
                    return
                active_holds.pop(hold_key, None)
                hass.bus.async_fire(EVENT_BUTTON, release_data)

            cancel_release = async_call_later(hass, _HOLD_RELEASE_DELAY, fire_release)
            active_holds[hold_key] = (last_seen, cancel_release)

        hass.bus.async_fire(EVENT_BUTTON, event_data)
        _LOGGER.debug(
            "eWeLink Remote %s: button %s %s via %s",
            decoded["device_id"],
            decoded["button"],
            decoded["action"],
            service_info.source,
        )

    cancel_listener = async_register_callback(
        hass,
        handle_ble_event,
        BluetoothCallbackMatcher(connectable=False),
        BluetoothScanningMode.PASSIVE,
    )

    @callback
    def cancel_all() -> None:
        cancel_listener()
        for _, cancel_release in active_holds.values():
            cancel_release()
        active_holds.clear()

    return cancel_all


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the receiver service or one confirmed remote."""
    runtime = hass.data[DOMAIN]
    device_registry = dr.async_get(hass)
    known_devices: dict[str, str] = {}

    if remote_id := entry.data.get(CONF_REMOTE_ID):
        device_type = entry.data.get(CONF_DEVICE_TYPE, "R5")
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, remote_id)},
            manufacturer="SONOFF",
            model=device_type,
            name=f"SONOFF SwitchMan {device_type} {remote_id[-4:]}",
        )
        known_devices[remote_id] = device_type
    else:
        # Preserve devices created by versions before the confirmation flow.
        for device in dr.async_entries_for_config_entry(
            device_registry, entry.entry_id
        ):
            legacy_remote_id = next(
                (
                    identifier
                    for domain, identifier in device.identifiers
                    if domain == DOMAIN
                ),
                None,
            )
            if legacy_remote_id is not None and device.model is not None:
                known_devices[legacy_remote_id] = device.model

    runtime[DATA_ENTRIES][entry.entry_id] = {
        "known_devices": known_devices,
    }
    for known_remote_id, device_type in known_devices.items():
        runtime[DATA_CONFIGURED_DEVICES][known_remote_id] = (
            device_type,
            entry.entry_id,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if DATA_SCANNER_CANCEL not in runtime:
        runtime[DATA_SCANNER_CANCEL] = _async_register_scanner(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    runtime = hass.data.get(DOMAIN, {})
    entry_data = runtime.get(DATA_ENTRIES, {}).pop(entry.entry_id, {})
    for remote_id in entry_data.get("known_devices", {}):
        configured = runtime.get(DATA_CONFIGURED_DEVICES, {}).get(remote_id)
        if configured is not None and configured[1] == entry.entry_id:
            runtime[DATA_CONFIGURED_DEVICES].pop(remote_id, None)

    if not runtime.get(DATA_ENTRIES) and (
        cancel_scanner := runtime.pop(DATA_SCANNER_CANCEL, None)
    ):
        cancel_scanner()
    return True
