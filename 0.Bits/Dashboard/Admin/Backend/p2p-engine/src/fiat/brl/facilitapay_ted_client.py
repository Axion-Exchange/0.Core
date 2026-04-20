"""
TED CLIENT (BRL via Facilitapay)
====================================
TED - Brazilian bank wire transfer.
"""

from src.core.types import UnifiedPayment


class FacilitapayTedClient:
    """Brazilian TED wire transfer client via Facilitapay."""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
    
    async def get_incoming_payments(self, limit: int = 50) -> list[UnifiedPayment]:
        """Get incoming BRL TED payments."""
        # TODO: Implement
        return []
    
    async def initiate_payout(
        self,
        amount: str,
        recipient_name: str,
        recipient_cpf: str,
        bank_code: str,
        branch: str,
        account: str,
        account_type: str,  # "checking" or "savings"
    ) -> UnifiedPayment | None:
        """Send BRL via TED wire."""
        # TODO: Implement
        return None
