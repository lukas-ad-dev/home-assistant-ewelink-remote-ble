"""Device triggers for SONOFF eWeLink-Remote BLE devices."""

from __future__ import annotations

from typing import Any

import probatio
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.components.homeassistant.triggers.event import EventTriggerArgument
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_EVENT,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import (
    BUTTON_TYPES,
    CONF_SUBTYPE,
    DOMAIN,
    EVENT_BUTTON,
    TRIGGER_SUBTYPES,
)


def _remote_id(hass: HomeAssistant, device_id: str) -> str | None:
    """Return the eWeLink device identifier for a HA device registry ID."""
    device = dr.async_get(hass).async_get(device_id, include_child_devices=False)
    if device is None or device.model != "R5":
        return None
    return next(
        (identifier for domain, identifier in device.identifiers if domain == DOMAIN),
        None,
    )


async def async_validate_trigger_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate a device trigger."""
    schema = DEVICE_TRIGGER_BASE_SCHEMA.extend(
        {
            probatio.Required(CONF_TYPE): probatio.In(BUTTON_TYPES),
            probatio.Required(CONF_SUBTYPE): probatio.In(TRIGGER_SUBTYPES),
        }
    )
    return schema(config)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Return all R5 button triggers for a device."""
    if _remote_id(hass, device_id) is None:
        return []

    return [
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: button_type,
            CONF_SUBTYPE: subtype,
        }
        for button_type in BUTTON_TYPES
        for subtype in TRIGGER_SUBTYPES
    ]


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach an R5 device trigger to the decoded event bus."""
    remote_id = _remote_id(hass, config[CONF_DEVICE_ID])
    if remote_id is None:
        raise ValueError(f"Unknown eWeLink Remote BLE device {config[CONF_DEVICE_ID]}")

    button = int(config[CONF_TYPE].split("_", 1)[1])
    subtype = config[CONF_SUBTYPE]
    event_data: dict[str, Any] = {
        "device_id": remote_id,
        "button": button,
    }
    if subtype == "single":
        event_data["action"] = "single"
    elif subtype == "double":
        event_data["action"] = "double"
    else:
        event_data["action"] = "hold"
        event_data["phase"] = subtype.removeprefix("hold_")

    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            EventTriggerArgument.PLATFORM: CONF_EVENT,
            EventTriggerArgument.EVENT_TYPE: EVENT_BUTTON,
            EventTriggerArgument.EVENT_DATA: event_data,
        }
    )
    return await event_trigger.async_attach_trigger(
        hass,
        event_config,
        action,
        trigger_info,
        platform_type="device",
    )
