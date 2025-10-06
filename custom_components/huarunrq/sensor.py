from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import *

async def async_setup_entry(hass, entry, async_add_entities):
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
        return data.get("totalGasNum") if data else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.cno)
        return {"records": data.get("bills", [])} if data else {}