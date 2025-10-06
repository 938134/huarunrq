"""Config flow for HuaRunRQ integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_CNO_LIST, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL


def validate_cnolist(value: str) -> list[str]:
    """返回去重后户号列表，异常抛出 voluptuous.Invalid"""
    cnos = [c.strip() for c in value.split(",") if c.strip().isdigit() and 10 <= len(c.strip()) <= 12]
    if not cnos:
        raise vol.Invalid("至少输入一个 10-12 位数字户号，多个用英文逗号分隔")
    return list(set(cnos))   # 去重


class HuaRunRQConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HuaRunRQ."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "HuaRunRQOptionsFlowHandler":
        """Create options flow handler."""
        return HuaRunRQOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
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

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CNO_LIST): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)


class HuaRunRQOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for HuaRunRQ integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                cnos = validate_cnolist(user_input[CONF_CNO_LIST])
                # 更新选项 & 重新加载以增删设备
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    options={CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)}
                )
                # 数据字段也更新（会触发 async_setup_entry 重新执行）
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={CONF_CNO_LIST: cnos}
                )
                return self.async_create_entry(title="", data={})
            except vol.Invalid as e:
                errors["base"] = str(e)

        current_cnolist = ",".join(self.config_entry.data[CONF_CNO_LIST])
        schema = vol.Schema(
            {
                vol.Required(CONF_CNO_LIST, default=current_cnolist): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)