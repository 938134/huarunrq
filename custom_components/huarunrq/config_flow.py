"""Config flow for HuaRunRQ integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from .const import *

def validate_cnolist(value: str) -> list[str]:
    cnos = [c.strip() for c in value.split(",") if c.strip().isdigit() and 10 <= len(c.strip()) <= 12]
    if not cnos:
        raise vol.Invalid("至少输入一个 10-12 位数字户号，多个用英文逗号分隔")
    return list(set(cnos))


class HuaRunRQConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HuaRunRQOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                cnos = validate_cnolist(user_input[CONF_CNO_LIST])
                await self.async_set_unique_id(",".join(sorted(cnos)))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"华润燃气 {len(cnos)} 户",
                    data={CONF_CNO_LIST: cnos},
                    options={CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)},
                )
            except vol.Invalid as e:
                errors["base"] = str(e)

        schema = vol.Schema({
            vol.Required(CONF_CNO_LIST): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class HuaRunRQOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            cnos = validate_cnolist(user_input[CONF_CNO_LIST])
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={CONF_CNO_LIST: cnos},
                options={CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)},
            )
            return self.async_create_entry(title="", data={})

        current_cnolist = ",".join(self.config_entry.data[CONF_CNO_LIST])
        schema = vol.Schema({
            vol.Required(CONF_CNO_LIST, default=current_cnolist): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int,
        })
        return self.async_show_form(step_id="init", data_schema=schema)