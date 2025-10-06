"""Binary sensor platform for HuaRunRQ."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import *

async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for cno in coord.cnos:
        device = DeviceInfo(identifiers={(DOMAIN, cno)}, name=f"华润燃气 {cno}", manufacturer="华润燃气")
        entities.append(ArrearsSensor(coord, cno, device))
    async_add_entities(entities)


class ArrearsSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_arrears"
        self._attr_name = f"{cno} 欠费状态"
        self._attr_icon = "mdi:alert-circle"

    @property
    def is_on(self):
        data = self.coordinator.data.get(self.cno)
        return data.get("arrearsStatus", 0) > 0 if data else False