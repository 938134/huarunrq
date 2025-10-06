import asyncio, aiohttp, base64, json
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from .crypto import encrypt_param
from .const import *

class HuaRunRQCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, cnos: list[str], scan: int):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan))
        self.cnos = cnos
        self._session = aiohttp.ClientSession()

    async def _async_update_data(self):
        """返回 dict[cno -> data]"""
        tasks = [self._fetch_one(cno) for cno in self.cnos]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {cno: (res if not isinstance(res, Exception) else None) for cno, res in zip(self.cnos, results)}

    async def _fetch_one(self, cno: str):
        loop = asyncio.get_running_loop()
        param = await loop.run_in_executor(None, encrypt_param)
        body = {"USER": "bizH5", "PWD": param}
        b64_body = base64.urlsafe_b64encode(json.dumps(body).encode()).decode()

        url = f"https://mbhapp.crcgas.com/bizonline/pay/queryArrears?authVersion=v2&consNo={cno}"
        hdr = {"Content-Type": "application/json, text/plain, */*", "Param": b64_body}

        async with self._session.get(url, headers=hdr) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["dataResult"]   # 余额对象