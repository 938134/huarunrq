"""Constants for HuaRunRQ integration."""
DOMAIN = "huarunrq"
MANUFACTURER = "华润燃气"

CONF_CNS = "cns"
CONF_SCAN_INTERVAL = "scan_interval"

# 使用抓包数据中的准确API URL
API_BASE_URL = "https://mbhapp.crcgas.com/bizonline"
API_QUERY_ARREARS = f"{API_BASE_URL}/pay/queryArrears?consNo={{cno}}"
API_GAS_BILL_LIST = f"{API_BASE_URL}/gasbill/getGasBillList4Chart?consNo={{cno}}&page=1&pageNum=6"

SENSOR_TYPES = {
    "balance": ["燃气余额", "CNY", "mdi:cash"],
    "gas_usage": ["本月用气量", "m³", "mdi:fire"],
}