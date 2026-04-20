"""
PSE CLIENT (COP via Facilitapay)
====================================
PSE (Pagos Seguros en Línea) - Colombian online bank transfers.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx

from src.core.types import (
    BankProvider,
    Currency,
    PaymentDirection,
    PaymentStatus,
    UnifiedPayment,
    UnifiedBalance,
)


class FacilitapayPseClient:
    """
    Colombian PSE payment client via Facilitapay.
    """
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: dict[str, Any] | None = None
    ) -> dict:
        """Make Facilitapay API request."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        if method == "GET":
            response = await self.client.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                params=data
            )
        else:
            response = await self.client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=data
            )
        
        response.raise_for_status()
        return response.json()
    
    async def get_incoming_payments(self, limit: int = 50) -> list[UnifiedPayment]:
        """Get incoming COP PSE payments."""
        # TODO: Implement based on Facilitapay API
        return []
    
    async def initiate_payout(
        self,
        amount: str,
        recipient_name: str,
        recipient_account: str,
        bank_code: str,
        reference: str | None = None,
    ) -> UnifiedPayment | None:
        """Send COP via PSE."""
        # TODO: Implement
        return None
    
    async def get_balance(self) -> UnifiedBalance | None:
        """Get COP balance."""
        # TODO: Implement
        return None
    
    def _transform_payment(self, raw: dict[str, Any], direction: str) -> UnifiedPayment:
        """Transform Facilitapay payment to unified format."""
        return UnifiedPayment(
            id=f"uni_{uuid4().hex[:12]}",
            external_id=str(raw.get("id", "")),
            provider=BankProvider.FACILITAPAY,
            direction=PaymentDirection(direction),
            status=PaymentStatus.PENDING,
            amount=str(raw.get("amount", "0")),
            currency=Currency.COP,
            sender_name=raw.get("sender_name"),
            receiver_name=raw.get("receiver_name"),
            payment_method="PSE",
            created_at=datetime.now(),
            raw=raw
        )
