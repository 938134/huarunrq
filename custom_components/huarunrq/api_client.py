# api_client.py
"""华润燃气API客户端"""
import base64
import json
import random
import time
from typing import Dict, Optional, Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

from .const import (
    API_BASE_URL, API_PUBLIC_KEY, API_USER, API_SECRET,
    ENDPOINT_QUERY_ARREARS,
    DEFAULT_REQUEST_TIMEOUT, API_MSG_SUCCESS
)

_LOGGER = logging.getLogger(__name__)


class HuaRunApiClient:
    """华润燃气API客户端"""
    
    def __init__(self, hass, cons_no: str):
        self.hass = hass
        self.cons_no = cons_no
        self._session = None
    
    async def _get_session(self):
        """获取HTTP会话"""
        if self._session is None:
            self._session = async_get_clientsession(self.hass)
        return self._session
    
    async def _get_auth_header(self) -> Dict[str, str]:
        """生成认证头"""
        # 生成加密参数
        timestamp = int(time.time() * 1000)
        random_num = random.randint(1000, 9999)
        data_to_encrypt = f"{API_SECRET}#{timestamp}#{random_num}"
        
        # 加载公钥
        public_key = serialization.load_pem_public_key(
            API_PUBLIC_KEY.encode("utf-8"),
            backend=default_backend()
        )
        
        # 加密
        encrypted_data = public_key.encrypt(
            data_to_encrypt.encode("utf-8"),
            padding.PKCS1v15()
        )
        base64_encrypted_data = base64.urlsafe_b64encode(encrypted_data).decode("utf-8")
        
        # 构建请求体
        request_body = {"USER": API_USER, "PWD": base64_encrypted_data}
        base64_encoded_body = base64.urlsafe_b64encode(
            json.dumps(request_body).encode("utf-8")
        ).decode("utf-8")
        
        return {
            "Content-Type": "application/json",
            "Param": base64_encoded_body
        }
    
    async def _request(self, endpoint: str, params: Dict = None) -> Any:
        """发送请求"""
        session = await self._get_session()
        headers = await self._get_auth_header()
        
        # 构建URL
        url = f"{API_BASE_URL}{endpoint}"
        if params:
            query_params = []
            for k, v in params.items():
                if v is not None:
                    query_params.append(f"{k}={v}")
            if query_params:
                url = f"{url}?{'&'.join(query_params)}"
        
        _LOGGER.debug(f"请求API: {url}")
        
        try:
            async with session.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT) as response:
                response_text = await response.text()
                _LOGGER.debug(f"API响应: {response_text[:200]}")
                
                result = json.loads(response_text)
                
                # 检查响应状态
                if result.get("statusCode") == "B0001":
                    raise ConnectionError(f"服务器异常: {result.get('msg', '未知错误')}")
                
                if result.get("msg") != API_MSG_SUCCESS:
                    _LOGGER.warning(f"API返回非成功状态: {result.get('msg')}")
                    return None
                
                return result.get("dataResult")
                
        except Exception as e:
            _LOGGER.error(f"API请求失败 [{endpoint}]: {e}")
            raise
    
    async def get_balance(self) -> Optional[float]:
        """获取当前余额"""
        try:
            params = {"authVersion": "v2", "consNo": self.cons_no}
            data = await self._request(ENDPOINT_QUERY_ARREARS, params)
            if data and isinstance(data, dict):
                return data.get("totalGasBalance")
            return None
        except Exception as e:
            _LOGGER.error(f"获取余额失败: {e}")
            return None