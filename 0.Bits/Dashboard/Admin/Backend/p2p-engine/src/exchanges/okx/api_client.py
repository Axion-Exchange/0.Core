"""OKX API CLIENT - Implement based on OKX P2P API docs."""
from src.core.clients import ExchangeApiClient
from src.core.types import ExchangeId, UnifiedOrder, UnifiedBalance

class OkxApiClient(ExchangeApiClient):
    def __init__(self, api_key: str, api_secret: str, passphrase: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
    
    @property
    def exchange_id(self) -> ExchangeId:
        return ExchangeId.OKX
    
    async def is_ready(self) -> bool:
        return False
    
    async def get_active_orders(self) -> list[UnifiedOrder]:
        return []
    
    async def get_order(self, external_id: str) -> UnifiedOrder | None:
        return None
    
    async def get_balances(self) -> list[UnifiedBalance]:
        return []
