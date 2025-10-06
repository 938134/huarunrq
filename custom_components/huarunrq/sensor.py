"""Platform for sensor integration."""
import asyncio
import logging
import base64
import json
import random
import time
import aiohttp
from datetime import timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, MANUFACTURER, SENSOR_TYPES, CONF_SCAN_INTERVAL, API_QUERY_ARREARS, API_GAS_BILL_LIST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up the HuaRunRQ sensor based on a config entry."""
    cns = config_entry.data["cns"]
    scan_interval = config_entry.options.get("scan_interval", 3600)

    # 为每个户号创建协调器和传感器
    for cno in cns:
        coordinator = HuaRunRQDataUpdateCoordinator(hass, cno, scan_interval)
        await coordinator.async_config_entry_first_refresh()
        
        # 为每个户号创建所有传感器
        sensors = []
        for sensor_type in SENSOR_TYPES:
            sensors.append(HuaRunRQSensor(coordinator, cno, sensor_type))
        
        async_add_entities(sensors, True)

async def fetch_data(cno, api_url):
    """Fetch data from the API asynchronously."""
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

    headers = {
        'Content-Type': 'application/json, text/plain, */*',
        'Param': base64_encoded_body
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data["dataResult"]
            else:
                raise Exception(f"API request failed with status code {response.status}")

class HuaRunRQDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HuaRunRQ data."""

    def __init__(self, hass, cno, scan_interval):
        """Initialize global data updater."""
        self.cno = cno
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"华润燃气 {cno}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            data = {}
            
            # 获取余额信息
            arrears_url = API_QUERY_ARREARS.format(cno=self.cno)
            _LOGGER.info(f"Fetching arrears data for {self.cno}")
            arrears_data = await fetch_data(self.cno, arrears_url)
            if arrears_data:
                data.update(arrears_data)
                _LOGGER.info(f"Arrears data received: {arrears_data}")
            else:
                _LOGGER.warning(f"No arrears data received for {self.cno}")
            
            # 获取账单列表，提取最新月份用气量
            bill_url = API_GAS_BILL_LIST.format(cno=self.cno)
            _LOGGER.info(f"Fetching bill data for {self.cno}")
            bill_data = await fetch_data(self.cno, bill_url)
            if bill_data and "list" in bill_data and bill_data["list"]:
                latest_bill = bill_data["list"][0]  # 最新账单
                data.update({
                    "current_gas_usage": latest_bill.get("gasVolume"),
                    "current_bill_month": latest_bill.get("billYm"),
                    "current_bill_amount": latest_bill.get("billAmt"),
                    "current_bill_status": latest_bill.get("billStatus")
                })
                _LOGGER.info(f"Bill data received: {bill_data}")
            else:
                _LOGGER.warning(f"No bill data received for {self.cno}")
            
            return data
            
        except Exception as err:
            _LOGGER.error(f"Error fetching data for {self.cno}: {err}")
            raise UpdateFailed(f"Error communicating with API: {err}") from err

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
            balance = data.get("totalGasBalance")
            # 确保返回的是数字或None
            if balance is not None:
                try:
                    return float(balance)
                except (ValueError, TypeError):
                    return None
            return None
        elif self._sensor_type == "gas_usage":
            usage = data.get("current_gas_usage")
            # 确保返回的是数字或None
            if usage is not None:
                try:
                    return float(usage)
                except (ValueError, TypeError):
                    return None
            return None
        
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