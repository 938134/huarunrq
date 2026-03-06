"""Config flow for HuaRun Gas integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import re

from .const import (
    DOMAIN,
    CONF_CNO,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class HuaRunGasFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HuaRun Gas."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HuaRunGasOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            cno = user_input.get(CONF_CNO, "").strip()
            
            # 验证户号
            if not cno:
                errors[CONF_CNO] = "missing_cno"
            elif not re.match(r"^\d{10,12}$", cno):
                errors[CONF_CNO] = "invalid_number"
            
            if not errors:
                await self.async_set_unique_id(cno)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f"华润燃气 ({cno})",
                    data={CONF_CNO: cno},
                    options={CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CNO): str,
            }),
            errors=errors,
            description_placeholders={
                "example": "1032246196"
            }
        )


class HuaRunGasOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for HuaRun Gas."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        
        if user_input is not None:
            cno = user_input.get(CONF_CNO, "").strip()
            interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            
            # 验证户号
            if not cno:
                errors[CONF_CNO] = "missing_cno"
            elif not re.match(r"^\d{10,12}$", cno):
                errors[CONF_CNO] = "invalid_number"
            
            # 验证间隔
            try:
                interval = int(interval)
                if not MIN_UPDATE_INTERVAL <= interval <= MAX_UPDATE_INTERVAL:
                    errors[CONF_UPDATE_INTERVAL] = "invalid_interval"
            except ValueError:
                errors[CONF_UPDATE_INTERVAL] = "invalid_number"
            
            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_CNO: cno,
                        CONF_UPDATE_INTERVAL: interval
                    }
                )

        current_cno = self.config_entry.options.get(
            CONF_CNO, 
            self.config_entry.data.get(CONF_CNO, "")
        )
        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, 
            DEFAULT_UPDATE_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_CNO, default=current_cno): str,
                vol.Required(
                    CONF_UPDATE_INTERVAL, 
                    default=current_interval
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=72)),
            }),
            errors=errors
        )