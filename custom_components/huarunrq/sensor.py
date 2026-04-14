# sensor.py
"""华润燃气传感器"""
import logging
from datetime import timedelta
from typing import Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed
)
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN, DEVICE_MANUFACTURER, DEVICE_MODEL, DEVICE_NAME,
    DEFAULT_UPDATE_INTERVAL_HOURS, SENSOR_BALANCE, CONF_UPDATE_INTERVAL
)
from .api_client import HuaRunApiClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """设置传感器"""
    cons_no = entry.data.get("cno")
    name = entry.title
    
    # 创建API客户端和数据协调器
    api_client = HuaRunApiClient(hass, cons_no)
    coordinator = GasDataCoordinator(hass, api_client, cons_no, entry.entry_id, entry)
    
    # 首次刷新
    await coordinator.async_config_entry_first_refresh()
    
    # 创建传感器
    entities = [
        GasBalanceSensor(coordinator, name, cons_no),
    ]
    
    async_add_entities(entities, True)


class GasDataCoordinator(DataUpdateCoordinator):
    """数据协调器"""
    
    def __init__(self, hass: HomeAssistant, api_client: HuaRunApiClient, cons_no: str, entry_id: str, entry: ConfigEntry):
        # 从 data 中读取更新间隔
        update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_HOURS)
        super().__init__(
            hass,
            _LOGGER,
            name=f"华润燃气 {cons_no}",
            update_interval=timedelta(hours=update_interval),
        )
        self.api_client = api_client
        self.cons_no = cons_no
        self.entry_id = entry_id
        self.entry = entry
        
        # 缓存数据
        self.balance = None
        
        # 监听配置变更
        self._remove_listener = entry.add_update_listener(self._async_entry_updated)
    
    async def _async_entry_updated(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """当配置更新时，调整更新间隔"""
        new_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_HOURS)
        self.update_interval = timedelta(hours=new_interval)
        _LOGGER.debug(f"更新间隔已调整为 {new_interval} 小时")
        await self.async_request_refresh()
    
    async def _async_update_data(self):
        """更新数据"""
        try:
            # 获取余额
            balance = await self.api_client.get_balance()
            
            # 处理余额
            self.balance = balance
            
            return {
                "balance": self.balance,
            }
            
        except Exception as err:
            raise UpdateFailed(f"更新失败: {err}")
    
    async def async_shutdown(self) -> None:
        """关闭时移除监听器"""
        self._remove_listener()
        await super().async_shutdown()


class GasBalanceSensor(CoordinatorEntity, SensorEntity):
    """余额传感器"""
    
    def __init__(self, coordinator: GasDataCoordinator, name: str, cons_no: str):
        super().__init__(coordinator)
        self._attr_name = f"{name} 余额"
        self._attr_unique_id = f"{coordinator.entry_id}_{SENSOR_BALANCE}"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "CNY"
        self._cons_no = cons_no
    
    @property
    def native_value(self):
        return self.coordinator.balance
    
    @property
    def extra_state_attributes(self):
        return {
            "燃气编号": self._cons_no,
            "更新成功": self.coordinator.last_update_success,
            "更新间隔": f"{self.coordinator.update_interval.total_seconds() / 3600}小时"
        }
    
    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._cons_no)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            entry_type=DeviceEntryType.SERVICE,
        )