"""Data update coordinator for HuaRunRQ."""
import asyncio
import logging
import base64
import json
import random
import time
import aiohttp
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, API_QUERY_ARREARS, API_GAS_BILL_LIST

_LOGGER = logging.getLogger(__name__)

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

    def __init__(self, hass, cno, config_entry):
        """Initialize global data updater."""
        self.cno = cno
        scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, 3600)
        
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