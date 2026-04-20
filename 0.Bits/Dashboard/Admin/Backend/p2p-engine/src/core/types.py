"""
UNIFIED TYPES
=============
Pydantic models defining the unified API format.
All clients convert external API responses to these types.

WORKFLOW:
1. Define new types here first
2. Add client method to base class
3. Implement in specific client
4. Expose via API route
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class ExchangeId(str, Enum):
    """Supported crypto exchanges."""
    BINANCE = "binance"
    BYBIT = "bybit"
    OKX = "okx"
    BITGET = "bitget"
    MEXC = "mexc"
    HTX = "htx"
    KUCOIN = "kucoin"
    BINANCE_BRL = "binance_brl"  # Second Binance account for BRL trading
    BINANCE_MXN = "binance_mxn"  # Third Binance account for MXN trading


# Exchange prefixes for internal order numbers (2-letter codes)
EXCHANGE_PREFIXES = {
    ExchangeId.BINANCE: "BI",
    ExchangeId.BYBIT: "BY",
    ExchangeId.OKX: "OK",
    ExchangeId.BITGET: "BG",
    ExchangeId.MEXC: "MX",
    ExchangeId.HTX: "HX",
    ExchangeId.KUCOIN: "KU",
    ExchangeId.BINANCE_BRL: "BB",  # BRL account prefix
    ExchangeId.BINANCE_MXN: "BX",  # MXN account prefix
}


def make_internal_order_number(exchange: ExchangeId | str, order_id: str) -> str:
    """
    Create standardized internal order number.
    
    Format: {2-letter exchange prefix}{last 6 digits of order_id}
    No hyphens.
    
    Examples:
        Binance 12345678901234 → BI901234
        Bitget 98765432109876 → BG109876
        
    Args:
        exchange: Exchange ID or string
        order_id: External order ID from exchange
        
    Returns:
        Internal order number (e.g., "BI123456")
    """
    # Get only the last 6 digits of the order ID
    order_suffix = order_id[-6:] if len(order_id) >= 6 else order_id.zfill(6)
    
    if isinstance(exchange, str):
        try:
            exchange = ExchangeId(exchange.lower())
        except ValueError:
            # Unknown exchange, use first 2 chars uppercase
            prefix = exchange.upper()[:2]
            return f"{prefix}{order_suffix}"
    
    prefix = EXCHANGE_PREFIXES.get(exchange, exchange.value.upper()[:2])
    return f"{prefix}{order_suffix}"


def parse_internal_order_number(internal_order_number: str) -> tuple[str, str]:
    """
    Parse internal order number into exchange prefix and order suffix.
    
    Args:
        internal_order_number: e.g., "BI123456" (2-letter prefix + 6-digit suffix)
        
    Returns:
        Tuple of (exchange_prefix, order_suffix)
    """
    if len(internal_order_number) < 3:
        return "", internal_order_number
    
    # First 2 chars are prefix, rest is order suffix
    return internal_order_number[:2], internal_order_number[2:]


def get_exchange_from_internal_order(internal_order_number: str) -> ExchangeId | None:
    """
    Extract exchange from internal order number.
    
    Args:
        internal_order_number: e.g., "BI123456"
        
    Returns:
        ExchangeId or None if unknown
    """
    prefix, _ = parse_internal_order_number(internal_order_number)
    
    # Reverse lookup
    for exchange, ex_prefix in EXCHANGE_PREFIXES.items():
        if ex_prefix == prefix:
            return exchange
    
    return None


class BankProvider(str, Enum):
    """Banking/fiat providers."""
    JANUAR = "januar"
    FACILITAPAY = "facilitapay"


class Currency(str, Enum):
    """Supported fiat currencies."""
    EUR = "EUR"
    USD = "USD"
    BRL = "BRL"
    COP = "COP"
    MXN = "MXN"


class CryptoAsset(str, Enum):
    """Supported crypto assets."""
    USDT = "USDT"
    USDC = "USDC"
    BTC = "BTC"
    ETH = "ETH"


class OrderSide(str, Enum):
    """Trade direction from OUR perspective."""
    BUY = "buy"
    SELL = "sell"


class OrderState(str, Enum):
    """
    Unified order state (internal + exchange).
    
    All states map to Binance API status codes via binance_code property.
    Internal-only states (ERROR, AGENT_*, REFUNDED) return None for binance_code.
    """
    # Active states - Binance: pending (1)
    NEW = "new"
    AWAITING_PAYMENT = "awaiting_payment"
    
    # Active states - Binance: paid (2)
    MARKED_AS_PAID = "marked_as_paid"
    DELAYED = "delayed"
    THIRD_PARTY_CONFIRMED = "third_party_confirmed"
    RELEASING = "releasing"
    
    # Active states - Binance: appealed (5)
    APPEALED = "appealed"
    
    # Terminal states
    COMPLETED = "completed"      # Binance: 3
    CANCELLED = "cancelled"      # Binance: 4
    EXPIRED = "expired"          # Binance: 6
    
    # Internal-only states (no Binance mapping)
    ERROR = "error"
    AGENT_REQUIRED = "agent_required"
    AGENT_PROCESSING = "agent_processing"
    REFUNDED = "refunded"
    
    @property
    def binance_code(self) -> int | None:
        """Get Binance API status code for this state."""
        mapping = {
            "new": 1,
            "awaiting_payment": 1,
            "marked_as_paid": 2,
            "delayed": 2,
            "third_party_confirmed": 2,
            "releasing": 2,
            "completed": 3,
            "cancelled": 4,
            "appealed": 5,
            "expired": 6,
        }
        return mapping.get(self.value)
    
    @property
    def is_active(self) -> bool:
        """Whether this state represents an active (non-terminal) order."""
        return self.binance_code in (1, 2, 5)
    
    @property
    def is_terminal(self) -> bool:
        """Whether this state is a terminal (final) state."""
        return self.value in ("completed", "cancelled", "expired", "refunded")
    
    @classmethod
    def from_binance_code(cls, code: int) -> "OrderState":
        """Convert Binance status code to OrderState."""
        mapping = {
            1: cls.AWAITING_PAYMENT,
            2: cls.MARKED_AS_PAID,
            3: cls.COMPLETED,
            4: cls.CANCELLED,
            5: cls.APPEALED,
            6: cls.EXPIRED,
        }
        return mapping.get(code, cls.AWAITING_PAYMENT)
    
    @classmethod
    def _missing_(cls, value: str) -> "OrderState | None":
        """
        Handle legacy status values from database.
        Maps old OrderStatus values to new OrderState values.
        """
        legacy_mapping = {
            "pending": cls.AWAITING_PAYMENT,
            "paid": cls.MARKED_AS_PAID,
        }
        return legacy_mapping.get(value.lower() if isinstance(value, str) else value)
    
    @classmethod
    def valid_transitions(cls) -> dict["OrderState", set["OrderState"]]:
        """
        Get all valid state transitions.
        
        Returns a dict mapping each state to the set of states it can transition to.
        This is the single source of truth for the state machine.
        """
        return {
            cls.NEW: {cls.AWAITING_PAYMENT, cls.CANCELLED, cls.ERROR},
            cls.AWAITING_PAYMENT: {cls.MARKED_AS_PAID, cls.DELAYED, cls.CANCELLED, cls.EXPIRED, cls.APPEALED},
            cls.DELAYED: {cls.MARKED_AS_PAID, cls.RELEASING, cls.THIRD_PARTY_CONFIRMED, cls.CANCELLED, cls.APPEALED, cls.COMPLETED},
            cls.MARKED_AS_PAID: {cls.RELEASING, cls.THIRD_PARTY_CONFIRMED, cls.DELAYED, cls.CANCELLED, cls.APPEALED},
            cls.THIRD_PARTY_CONFIRMED: {cls.RELEASING, cls.CANCELLED, cls.APPEALED},
            cls.RELEASING: {cls.COMPLETED, cls.ERROR, cls.APPEALED},
            cls.APPEALED: {cls.COMPLETED, cls.CANCELLED},
            cls.ERROR: {cls.AWAITING_PAYMENT, cls.RELEASING, cls.CANCELLED, cls.AGENT_REQUIRED},
            cls.AGENT_REQUIRED: {cls.AGENT_PROCESSING, cls.CANCELLED, cls.REFUNDED},
            cls.AGENT_PROCESSING: {cls.COMPLETED, cls.CANCELLED, cls.AWAITING_PAYMENT, cls.RELEASING, cls.REFUNDED},
            cls.REFUNDED: {cls.CANCELLED},
            # Terminal states have no outgoing transitions
            cls.COMPLETED: set(),
            cls.CANCELLED: set(),
            cls.EXPIRED: set(),
        }
    
    def can_transition_to(self, target: "OrderState") -> bool:
        """Check if this state can transition to the target state."""
        transitions = self.valid_transitions()
        if self not in transitions:
            return False
        return target in transitions[self]


# Legacy alias for backwards compatibility during migration
OrderStatus = OrderState


class PaymentStatus(str, Enum):
    """Payment transaction status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


# =============================================================================
# P2P ORDER
# =============================================================================

class Counterparty(BaseModel):
    """Info about the trading counterparty."""
    name: str
    real_name: str | None = None
    trade_count: int | None = None
    completion_rate: float | None = None


class UnifiedOrder(BaseModel):
    """
    Unified P2P order representation.
    All exchange clients convert their native format to this.
    """
    id: str = Field(description="Internal unified ID")
    external_id: str = Field(description="Original order ID from exchange")
    exchange: ExchangeId
    side: OrderSide
    status: OrderStatus
    
    crypto_asset: CryptoAsset
    crypto_amount: str
    fiat_currency: Currency
    fiat_amount: str
    price: str
    
    counterparty: Counterparty
    payment_method: str
    
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    
    raw: dict[str, Any] | None = Field(default=None, description="Original response for debugging")
    
    @property
    def internal_order_number(self) -> str:
        """
        Get standardized internal order number.
        
        Format: {EXCHANGE_PREFIX}-{ORDER_ID}
        Example: BIN-12345678
        
        Used as:
        - Payment reference for BUY orders
        - Payment reference for SELL orders
        - Cross-system tracking ID
        """
        return make_internal_order_number(self.exchange, self.external_id)


# =============================================================================
# CHAT MESSAGE
# =============================================================================

class MessageSender(str, Enum):
    US = "us"
    COUNTERPARTY = "counterparty"
    SYSTEM = "system"


class ChatAttachment(BaseModel):
    type: str  # "image" | "file"
    url: str


class ChatMessage(BaseModel):
    """Unified chat message."""
    id: str
    order_id: str
    exchange: ExchangeId
    sender: MessageSender
    content: str
    attachment: ChatAttachment | None = None
    timestamp: datetime
    read: bool = False


# =============================================================================
# P2P ADVERTISEMENT
# =============================================================================

class PriceType(str, Enum):
    FIXED = "fixed"
    FLOATING = "floating"


class UnifiedAd(BaseModel):
    """Unified P2P advertisement."""
    id: str
    external_id: str
    exchange: ExchangeId
    side: OrderSide
    active: bool
    
    crypto_asset: CryptoAsset
    fiat_currency: Currency
    price: str
    price_type: PriceType
    floating_rate: str | None = None
    
    available_amount: str
    min_limit: str
    max_limit: str
    
    payment_methods: list[str]
    auto_reply: str | None = None
    
    raw: dict[str, Any] | None = None


# =============================================================================
# PAYMENT (BANKING)
# =============================================================================

class PaymentDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class UnifiedPayment(BaseModel):
    """Unified payment/transaction from banking providers."""
    id: str
    external_id: str
    provider: BankProvider
    direction: PaymentDirection
    status: PaymentStatus
    
    amount: str
    currency: Currency
    
    sender_name: str | None = None
    sender_account: str | None = None
    receiver_name: str | None = None
    receiver_account: str | None = None
    
    reference: str | None = None
    payment_method: str
    
    created_at: datetime
    completed_at: datetime | None = None
    
    raw: dict[str, Any] | None = None


# =============================================================================
# BALANCE
# =============================================================================

class UnifiedBalance(BaseModel):
    """Balance for an asset/currency."""
    source: str  # ExchangeId or BankProvider
    asset: str
    available: str
    locked: str
    total: str
    updated_at: datetime



# =============================================================================
# API RESPONSE WRAPPER
# =============================================================================

from typing import Generic, TypeVar

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format."""
    success: bool
    data: T | None = None
    error: dict[str, str] | None = None
    meta: dict[str, Any] | None = None
