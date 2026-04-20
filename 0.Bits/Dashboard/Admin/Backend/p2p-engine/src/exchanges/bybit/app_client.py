"""
BYBIT APP CLIENT (UIAutomator2)
===================================
App automation for features not in API.
"""

from src.core.clients import ExchangeAppClient
from src.core.types import ExchangeId, UnifiedOrder, ChatMessage


class BybitAppClient(ExchangeAppClient):
    """Bybit app client - implement UIAutomator2 automation."""
    
    def __init__(self):
        self.device = None
        self.device_id: str | None = None
    
    @property
    def exchange_id(self) -> ExchangeId:
        return ExchangeId.BYBIT
    
    async def connect_device(self, device_id: str) -> bool:
        self.device_id = device_id
        return False
    
    async def is_connected(self) -> bool:
        return False
    
    async def get_active_orders(self) -> list[UnifiedOrder]:
        return []
    
    async def get_chat_messages(self, order_id: str) -> list[ChatMessage]:
        return []
    
    async def send_chat_message(self, order_id: str, message: str) -> bool:
        return False
