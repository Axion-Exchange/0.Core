"""OKX APP CLIENT - UIAutomator2 automation."""
from src.core.clients import ExchangeAppClient
from src.core.types import ExchangeId, UnifiedOrder, ChatMessage

class OkxAppClient(ExchangeAppClient):
    def __init__(self):
        self.device = None
    
    @property
    def exchange_id(self) -> ExchangeId:
        return ExchangeId.OKX
    
    async def connect_device(self, device_id: str) -> bool:
        return False
    
    async def is_connected(self) -> bool:
        return False
