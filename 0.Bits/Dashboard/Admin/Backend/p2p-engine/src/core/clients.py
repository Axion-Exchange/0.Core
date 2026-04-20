"""
BASE CLIENT CLASSES
=======================
Abstract base classes defining what methods each client must implement.

WORKFLOW FOR NEW ENDPOINTS:
1. Add abstract method here
2. Implement in each exchange/bank client
3. Add API route
"""

from abc import ABC, abstractmethod
from typing import Any

from .types import (
    ExchangeId,
    UnifiedOrder,
    UnifiedAd,
    UnifiedBalance,
    ChatMessage,
    UnifiedPayment,
    OrderSide,
)


# =============================================================================
# EXCHANGE CLIENT (API-based)
# =============================================================================

class ExchangeApiClient(ABC):
    """
    Base class for exchange API clients.
    Exchanges with official P2P APIs (Binance, Bybit, OKX, Bitget) implement this.
    """
    
    @property
    @abstractmethod
    def exchange_id(self) -> ExchangeId:
        """Return the exchange identifier."""
        pass
    
    @property
    def display_name(self) -> str:
        """Human-readable exchange name."""
        return self.exchange_id.value.title()
    
    # -------------------------------------------------------------------------
    # CONNECTIVITY
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if credentials are valid and API is accessible."""
        pass
    
    # -------------------------------------------------------------------------
    # ORDERS
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def get_active_orders(self) -> list[UnifiedOrder]:
        """Get all currently open/pending orders."""
        pass
    
    @abstractmethod
    async def get_order(self, external_id: str) -> UnifiedOrder | None:
        """Get a specific order by its exchange ID."""
        pass
    
    async def get_order_history(
        self,
        limit: int = 50,
        start_time: str | None = None,
        end_time: str | None = None,
        side: OrderSide | None = None,
    ) -> list[UnifiedOrder]:
        """Get completed/cancelled order history. Override if supported."""
        return []
    
    async def mark_order_paid(self, external_id: str) -> bool:
        """Mark an order as paid (when buying). Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support mark_order_paid via API")
    
    async def release_crypto(self, external_id: str) -> bool:
        """Release crypto to buyer (when selling). Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support release_crypto via API")
    
    async def cancel_order(self, external_id: str) -> bool:
        """Cancel an order. Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support cancel_order via API")
    
    async def appeal_order(self, external_id: str, reason: str) -> bool:
        """Submit an appeal for an order. Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support appeal_order via API")
    
    # -------------------------------------------------------------------------
    # CHAT
    # -------------------------------------------------------------------------
    
    async def get_chat_messages(self, order_id: str) -> list[ChatMessage]:
        """Get chat messages for an order. Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support chat via API")
    
    async def send_chat_message(self, order_id: str, message: str) -> ChatMessage | None:
        """Send a chat message. Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support chat via API")
    
    # -------------------------------------------------------------------------
    # ADVERTISEMENTS
    # -------------------------------------------------------------------------
    
    async def get_ads(self) -> list[UnifiedAd]:
        """Get our active advertisements. Override if supported."""
        return []
    
    async def update_ad_price(self, ad_id: str, new_price: str) -> bool:
        """Update an ad's price. Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support ad updates via API")
    
    async def toggle_ad(self, ad_id: str, active: bool) -> bool:
        """Enable/disable an ad. Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support ad toggle via API")
    
    # -------------------------------------------------------------------------
    # BALANCES
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def get_balances(self) -> list[UnifiedBalance]:
        """Get all asset balances."""
        pass


# =============================================================================
# EXCHANGE CLIENT (UIAutomator-based)
# =============================================================================

class ExchangeAppClient(ABC):
    """
    Base class for exchange app automation clients.
    Used when APIs don't expose certain features (chat, etc.) or
    for exchanges without P2P APIs (MEXC, HTX, Kucoin).
    """
    
    @property
    @abstractmethod
    def exchange_id(self) -> ExchangeId:
        """Return the exchange identifier."""
        pass
    
    @property
    def display_name(self) -> str:
        return f"{self.exchange_id.value.title()} (App)"
    
    # -------------------------------------------------------------------------
    # DEVICE MANAGEMENT
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def connect_device(self, device_id: str) -> bool:
        """Connect to an Android device via ADB."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if device is connected and app is running."""
        pass
    
    # -------------------------------------------------------------------------
    # ORDERS (via app automation)
    # -------------------------------------------------------------------------
    
    async def get_active_orders(self) -> list[UnifiedOrder]:
        """Scrape active orders from app UI."""
        raise NotImplementedError()
    
    async def get_order(self, external_id: str) -> UnifiedOrder | None:
        """Navigate to and scrape order details."""
        raise NotImplementedError()
    
    async def mark_order_paid(self, external_id: str) -> bool:
        """Tap the 'Paid' button in the app."""
        raise NotImplementedError()
    
    async def release_crypto(self, external_id: str) -> bool:
        """Tap the 'Release' button in the app."""
        raise NotImplementedError()
    
    # -------------------------------------------------------------------------
    # CHAT (via app automation)
    # -------------------------------------------------------------------------
    
    async def get_chat_messages(self, order_id: str) -> list[ChatMessage]:
        """Scrape chat messages from app."""
        raise NotImplementedError()
    
    async def send_chat_message(self, order_id: str, message: str) -> ChatMessage | None:
        """Type and send a message in the app."""
        raise NotImplementedError()
    
    async def send_chat_image(self, order_id: str, image_path: str) -> bool:
        """Send an image in chat."""
        raise NotImplementedError()


# =============================================================================
# BANK CLIENT
# =============================================================================

class BankClient(ABC):
    """
    Base class for banking/fiat provider clients.
    """
    
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Return the provider identifier."""
        pass
    
    @property
    @abstractmethod
    def supported_currencies(self) -> list[str]:
        """Return list of supported currency codes."""
        pass
    
    @property
    def display_name(self) -> str:
        return self.provider_id.title()
    
    # -------------------------------------------------------------------------
    # CONNECTIVITY
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if credentials are valid."""
        pass
    
    # -------------------------------------------------------------------------
    # PAYMENTS
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def get_incoming_payments(
        self,
        currency: str | None = None,
        limit: int = 50,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[UnifiedPayment]:
        """Get incoming payment transactions."""
        pass
    
    async def get_outgoing_payments(
        self,
        currency: str | None = None,
        limit: int = 50,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[UnifiedPayment]:
        """Get outgoing payment transactions. Override if supported."""
        return []
    
    async def initiate_payout(
        self,
        amount: str,
        currency: str,
        recipient_name: str,
        recipient_account: str,
        payment_method: str,
        reference: str | None = None,
    ) -> UnifiedPayment | None:
        """Initiate an outgoing payment. Override if supported."""
        raise NotImplementedError(f"{self.display_name} does not support payouts via API")
    
    # -------------------------------------------------------------------------
    # BALANCES
    # -------------------------------------------------------------------------
    
    @abstractmethod
    async def get_balances(self) -> list[UnifiedBalance]:
        """Get all currency balances."""
        pass


# =============================================================================
# CRYPTO-FIAT CONVERTER (Januar specific)
# =============================================================================

class CryptoFiatConverter(ABC):
    """
    Base class for crypto/fiat conversion providers.
    Januar provides both EUR banking AND USDC liquidity conversions.
    """
    
    @abstractmethod
    async def get_conversion_rate(
        self,
        from_asset: str,
        to_asset: str,
        amount: str,
    ) -> dict[str, str]:
        """Get a quote for conversion. Returns rate and fees."""
        pass
    
    @abstractmethod
    async def buy_crypto(
        self,
        fiat_amount: str,
        fiat_currency: str,
        crypto_asset: str,
    ) -> dict[str, Any]:
        """Buy crypto with fiat. Returns tx details."""
        pass
    
    @abstractmethod
    async def sell_crypto(
        self,
        crypto_amount: str,
        crypto_asset: str,
        fiat_currency: str,
    ) -> dict[str, Any]:
        """Sell crypto for fiat. Returns tx details."""
        pass
