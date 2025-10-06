"""HuaRunRQ integration."""
import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_CNS
from .coordinator import HuaRunRQDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up HuaRunRQ from a config entry."""
    cns = config_entry.data[CONF_CNS]
    _LOGGER.info(f"Setting up HuaRunRQ with cns: {cns}")
    
    # 为每个户号创建协调器
    coordinators = {}
    for cno in cns:
        coordinator = HuaRunRQDataUpdateCoordinator(hass, cno, config_entry)
        await coordinator.async_config_entry_first_refresh()
        coordinators[cno] = coordinator

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = coordinators

    # 设置传感器平台
    await hass.config_entries.async_forward_entry_setups(config_entry, ["sensor"])
    _LOGGER.info("HuaRunRQ setup completed successfully")
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok