"""Config flow for eWeLink Remote BLE."""

from __future__ import annotations

from typing import Any, override

import probatio

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


class EwelinkRemoteBleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create the single passive R5 receiver entry."""

    VERSION = 1

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
