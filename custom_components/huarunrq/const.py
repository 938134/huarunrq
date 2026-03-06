"""Constants for HuaRun Gas integration."""
from homeassistant.const import Platform

DOMAIN = "huarunrq"
PLATFORMS = [Platform.SENSOR]

# 配置相关常量
CONF_CNO = "cno"
CONF_UPDATE_INTERVAL = "update_interval_hours"
DEFAULT_UPDATE_INTERVAL = 24
MIN_UPDATE_INTERVAL = 1
MAX_UPDATE_INTERVAL = 72

# API相关常量
API_BASE_URL = "https://mbhapp.crcgas.com/bizonline/api"
API_QUERY_ARREARS = "/h5/pay/queryArrears"
PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAIi4Gb8iOGcc05iqNilFb1gM6/iG4fSiECeEaEYN2cxaBVT+6zgp+Tp0TbGVqGMIB034BLaVdNZZPnqKFH4As8UCAwEAAQ==
-----END PUBLIC KEY-----'''

# 属性名称
ATTR_GAS_NUMBER = "燃气编号"
ATTR_UPDATE_INTERVAL = "更新间隔（小时）"
ATTR_LAST_UPDATE = "最后更新时间"