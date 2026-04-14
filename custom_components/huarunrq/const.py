# const.py
"""常量定义"""
from homeassistant.const import Platform

DOMAIN = "huarun_gas"
PLATFORMS = [Platform.SENSOR]

# API相关常量
API_BASE_URL = "https://mbhapp.crcgas.com/bizonline"
API_PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAIi4Gb8iOGcc05iqNilFb1gM6/iG4fSiECeEaEYN2cxaBVT+6zgp+Tp0TbGVqGMIB034BLaVdNZZPnqKFH4As8UCAwEAAQ==
-----END PUBLIC KEY-----'''
API_USER = "bizH5"
API_SECRET = "e5b871c278a84defa8817d22afc34338"

# API端点
ENDPOINT_QUERY_ARREARS = "/api/h5/pay/queryArrears"
# 以下端点认证方式有问题，暂时禁用
# ENDPOINT_GET_BILL_LIST = "/gasbill/getGasBillList"
# ENDPOINT_GET_BILL_DETAIL = "/gasbill/getBillDetail"
# ENDPOINT_GET_YEARLY_CHART = "/gasbill/getGasBillList4Chart"

# 默认配置
DEFAULT_UPDATE_INTERVAL_HOURS = 6
DEFAULT_REQUEST_TIMEOUT = 15

# 范围限制
MIN_UPDATE_INTERVAL = 1
MAX_UPDATE_INTERVAL = 72

# 传感器命名
SENSOR_BALANCE = "balance"

# 设备信息
DEVICE_MANUFACTURER = "华润燃气"
DEVICE_MODEL = "智能燃气表"
DEVICE_NAME = "华润燃气表"

# 配置项键名
CONF_CONS_NO = "cno"
CONF_UPDATE_INTERVAL = "update_interval_hours"

# API响应消息
API_MSG_SUCCESS = "操作成功"