"""Platform for sensor integration."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, SENSOR_TYPES

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up HuaRunRQ sensors based on a config entry."""
    coordinators = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    
    for cno, coordinator in coordinators.items():
        # 为每个户号创建所有传感器类型
        for sensor_type in SENSOR_TYPES:
            entities.append(
                HuaRunRQSensor(coordinator, cno, sensor_type)
            )
    
    async_add_entities(entities, True)

class HuaRunRQSensor(CoordinatorEntity, SensorEntity):
    """Representation of a HuaRunRQ Sensor."""

    def __init__(self, coordinator, cno, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._cno = cno
        self._sensor_type = sensor_type
        self._attr_name = f"华润燃气 {cno} {SENSOR_TYPES[sensor_type][0]}"
        self._attr_unique_id = f"{DOMAIN}_{cno}_{sensor_type}"
        self._attr_icon = SENSOR_TYPES[sensor_type][2]
        self._attr_unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cno)},
            name=f"华润燃气 {cno}",
            manufacturer=MANUFACTURER,
            model="燃气用户",
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        data = self.coordinator.data
        
        if self._sensor_type == "balance":
            return data.get("totalGasBalance")
        elif self._sensor_type == "gas_usage":
            # 返回最新月份的用气量
            return data.get("current_gas_usage")
        
        return None

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}
            
        attrs = {"户号": self._cno}
        data = self.coordinator.data
        
        if self._sensor_type == "gas_usage":
            attrs.update({
                "账单月份": data.get("current_bill_month"),
                "账单金额": data.get("current_bill_amount"),
                "账单状态": data.get("current_bill_status")
            })
            
        return attrs