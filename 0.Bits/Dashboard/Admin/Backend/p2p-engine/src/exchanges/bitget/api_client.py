"""BITGET API CLIENT - Implement based on Bitget P2P API docs."""
import time
import hmac
import base64
import json
import httpx
from src.core.clients import ExchangeApiClient
from src.core.types import ExchangeId, UnifiedOrder, UnifiedBalance

class BitgetApiClient(ExchangeApiClient):
    def __init__(self, api_key: str, api_secret: str, passphrase: str = ''):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.base_url = 'https://api.bitget.com'
    
    @property
    def exchange_id(self) -> ExchangeId:
        return ExchangeId.BITGET
    
    def _sign(self, method: str, path: str, timestamp: str, body: str) -> str:
        message = str(timestamp) + method.upper() + path + (body if body else '')
        mac = hmac.new(
            bytes(self.api_secret, 'utf8'),
            bytes(message, 'utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode('utf-8')

    async def _request(self, method: str, endpoint: str, auth: bool = True, params=None, data=None):
        url = f'{self.base_url}{endpoint}'
        headers = {'Content-Type': 'application/json'}
        
        if auth:
            timestamp = str(int(time.time() * 1000))
            body_str = json.dumps(data) if data else ''
            
            # Form path including query string for signature
            path_for_sign = endpoint
            if params:
                query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
                path_for_sign = f'{endpoint}?{query_string}'

            sign = self._sign(method, path_for_sign, timestamp, body_str)
            
            headers.update({
                'ACCESS-KEY': self.api_key,
                'ACCESS-SIGN': sign,
                'ACCESS-TIMESTAMP': timestamp,
                'ACCESS-PASSPHRASE': self.passphrase,
                'locale': 'en-US'
            })
            
        async with httpx.AsyncClient() as client:
            req = client.build_request(method, url, headers=headers, params=params, json=data)
            resp = await client.send(req)
            resp.raise_for_status()
            return resp.json()

    async def is_ready(self) -> bool:
        try:
            res = await self._request('GET', '/api/v2/spot/account/info', auth=True)
            return res.get('code') == '00000'
        except Exception:
            return False

    async def get_spot_fills(self, symbol: str = 'USDTUSDC', limit: int = 100):
        # Bitget V2 spot fills
        # API: /api/v2/spot/trade/fills
        params = {'symbol': symbol, 'limit': str(limit)}
        res = await self._request('GET', '/api/v2/spot/trade/fills', auth=True, params=params)
        return res.get('data', [])
        
    async def get_active_orders(self) -> list[UnifiedOrder]:
        return []
    
    async def get_order(self, external_id: str) -> UnifiedOrder | None:
        return None
    
    async def get_balances(self) -> list[UnifiedBalance]:
        return []
