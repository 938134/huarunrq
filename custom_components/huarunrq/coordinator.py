"""Data update coordinator for HuaRunRQ."""
import asyncio
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HuaRunRQAPI
from .const import CONF_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class HuaRunRQDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HuaRunRQ data."""

    def __init__(self, hass, cno, config_entry):
        """Initialize global data updater."""
        self.cno = cno
        self.api = HuaRunRQAPI()
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
            arrears_data = await self.api.async_get_arrears(self.cno)
            if arrears_data:
                data.update(arrears_data)
            
            # 获取账单列表，提取最新月份用气量
            bill_data = await self.api.async_get_bill_list(self.cno)
            if bill_data and "list" in bill_data and bill_data["list"]:
                latest_bill = bill_data["list"][0]  # 最新账单
                data.update({
                    "current_gas_usage": latest_bill.get("gasVolume"),
                    "current_bill_month": latest_bill.get("billYm"),
                    "current_bill_amount": latest_bill.get("billAmt"),
                    "current_bill_status": latest_bill.get("billStatus")
                })
            
            return data
            
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err