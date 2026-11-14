"""Config flow for eWeLink Remote BLE."""

from __future__ import annotations

import asyncio
from typing import Any, override

import probatio
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_DEVICE_TYPE,
    CONF_REMOTE_ID,
    DATA_CONFIRMATION_WAITERS,
    DOMAIN,
)

_CONFIRM_TIMEOUT = 60.0
_INTERACTION_POLL_INTERVAL = 0.25


class EwelinkRemoteBleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up the receiver service and user-confirmed remotes."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._remote_id: str | None = None
        self._device_type: str | None = None
        self._confirmation_task: asyncio.Task[bool] | None = None

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle setup from the integrations page."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="eWeLink Remote BLE", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema({}),
        )

    @override
    async def async_step_integration_discovery(
        self, discovery_info: dict[str, str]
    ) -> ConfigFlowResult:
        """Offer an unknown remote as a discovered device."""
        self._remote_id = discovery_info[CONF_REMOTE_ID]
        self._device_type = discovery_info[CONF_DEVICE_TYPE]
        name = self._device_name
        self.context["title_placeholders"] = {"name": name}

        await self.async_set_unique_id(self._remote_id)
        self._abort_if_unique_id_configured()
        self._confirmation_task = self.hass.async_create_task(
            self._async_wait_for_button_after_user_interaction(),
            f"Confirm eWeLink Remote BLE {self._remote_id}",
        )
        return await self.async_step_wait_for_button()

    async def async_step_wait_for_button(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Wait for a new advertisement from the selected remote."""
        if self._confirmation_task is None:
            return self.async_abort(reason="confirmation_failed")

        if not self._confirmation_task.done():
            return self.async_show_progress(
                step_id="wait_for_button",
                progress_action="wait_for_button",
                description_placeholders={"name": self._device_name},
                progress_task=self._confirmation_task,
            )

        return self.async_show_progress_done(
            next_step_id=("finish" if self._confirmation_task.result() else "timeout")
        )

    async def async_step_timeout(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Abort after a timed-out confirmation."""
        return self.async_abort(reason="confirmation_timeout")

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the config entry after physical confirmation."""
        if self._remote_id is None or self._device_type is None:
            return self.async_abort(reason="confirmation_failed")

        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=self._device_name,
            data={
                CONF_REMOTE_ID: self._remote_id,
                CONF_DEVICE_TYPE: self._device_type,
            },
        )

    @property
    def _device_name(self) -> str:
        """Return a human-readable discovered device name."""
        remote_id = self._remote_id or "unknown"
        device_type = self._device_type or "Remote"
        return f"SONOFF SwitchMan {device_type} {remote_id[-4:]}"

    async def _async_wait_for_button_after_user_interaction(self) -> bool:
        """Wait for interaction, then for another packet from the same remote."""
        if self._remote_id is None:
            return False

        # Home Assistant marks a discovery flow as protected once the user opens
        # it from the discovered-devices card. Do not accept a second packet
        # before that point, or an unattended remote could confirm itself.
        while not self.context.get("dismiss_protected"):
            await asyncio.sleep(_INTERACTION_POLL_INTERVAL)

        runtime = self.hass.data.setdefault(DOMAIN, {})
        waiters = runtime.setdefault(DATA_CONFIRMATION_WAITERS, {})
        waiter: asyncio.Future[dict[str, Any]] = (
            asyncio.get_running_loop().create_future()
        )
        waiters[self._remote_id] = waiter
        try:
            decoded = await asyncio.wait_for(waiter, _CONFIRM_TIMEOUT)
            return decoded.get(CONF_DEVICE_TYPE) == self._device_type
        except TimeoutError:
            return False
        finally:
            if waiters.get(self._remote_id) is waiter:
                waiters.pop(self._remote_id, None)
