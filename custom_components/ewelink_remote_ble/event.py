"""Event entities for SONOFF eWeLink-Remote BLE devices."""

from __future__ import annotations

from typing import Any, override

from homeassistant.components.event import (
    EventDeviceClass,
    EventEntity,
    EventEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    DATA_ENTRIES,
    DOMAIN,
    EVENT_BUTTON,
    TRIGGER_SUBTYPES,
)


class EwelinkRemoteButtonEvent(EventEntity):
    """Represent one physical button on an R5 remote."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:gesture-tap-button"
    _attr_should_poll = False

    def __init__(self, remote_id: str, button: int) -> None:
        """Initialize an R5 button event entity."""
        self._remote_id = remote_id
        self._button = button
        self._attr_unique_id = f"{remote_id}_button_{button}"
        self._attr_device_info = dr.DeviceInfo(identifiers={(DOMAIN, remote_id)})
        self.entity_description = EventEntityDescription(
            key=f"button_{button}",
            translation_key=f"button_{button}",
            event_types=list(TRIGGER_SUBTYPES),
            device_class=EventDeviceClass.BUTTON,
        )

    @override
    async def async_added_to_hass(self) -> None:
        """Start listening for decoded remote events."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_BUTTON, self._async_handle_event)
        )

    @callback
    def _async_handle_event(self, event: Event) -> None:
        """Update this entity when its physical button was used."""
        data = event.data
        if data.get("device_id") != self._remote_id:
            return
        if data.get("button") != self._button:
            return

        action = data.get("action")
        if action in ("single", "double"):
            event_type = action
        elif action == "hold" and (phase := data.get("phase")):
            event_type = f"hold_{phase}"
        else:
            return

        attributes: dict[str, Any] = {
            key: data[key]
            for key in ("counter", "rssi", "source", "synthetic")
            if key in data
        }
        self._trigger_event(event_type, attributes)
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up event entities for known and newly discovered R5 remotes."""
    seen: set[str] = set()

    @callback
    def add_remote(remote_id: str, device_type: str) -> None:
        if device_type != "R5" or remote_id in seen:
            return
        seen.add(remote_id)
        async_add_entities(
            EwelinkRemoteButtonEvent(remote_id, button) for button in range(1, 7)
        )

    known_devices = hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id]["known_devices"]
    for remote_id, device_type in known_devices.items():
        add_remote(remote_id, device_type)
