# custom_components/huarunrq/const.py
import logging
from datetime import timedelta

DOMAIN = "huarunrq"
CONF_CNO_LIST = "cno_list"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 3600

BASE_URL = "https://mbhapp.crcgas.com/bizonline"
API_ARREARS = BASE_URL + "/pay/queryArrears?authVersion=v2&consNo={cno}"
API_BILL_LIST = BASE_URL + "/gasbill/getGasBillList?page={page}&pageNum={pageNum}&consNo={cno}"

BIZ_H5_PUBLIC_KEY_PEM = """\
-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAIi4Gb8iOGcc05iqNilFb1gM6/iG4fSi
ECeEaEYN2cxaBVT+6zgp+Tp0TbGVqGMIB034BLaVdNZZPnqKFH4As8UCAwEAAQ==
-----END PUBLIC KEY-----"""

_LOGGER = logging.getLogger(__name__)