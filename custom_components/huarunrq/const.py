"""Constants for HuaRunRQ integration."""
DOMAIN = "huarunrq"
MANUFACTURER = "华润燃气"

CONF_CNS = "cns"
CONF_SCAN_INTERVAL = "scan_interval"

API_BASE_URL = "https://mbhapp.crcgas.com/bizonline"
API_QUERY_ARREARS = f"{API_BASE_URL}/api/h5/pay/queryArrears?authVersion=v2&consNo={{cno}}"
API_GAS_BILL_LIST = f"{API_BASE_URL}/gasbill/getGasBillList4Chart?consNo={{cno}}&page=1&pageNum=6"

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAIi4Gb8iOGcc05iqNilFb1gM6/iG4fSi
ECeEaEYN2cxaBVT+6zgp+Tp0TbGVqGMIB034BLaVdNZZPnqKFH4As8UCAwEAAQ==
-----END PUBLIC KEY-----"""

SENSOR_TYPES = {
    "balance": ["燃气余额", "CNY", "mdi:cash"],
    "gas_usage": ["本月用气量", "m³", "mdi:fire"],
}