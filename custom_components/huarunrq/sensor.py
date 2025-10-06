"""Sensor platform for HuaRunRQ."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """动态设备工厂：每户号 1 设备 + 传感器"""
    coord = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for cno in coord.cnos:
        device = DeviceInfo(identifiers={(DOMAIN, cno)}, name=f"华润燃气 {cno}", manufacturer="华润燃气")
        entities.extend([
            BalanceSensor(coord, cno, device),
            LatestGasSensor(coord, cno, device),
            YearTotalSensor(coord, cno, device),
        ])
    async_add_entities(entities)


class BalanceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_balance"
        self._attr_name = f"{cno} 账户余额"
        self._attr_unit_of_measurement = "元"
        self._attr_icon = "mdi:currency-cny"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        return -data.get("arrearsMoney", 0) if data else None


class LatestGasSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_latest_gas"
        self._attr_name = f"{cno} 最新用气量"
        self._attr_unit_of_measurement = "m³"
        self._attr_icon = "mdi:fire"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        return data.get("totalGasNum") or data.get("gasNum") or None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.cno)
        return {"records": data.get("bills", [])} if data else {}


class YearTotalSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_year_total"
        self._attr_name = f"{cno} 年度累计用气"
        self._attr_unit_of_measurement = "m³"
        self._attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        if not data or not data.get("bills"):
            return None
        return round(sum(b["gasNum"] for b in data["bills"]), 2)