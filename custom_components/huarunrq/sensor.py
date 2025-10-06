"""Platform for sensor integration."""
from datetime import timedelta
import logging
import requests
import voluptuous as vol
import base64
import time
import random
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_CNO = 'cno'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CNO): vol.Coerce(str),
    vol.Optional(CONF_NAME, default='华润燃气余额'): vol.Coerce(str),
})

MIN_TIME_BETWEEN_UPDATES = timedelta(hours=1)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    cno = config[CONF_CNO]
    name = config[CONF_NAME]

    add_entities([HuaRunRQBalanceSensor(name, cno)], True)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HuaRunRQ sensor based on a config entry."""
    cns = config_entry.data.get("cns", [])
    
    sensors = []
    for cno in cns:
        # 为每个户号创建余额传感器和用气量传感器
        sensors.append(HuaRunRQBalanceSensor(f"华润燃气 {cno} 余额", cno))
        sensors.append(HuaRunRQGasUsageSensor(f"华润燃气 {cno} 用气量", cno))
    
    async_add_entities(sensors, True)

class HuaRunRQBalanceSensor(SensorEntity):
    """Representation of a Balance Sensor."""

    def __init__(self, name, cno):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._cno = cno
        self._attributes = {}
        self._attr_unique_id = f"huarunrq_{cno}_balance"
        self._attr_icon = "mdi:cash"
        self._attr_unit_of_measurement = "CNY"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._attributes

    @property
    def device_info(self):
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={("huarunrq", self._cno)},
            name=f"华润燃气 {self._cno}",
            manufacturer="华润燃气",
            model="燃气用户",
            entry_type=DeviceEntryType.SERVICE,
        )

    def update(self):
        """Fetch new state data for the sensor."""
        try:
            # 获取余额数据
            data = self.get_arrears_data()
            self._state = data.get("totalGasBalance")
            self._attributes = {
                "户号": self._cno,
                "欠费金额": data.get("arrearsAmt"),
                "最近充值金额": data.get("lastChargeAmt"),
                "最近充值时间": data.get("lastChargeTime")
            }
            _LOGGER.info(f"Successfully updated balance data for {self._cno}: {data}")
        except Exception as e:
            _LOGGER.error("Error fetching balance data: %s", e)
            self._state = None
            self._attributes = {}

    def get_arrears_data(self):
        """Get the arrears data from the API."""
        public_key_pem = '''-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAIi4Gb8iOGcc05iqNilFb1gM6/iG4fSiECeEaEYN2cxaBVT+6zgp+Tp0TbGVqGMIB034BLaVdNZZPnqKFH4As8UCAwEAAQ==
-----END PUBLIC KEY-----'''

        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )

        data_to_encrypt = 'e5b871c278a84defa8817d22afc34338#' + str(int(time.time() * 1000)) + '#' + str(random.randint(1000, 9999))

        encrypted_data = public_key.encrypt(
            data_to_encrypt.encode('utf-8'),
            padding.PKCS1v15()
        )

        base64_encrypted_data = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

        request_body = {
            'USER': 'bizH5',
            'PWD': base64_encrypted_data
        }

        base64_encoded_body = base64.urlsafe_b64encode(json.dumps(request_body).encode('utf-8')).decode('utf-8')

        api_url = 'https://mbhapp.crcgas.com/bizonline/api/h5/pay/queryArrears?authVersion=v2&consNo=' + self._cno
        headers = {
            'Content-Type': 'application/json, text/plain, */*',
            'Param': base64_encoded_body
        }
        
        _LOGGER.debug(f"Balance Request URL: {api_url}")
        
        response = requests.get(api_url, headers=headers)
        
        _LOGGER.debug(f"Balance Response status: {response.status_code}")

        if response.status_code != 200:
            raise Exception(f"Balance API request failed with status code {response.status_code}")

        data = response.json()
        return data["dataResult"]


class HuaRunRQGasUsageSensor(SensorEntity):
    """Representation of a Gas Usage Sensor."""

    def __init__(self, name, cno):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._cno = cno
        self._attributes = {}
        self._attr_unique_id = f"huarunrq_{cno}_gas_usage"
        self._attr_icon = "mdi:fire"
        self._attr_unit_of_measurement = "m³"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._attributes

    @property
    def device_info(self):
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={("huarunrq", self._cno)},
            name=f"华润燃气 {self._cno}",
            manufacturer="华润燃气",
            model="燃气用户",
            entry_type=DeviceEntryType.SERVICE,
        )

    def update(self):
        """Fetch new state data for the sensor."""
        try:
            # 获取用气量数据
            data = self.get_bill_data()
            if data and "list" in data and data["list"]:
                latest_bill = data["list"][0]  # 获取最新账单
                self._state = latest_bill.get("gasVolume")
                self._attributes = {
                    "户号": self._cno,
                    "账单月份": latest_bill.get("billYm"),
                    "账单金额": latest_bill.get("billAmt"),
                    "账单状态": latest_bill.get("billStatus"),
                    "申请单号": latest_bill.get("applicationNo")
                }
                _LOGGER.info(f"Successfully updated gas usage data for {self._cno}: {latest_bill}")
            else:
                _LOGGER.warning(f"No bill data received for {self._cno}")
                self._state = None
                self._attributes = {"户号": self._cno, "状态": "无数据"}
                
        except Exception as e:
            _LOGGER.error("Error fetching gas usage data: %s", e)
            self._state = None
            self._attributes = {}

    def get_bill_data(self):
        """Get the bill data from the API."""
        public_key_pem = '''-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAIi4Gb8iOGcc05iqNilFb1gM6/iG4fSiECeEaEYN2cxaBVT+6zgp+Tp0TbGVqGMIB034BLaVdNZZPnqKFH4As8UCAwEAAQ==
-----END PUBLIC KEY-----'''

        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )

        data_to_encrypt = 'e5b871c278a84defa8817d22afc34338#' + str(int(time.time() * 1000)) + '#' + str(random.randint(1000, 9999))

        encrypted_data = public_key.encrypt(
            data_to_encrypt.encode('utf-8'),
            padding.PKCS1v15()
        )

        base64_encrypted_data = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

        request_body = {
            'USER': 'bizH5',
            'PWD': base64_encrypted_data
        }

        base64_encoded_body = base64.urlsafe_b64encode(json.dumps(request_body).encode('utf-8')).decode('utf-8')

        # 修正API URL - 使用正确的用气量API
        api_url = f'https://mbhapp.crcgas.com/bizonline/gasbill/getGasBillList4Chart?consNo={self._cno}&page=1&pageNum=6'
        headers = {
            'Content-Type': 'application/json, text/plain, */*',
            'Param': base64_encoded_body,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541022) XWEB/16467 Flue',
            'Accept': 'application/json, text/plain, */*',
            'Referer': f'https://mbhapp.crcgas.com/bill?billType=gas&appid=wx9d74a155dad6a4e2&state=2209'
        }
        
        _LOGGER.debug(f"Gas Usage Request URL: {api_url}")
        
        response = requests.get(api_url, headers=headers)
        
        _LOGGER.debug(f"Gas Usage Response status: {response.status_code}")
        _LOGGER.debug(f"Gas Usage Response content: {response.text}")

        if response.status_code != 200:
            raise Exception(f"Gas Usage API request failed with status code {response.status_code}")

        data = response.json()
        return data["dataResult"]