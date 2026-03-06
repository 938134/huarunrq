"""HuaRun Gas integration core logic."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HuaRun Gas from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # 使用新版API
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # 添加更新监听器
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    _LOGGER.info("Successfully set up entry: %s", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info("Successfully unloaded entry: %s", entry.title)
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
    _LOGGER.debug("Options updated for entry: %s", entry.title)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)
    
    if entry.version == 1:
        # 迁移逻辑
        entry.version = 2
    
    _LOGGER.info("Migration to version %s successful", entry.version)
    return True