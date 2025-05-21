# custom_components/huarunrq/const.py
import voluptuous as vol

DOMAIN = "huarunrq"
DATA_SCHEMA = vol.Schema({
    vol.Required("cno"): str,
    vol.Optional("scan_interval", default=3600): int
})

API_URL = "https://mbhapp.crcgas.com/bizonline/api/h5/pay/queryArrears?authVersion=v2&consNo={cno}"
MANUFACTURER = "华润燃气"