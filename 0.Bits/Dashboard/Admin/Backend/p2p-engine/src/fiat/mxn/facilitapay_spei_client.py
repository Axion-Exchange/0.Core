"""
SPEI CLIENT (MXN via Facilitapay)
=====================================
SPEI - Mexican interbank electronic payment system.
"""

from src.core.types import UnifiedPayment


class FacilitapaySpeiClient:
    """Mexican SPEI payment client via Facilitapay."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
    
    async def get_incoming_payments(self, limit: int = 50) -> list[UnifiedPayment]:
        """Get incoming MXN SPEI payments."""
        # TODO: Implement
        return []
    
    async def initiate_payout(
        self,
        amount: str,
        recipient_name: str,
        clabe: str,  # 18-digit Mexican bank account
        concept: str | None = None,
        reference: str | None = None,
    ) -> UnifiedPayment | None:
        """Send MXN via SPEI."""
        # TODO: Implement
        return None
