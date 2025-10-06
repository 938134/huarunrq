"""API client for HuaRunRQ."""
import base64
import json
import random
import time
import aiohttp
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from .const import PUBLIC_KEY, API_QUERY_ARREARS, API_GAS_BILL_LIST

class HuaRunRQAPI:
    """API client for HuaRunRQ."""
    
    def __init__(self):
        """Initialize the API client."""
        self.session = None
        
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def _make_request(self, url):
        """Make API request with encrypted authentication."""
        await self._ensure_session()
        
        # 加密认证数据
        public_key = serialization.load_pem_public_key(
            PUBLIC_KEY.encode('utf-8'),
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
            'Param': base64_encoded_body,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("dataResult", {})
                else:
                    raise Exception(f"API request failed with status code {response.status}")
        except Exception as e:
            raise Exception(f"Request error: {e}")
    
    async def async_get_arrears(self, cno):
        """Get arrears and balance information."""
        url = API_QUERY_ARREARS.format(cno=cno)
        return await self._make_request(url)
    
    async def async_get_bill_list(self, cno):
        """Get gas bill list with usage information."""
        url = API_GAS_BILL_LIST.format(cno=cno)
        return await self._make_request(url)
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()