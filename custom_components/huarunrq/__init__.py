"""HuaRunRQ integration."""
import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the HuaRunRQ component."""
    # 在这里，我们不需要做任何特别的设置
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up HuaRunRQ from a config entry."""
    # 在这里，我们将传感器平台与配置条目关联起来
    # 注意：使用 async_forward_entry_setups 替代 async_forward_entry_setup
    await hass.config_entries.async_forward_entry_setups(config_entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    # 在这里，我们将传感器平台与配置条目解绑
    await hass.config_entries.async_unload_platforms(config_entry, ["sensor"])
    return True