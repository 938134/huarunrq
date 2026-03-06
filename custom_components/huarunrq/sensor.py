"""Sensor platform for HuaRun Gas integration."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
import time
from datetime import timedelta
from typing import Any

import aiohttp
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_RENMINBI
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_CNO,
    CONF_UPDATE_INTERVAL,
    ATTR_GAS_NUMBER,
    ATTR_UPDATE_INTERVAL,
    ATTR_LAST_UPDATE,
    API_BASE_URL,
    API_QUERY_ARREARS,
    PUBLIC_KEY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HuaRun Gas sensor based on a config entry."""
    coordinator = HuaRunGasDataCoordinator(hass, entry)
    
    # 首次数据获取
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([HuaRunGasSensor(coordinator, entry)], True)


class HuaRunGasDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HuaRun Gas data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = entry
        self.cno = entry.options.get(CONF_CNO, entry.data[CONF_CNO])
        self.update_interval_hours = entry.options.get(
            CONF_UPDATE_INTERVAL, 
            24
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.cno}",
            update_interval=timedelta(hours=self.update_interval_hours),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            return await self._fetch_gas_data()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def _fetch_gas_data(self) -> dict[str, Any]:
        """Fetch gas balance data from API."""
        session = async_get_clientsession(self.hass)
        
        try:
            # 加载公钥
            public_key = serialization.load_pem_public_key(
                PUBLIC_KEY.encode("utf-8"),
                backend=default_backend()
            )

            # 生成加密参数
            timestamp = int(time.time() * 1000)
            random_num = random.randint(1000, 9999)
            data_to_encrypt = f"e5b871c278a84defa8817d22afc34338#{timestamp}#{random_num}"
            
            encrypted_data = public_key.encrypt(
                data_to_encrypt.encode("utf-8"),
                padding.PKCS1v15()
            )
            base64_encrypted_data = base64.urlsafe_b64encode(encrypted_data).decode("utf-8")

            # 构建请求
            request_body = {"USER": "bizH5", "PWD": base64_encrypted_data}
            base64_encoded_body = base64.urlsafe_b64encode(
                json.dumps(request_body).encode("utf-8")
            ).decode("utf-8")

            # 调用API
            api_url = f"{API_BASE_URL}{API_QUERY_ARREARS}"
            headers = {
                "Content-Type": "application/json",
                "Param": base64_encoded_body
            }
            params = {
                "authVersion": "v2",
                "consNo": self.cno
            }
            
            async with session.get(
                api_url, 
                headers=headers, 
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                response.raise_for_status()
                response_text = await response.text()
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as err:
                    raise ValueError(f"Invalid JSON response: {response_text[:200]}") from err

                # 检查API响应
                if result.get("statusCode") == "B0001":
                    raise ConnectionError(f"Server error: {result.get('msg', 'Unknown error')}")
                
                if result.get("msg") != "操作成功":
                    raise ValueError(f"API error: {result.get('msg')}")

                data_result = result.get("dataResult", {})
                return {
                    "balance": data_result.get("totalGasBalance", 0),
                    "last_update": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

        except asyncio.TimeoutError as err:
            raise ConnectionError("API request timeout") from err
        except aiohttp.ClientError as err:
            raise ConnectionError(f"Network error: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error in API request")
            raise


class HuaRunGasSensor(CoordinatorEntity, SensorEntity):
    """Representation of a HuaRun Gas sensor."""

    def __init__(
        self, 
        coordinator: HuaRunGasDataCoordinator, 
        entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.cno = coordinator.cno
        
        self._attr_unique_id = f"{DOMAIN}_{self.cno}"
        self._attr_name = f"华润燃气 {self.cno[-4:]}"
        self._attr_native_unit_of_measurement = CURRENCY_RENMINBI
        self._attr_device_class = "monetary"
        self._attr_icon = "mdi:gas-station"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("balance")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            ATTR_GAS_NUMBER: self.cno,
            ATTR_UPDATE_INTERVAL: self.coordinator.update_interval_hours,
        }
        
        if self.coordinator.data:
            attrs[ATTR_LAST_UPDATE] = self.coordinator.data.get("last_update")
        
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.cno)},
            name="华润燃气表",
            manufacturer="华润燃气",
            model="智能燃气表",
            entry_type=DeviceEntryType.SERVICE,
        )