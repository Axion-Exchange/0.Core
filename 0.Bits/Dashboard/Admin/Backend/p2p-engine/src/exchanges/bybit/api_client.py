"""
BYBIT API CLIENT
====================
Translates Bybit P2P API responses to unified format.
"""

from datetime import datetime
from typing import Any

import httpx

from src.core.clients import ExchangeApiClient
from src.core.types import ExchangeId, UnifiedOrder, UnifiedBalance, UnifiedAd


class BybitApiClient(ExchangeApiClient):
    """Bybit P2P API client - implement based on Bybit API docs."""
    
    BASE_URL = "https://api.bybit.com"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def exchange_id(self) -> ExchangeId:
        return ExchangeId.BYBIT
    
    async def is_ready(self) -> bool:
        # TODO: Implement connectivity check
        return False
    
    async def get_active_orders(self) -> list[UnifiedOrder]:
        # TODO: Implement based on Bybit P2P API
        return []
    
    async def get_order(self, external_id: str) -> UnifiedOrder | None:
        # TODO: Implement
        return None
    
    async def get_balances(self) -> list[UnifiedBalance]:
        # TODO: Implement
        return []
    
    async def get_ads(self) -> list[UnifiedAd]:
        # TODO: Implement
        return []
