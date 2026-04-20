"""
PAYMENT AMOUNT MATCHER
======================
Simple verification that payment amount matches order amount.

Ensures:
1. Payment currency matches order currency
2. Payment amount >= order amount (exact or slight overpayment OK)
3. Returns match result with any discrepancy details
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from src.core.types import UnifiedOrder, UnifiedPayment


@dataclass
class AmountMatchResult:
    """Result of amount verification."""
    matched: bool
    order_amount: Decimal
    payment_amount: Decimal
    difference: Decimal
    currency: str
    reason: str = ""
    
    @property
    def is_underpaid(self) -> bool:
        return self.difference < 0
    
    @property
    def is_overpaid(self) -> bool:
        return self.difference > 0
    
    @property
    def is_exact(self) -> bool:
        return self.difference == 0


class AmountMatcher:
    """
    Verifies payment amounts match order amounts.
    
    Rules:
    - Currency must match
    - Payment >= Order amount (exact or slight overpayment OK)
    - Small tolerance for rounding (0.01 EUR)
    """
    
    # Maximum underpayment tolerance (e.g., 0.01 EUR due to bank rounding)
    UNDERPAY_TOLERANCE = Decimal("0.01")
    
    # Maximum acceptable overpayment (e.g., 1.00 EUR - anything more is suspicious)
    MAX_OVERPAY = Decimal("1.00")
    
    def match(
        self,
        order: UnifiedOrder,
        payment: UnifiedPayment,
    ) -> AmountMatchResult:
        """
        Verify payment amount matches order expectation.
        
        Args:
            order: The Binance P2P order (expected amount)
            payment: The Januar EUR payment (received amount)
            
        Returns:
            AmountMatchResult with match status and details
        """
        # Extract amounts
        order_amount = self._to_decimal(order.fiat_amount)
        payment_amount = self._to_decimal(payment.amount)
        
        # Extract currencies
        order_currency = self._normalize_currency(order.fiat_currency)
        payment_currency = self._normalize_currency(payment.currency)
        
        # Currency check
        if order_currency != payment_currency:
            return AmountMatchResult(
                matched=False,
                order_amount=order_amount,
                payment_amount=payment_amount,
                difference=payment_amount - order_amount,
                currency=f"{payment_currency}/{order_currency}",
                reason=f"Currency mismatch: expected {order_currency}, got {payment_currency}"
            )
        
        # Calculate difference
        difference = payment_amount - order_amount
        
        # Check for underpayment
        if difference < -self.UNDERPAY_TOLERANCE:
            return AmountMatchResult(
                matched=False,
                order_amount=order_amount,
                payment_amount=payment_amount,
                difference=difference,
                currency=order_currency,
                reason=f"Underpaid by {abs(difference):.2f} {order_currency}"
            )
        
        # Check for suspicious overpayment
        if difference > self.MAX_OVERPAY:
            return AmountMatchResult(
                matched=False,
                order_amount=order_amount,
                payment_amount=payment_amount,
                difference=difference,
                currency=order_currency,
                reason=f"Suspicious overpayment: +{difference:.2f} {order_currency}"
            )
        
        # Amount matches (exact or acceptable range)
        if difference == 0:
            reason = "Exact match"
        elif difference < 0:
            reason = f"Minor underpayment within tolerance: {difference:.2f}"
        else:
            reason = f"Overpaid by {difference:.2f} (acceptable)"
        
        return AmountMatchResult(
            matched=True,
            order_amount=order_amount,
            payment_amount=payment_amount,
            difference=difference,
            currency=order_currency,
            reason=reason
        )
    
    def _to_decimal(self, value: str | float | Decimal) -> Decimal:
        """Convert value to Decimal, handling various formats."""
        if isinstance(value, Decimal):
            return value
        
        # Handle string with potential formatting
        str_val = str(value).strip().replace(",", "")
        
        # Remove negative sign if present (for payment amounts)
        if str_val.startswith("-"):
            str_val = str_val[1:]
        
        return Decimal(str_val).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    
    def _normalize_currency(self, currency: str | object) -> str:
        """Normalize currency to string."""
        # Handle Currency enum or string
        currency_str = str(currency)
        
        # Remove "Currency." prefix if present
        if currency_str.startswith("Currency."):
            currency_str = currency_str.replace("Currency.", "")
        
        return currency_str.upper()


# =============================================================================
# CONVENIENCE
# =============================================================================

def verify_amount(order: UnifiedOrder, payment: UnifiedPayment) -> AmountMatchResult:
    """Quick helper to verify payment amount."""
    matcher = AmountMatcher()
    return matcher.match(order, payment)
