"""Sensor platform for HuaRunRQ —— 零 bo-token，Param 签名即可。"""
import asyncio, base64, json, random, time, logging
from datetime import timedelta
import aiohttp
from cryptography.hazmat.primitives import serialization, padding
from cryptography.hazmat.backends import default_backend

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo
from .const import *


# ---------- 加密工具 ----------
def _encrypt_param() -> str:
    pem = BIZ_H5_PUBLIC_KEY_PEM
    public_key = serialization.load_pem_public_key(pem.encode(), backend=default_backend())
    plain = f"e5b871c278a84defa8817d22afc34338#{int(time.time() * 1000)}#{random.randint(1000, 9999)}"
    encrypted = public_key.encrypt(plain.encode(), padding.PKCS1v15())
    return base64.urlsafe_b64encode(encrypted).decode()


# ---------- 异步获取一户数据 ----------
async def fetch_data(cno: str) -> dict:
    loop = asyncio.get_running_loop()
    param = await loop.run_in_executor(None, _encrypt_param)
    body = {"USER": "bizH5", "PWD": param}
    b64_body = base64.urlsafe_b64encode(json.dumps(body).encode()).decode()

    url = API_ARREARS.format(cno=cno)
    headers = {
        "Content-Type": "application/json, text/plain, */*",
        "Param": b64_body,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data.get("dataResult") is None:
                raise UpdateFailed("dataResult 为空")
            return data["dataResult"]


# ---------- Coordinator ----------
class HuaRunRQCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, cnos: list[str], scan: int):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan))
        self.cnos = cnos
        self._session = aiohttp.ClientSession()

    async def _async_update_data(self):
        tasks = [fetch_data(cno) for cno in self.cnos]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {cno: (res if not isinstance(res, Exception) else None) for cno, res in zip(self.cnos, results)}


# ---------- 平台入口（动态设备工厂） ----------
async def async_setup_entry(hass, entry, async_add_entities):
    """每户号 1 设备 + 完整传感器套件"""
    coord = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for cno in coord.cnos:
        device = DeviceInfo(identifiers={(DOMAIN, cno)}, name=f"华润燃气 {cno}", manufacturer="华润燃气")
        entities.extend([
            BalanceSensor(coord, cno, device),
            LatestGasSensor(coord, cno, device),
            LatestMoneySensor(coord, cno, device),
            CurrentStepSensor(coord, cno, device),
            YearTotalSensor(coord, cno, device),
            InvoiceNoSensor(coord, cno, device),
        ])
    async_add_entities(entities)


# ---------- 传感器类 ----------
class BalanceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_balance"
        self._attr_name = f"{cno} 账户余额"
        self._attr_unit_of_measurement = "元"
        self._attr_icon = "mdi:currency-cny"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        return -data.get("arrearsMoney", 0) if data else None


class LatestGasSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_latest_gas"
        self._attr_name = f"{cno} 最新用气量"
        self._attr_unit_of_measurement = "m³"
        self._attr_icon = "mdi:fire"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        return data.get("totalGasNum") or data.get("gasNum") or None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.cno)
        return {"records": data.get("bills", [])} if data else {}


class LatestMoneySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_latest_money"
        self._attr_name = f"{cno} 最新金额"
        self._attr_unit_of_measurement = "元"
        self._attr_icon = "mdi:cash"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        return data.get("money") if data else None


class CurrentStepSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_current_step"
        self._attr_name = f"{cno} 当前阶梯"
        self._attr_icon = "mdi:stairs"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        return data.get("step") if data else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.cno)
        return {"stepDetail": data.get("stepDetail", [])} if data else {}


class YearTotalSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_year_total"
        self._attr_name = f"{cno} 年度累计用气"
        self._attr_unit_of_measurement = "m³"
        self._attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        if not data or not data.get("bills"):
            return None
        return round(sum(b["gasNum"] for b in data["bills"]), 2)


class InvoiceNoSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, cno, device):
        super().__init__(coordinator)
        self.cno = cno
        self._attr_device_info = device
        self._attr_unique_id = f"{cno}_invoice_no"
        self._attr_name = f"{cno} 发票号"
        self._attr_icon = "mdi:file-document-check"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.cno)
        return data.get("invoiceNo") if data else None