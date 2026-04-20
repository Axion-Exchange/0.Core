"""KUCOIN APP CLIENT - Full app automation (no P2P API)."""
from src.core.clients import ExchangeAppClient
from src.core.types import ExchangeId, UnifiedOrder, ChatMessage

class KucoinAppClient(ExchangeAppClient):
    def __init__(self):
        self.device = None
    
    @property
    def exchange_id(self) -> ExchangeId:
        return ExchangeId.KUCOIN
    
    async def connect_device(self, device_id: str) -> bool:
        return False
    
    async def is_connected(self) -> bool:
        return False
    
    async def get_active_orders(self) -> list[UnifiedOrder]:
        return []
    
    async def get_order(self, external_id: str) -> UnifiedOrder | None:
        return None
    
    async def mark_order_paid(self, external_id: str) -> bool:
        return False
    
    async def release_crypto(self, external_id: str) -> bool:
        return False
    
    async def get_chat_messages(self, order_id: str) -> list[ChatMessage]:
        return []
    
    async def send_chat_message(self, order_id: str, message: str) -> ChatMessage | None:
        return None

    async def send_chat_image(self, order_id: str, image_path: str) -> bool:
        return False
