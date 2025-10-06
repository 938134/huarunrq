"""Constants for HuaRunRQ integration."""
DOMAIN = "huarunrq"
MANUFACTURER = "华润燃气"

CONF_CNS = "cns"
CONF_SCAN_INTERVAL = "scan_interval"

SENSOR_TYPES = {
    "balance": ["燃气余额", "CNY", "mdi:cash"],
    "gas_usage": ["本月用气量", "m³", "mdi:fire"],
}