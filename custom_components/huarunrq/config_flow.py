"""Config flow for HuaRunRQ integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_CNS, CONF_SCAN_INTERVAL

class HuaRunRQFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HuaRunRQ."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HuaRunRQOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # 验证户号格式（支持逗号分隔的多个户号）
            cns = [cno.strip() for cno in user_input[CONF_CNS].split(",") if cno.strip()]
            if not cns:
                errors[CONF_CNS] = "至少需要一个有效的户号"
            else:
                # 创建配置条目
                return self.async_create_entry(
                    title=f"华润燃气({len(cns)}个户号)",
                    data={CONF_CNS: cns},
                    options={CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, 3600)}
                )

        # 显示表单
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CNS, description="多个户号用逗号分隔"): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=3600): int
            }),
            errors=errors
        )

class HuaRunRQOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for HuaRunRQ integration."""

    def __init__(self, config_entry):
        """Initialize HuaRunRQ options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan_interval = self.config_entry.options.get(CONF_SCAN_INTERVAL, 3600)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_SCAN_INTERVAL, default=current_scan_interval): int
            })
        )