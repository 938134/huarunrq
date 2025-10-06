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

def generate_encrypted_params():
    """生成加密的请求参数 - 使用原来的固定格式"""
    # 固定的公钥
    public_key_pem = '''-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAIi4Gb8iOGcc05iqNilFb1gM6/iG4fSiECeEaEYN2cxaBVT+6zgp+Tp0TbGVqGMIB034BLaVdNZZPnqKFH4As8UCAwEAAQ==
-----END PUBLIC KEY-----'''

    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )

    # 使用原来的固定格式，只随机化时间戳和随机数部分
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

    return base64_encoded_body

def make_api_request(api_url):
    """通用的API请求方法"""
    encrypted_params = generate_encrypted_params()
    
    headers = {
        'Content-Type': 'application/json, text/plain, */*',
        'Param': encrypted_params
    }
    
    _LOGGER.debug(f"API Request URL: {api_url}")
    _LOGGER.debug(f"Encrypted Params: {encrypted_params}")
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        
        _LOGGER.debug(f"API Response status: {response.status_code}")
        _LOGGER.debug(f"API Response headers: {dict(response.headers)}")

        if response.status_code != 200:
            # 记录详细的错误信息
            error_detail = f"Status: {response.status_code}, Response: {response.text}"
            _LOGGER.error(f"API request failed: {error_detail}")
            raise Exception(f"API request failed: {error_detail}")

        data = response.json()
        _LOGGER.debug(f"API Response data: {data}")
        return data.get("dataResult", {})
        
    except requests.exceptions.Timeout:
        error_msg = "API request timeout"
        _LOGGER.error(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "API connection error"
        _LOGGER.error(error_msg)
        raise Exception(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"API response JSON decode error: {e}"
        _LOGGER.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"API request error: {str(e)}"
        _LOGGER.error(error_msg)
        raise Exception(error_msg)

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
            # 使用通用方法获取余额数据
            api_url = f'https://mbhapp.crcgas.com/bizonline/pay/queryArrears?consNo={self._cno}'
            data = make_api_request(api_url)
            
            self._state = data.get("totalGasBalance")
            self._attributes = {
                "户号": self._cno,
                "欠费金额": data.get("arrearsAmt"),
                "最近充值金额": data.get("lastChargeAmt"),
                "最近充值时间": data.get("lastChargeTime")
            }
            _LOGGER.info(f"Successfully updated balance data for {self._cno}: {self._state}")
        except Exception as e:
            _LOGGER.error("Error fetching balance data: %s", e)
            self._state = None
            self._attributes = {"错误": str(e)}


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
            # 使用通用方法获取用气量数据
            api_url = f'https://mbhapp.crcgas.com/bizonline/gasbill/getGasBillList4Chart?consNo={self._cno}&page=1&pageNum=6'
            data = make_api_request(api_url)
            
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
                _LOGGER.info(f"Successfully updated gas usage data for {self._cno}: {self._state}")
            else:
                _LOGGER.warning(f"No bill data received for {self._cno}")
                self._state = None
                self._attributes = {"户号": self._cno, "状态": "无数据"}
                
        except Exception as e:
            _LOGGER.error("Error fetching gas usage data: %s", e)
            self._state = None
            self._attributes = {"错误": str(e)}