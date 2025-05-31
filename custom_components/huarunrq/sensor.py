"""Platform for sensor integration."""
from datetime import timedelta
import logging
import base64
import time
import random
import json
import aiohttp
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, API_URL, MANUFACTURER

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HuaRunRQ sensor based on a config entry."""
    cno = config_entry.data.get("cno")
    name = config_entry.title
    scan_interval = config_entry.options.get("scan_interval", 3600)

    async def async_update_data():
        """Fetch data from API."""
        try:
            return await fetch_data(cno)
        except Exception as e:
            raise UpdateFailed(f"Error fetching data: {e}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=name,
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    # Do not immediately refresh data on setup
    async_add_entities([HuaRunRQSensor(coordinator, name, cno)], True)

async def fetch_data(cno):
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

    api_url = API_URL.format(cno=cno)
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

class HuaRunRQSensor(CoordinatorEntity, SensorEntity):
    """Representation of a HuaRunRQ Sensor."""

    def __init__(self, coordinator, name, cno):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._name = name
        self._cno = cno
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"{DOMAIN}_{self._cno}"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("totalGasBalance")
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data
        return {}

    @property
    def device_info(self):
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._cno)},
            name=self._name,
            manufacturer=MANUFACTURER,
            model=self._name,
            entry_type=DeviceEntryType.SERVICE,
        )