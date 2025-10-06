"""DataUpdateCoordinator for HuaRunRQ."""
import asyncio, aiohttp, base64, json, logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import *

_LOGGER = logging.getLogger(__name__)


def _encrypt_param() -> str:
    """同步加密 Param"""
    from cryptography.hazmat.primitives import serialization, padding
    from cryptography.hazmat.backends import default_backend
    pem = BIZ_H5_PUBLIC_KEY_PEM
    public_key = serialization.load_pem_public_key(pem.encode(), backend=default_backend())
    plain = f"e5b871c278a84defa8817d22afc34338#{int(time.time() * 1000)}#{__import__('random').randint(1000, 9999)}"
    encrypted = public_key.encrypt(plain.encode(), padding.PKCS1v15())
    return base64.urlsafe_b64encode(encrypted).decode()


class HuaRunRQCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, cnos: list[str], scan: int):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan))
        self.cnos = cnos
        self._session = aiohttp.ClientSession()

    async def _async_update_data(self):
        tasks = [self._fetch_one(cno) for cno in self.cnos]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {cno: (res if not isinstance(res, Exception) else None) for cno, res in zip(self.cnos, results)}

    async def _fetch_one(self, cno: str):
        loop = asyncio.get_running_loop()
        param = await loop.run_in_executor(None, _encrypt_param)
        body = {"USER": "bizH5", "PWD": param}
        b64_body = base64.urlsafe_b64encode(json.dumps(body).encode()).decode()

        url = API_ARREARS.format(cno=cno)
        headers = {
            "Content-Type": "application/json, text/plain, */*",
            "Param": b64_body,
            "Cookie": "HWWAFSESID=dummy",   # 无需 bo-token
        }

        async with self._session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data.get("dataResult") is None:
                raise UpdateFailed("dataResult 为空")
            return data["dataResult"]