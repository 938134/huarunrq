# config_flow.py
"""配置流程"""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_CONS_NO, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_HOURS, MIN_UPDATE_INTERVAL, MAX_UPDATE_INTERVAL


class HuaRunRQConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """配置流程"""
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """用户添加集成"""
        errors = {}
        
        if user_input is not None:
            cons_no = user_input.get(CONF_CONS_NO)
            update_interval = user_input.get(CONF_UPDATE_INTERVAL)
            
            # 验证户号格式
            if not cons_no or not cons_no.isdigit():
                errors[CONF_CONS_NO] = "invalid_number"
            elif update_interval < MIN_UPDATE_INTERVAL or update_interval > MAX_UPDATE_INTERVAL:
                errors[CONF_UPDATE_INTERVAL] = "invalid_interval"
            else:
                # 检查是否已配置
                await self.async_set_unique_id(cons_no)
                self._abort_if_unique_id_configured()
                
                # 测试API连接
                from .api_client import HuaRunApiClient
                client = HuaRunApiClient(self.hass, cons_no)
                balance = await client.get_balance()
                
                if balance is not None:
                    return self.async_create_entry(
                        title=f"华润燃气 {cons_no}",
                        data={
                            CONF_CONS_NO: cons_no,
                            CONF_UPDATE_INTERVAL: update_interval
                        }
                    )
                else:
                    errors["base"] = "cannot_connect"
        
        # 定义数据 schema
        data_schema = vol.Schema({
            vol.Required(CONF_CONS_NO): str,
            vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL_HOURS): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                # 添加描述信息，让前端知道这是数字输入框
                vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)
            )
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "min_interval": MIN_UPDATE_INTERVAL,
                "max_interval": MAX_UPDATE_INTERVAL
            }
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """获取选项流程"""
        return HuaRunRQOptionsFlow(config_entry)


class HuaRunRQOptionsFlow(config_entries.OptionsFlow):
    """选项流程"""
    
    def __init__(self, config_entry):
        """初始化选项流程"""
        self._config_entry = config_entry
    
    async def async_step_init(self, user_input=None):
        """选项设置"""
        errors = {}
        
        if user_input is not None:
            cons_no = user_input.get(CONF_CONS_NO)
            update_interval = user_input.get(CONF_UPDATE_INTERVAL)
            
            # 验证户号格式
            if not cons_no or not cons_no.isdigit():
                errors[CONF_CONS_NO] = "invalid_number"
            elif update_interval < MIN_UPDATE_INTERVAL or update_interval > MAX_UPDATE_INTERVAL:
                errors[CONF_UPDATE_INTERVAL] = "invalid_interval"
            else:
                # 如果户号变更，测试新户号是否有效
                if cons_no != self._config_entry.data.get(CONF_CONS_NO):
                    from .api_client import HuaRunApiClient
                    client = HuaRunApiClient(self.hass, cons_no)
                    balance = await client.get_balance()
                    
                    if balance is None:
                        errors["base"] = "cannot_connect"
                
                if not errors:
                    # 更新配置
                    new_data = {
                        **self._config_entry.data, 
                        CONF_CONS_NO: cons_no,
                        CONF_UPDATE_INTERVAL: update_interval
                    }
                    new_options = {CONF_UPDATE_INTERVAL: update_interval}
                    
                    # 如果户号变更，需要更新唯一ID
                    if cons_no != self._config_entry.data.get(CONF_CONS_NO):
                        self.hass.config_entries.async_update_entry(
                            self._config_entry,
                            data=new_data,
                            unique_id=cons_no,
                            title=f"华润燃气 {cons_no}"
                        )
                    else:
                        self.hass.config_entries.async_update_entry(
                            self._config_entry,
                            data=new_data
                        )
                    
                    return self.async_create_entry(title="", data=new_options)
        
        # 获取当前值
        current_cons_no = self._config_entry.data.get(CONF_CONS_NO, "")
        current_interval = self._config_entry.data.get(
            CONF_UPDATE_INTERVAL, 
            DEFAULT_UPDATE_INTERVAL_HOURS
        )
        
        # 定义数据 schema
        data_schema = vol.Schema({
            vol.Required(CONF_CONS_NO, default=current_cons_no): str,
            vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)
            )
        })
        
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "min_interval": MIN_UPDATE_INTERVAL,
                "max_interval": MAX_UPDATE_INTERVAL
            }
        )