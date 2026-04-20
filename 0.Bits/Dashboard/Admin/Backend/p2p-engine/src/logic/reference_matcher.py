"""
PAYMENT REFERENCE MATCHER
=========================
Primary identifier for matching payments to orders.

Reference Format: XX + NNNNNN
- XX: 2-letter exchange code (BI, BY, OK, BT, ME, KU, HT)
- NNNNNN: Last 6 digits of order number

Examples:
- BI123456 (Binance order ending in 123456)
- BT789012 (Bitget order ending in 789012)

If reference matches exactly, name/amount requirements are relaxed.
"""

import re
from dataclasses import dataclass
from typing import Any

from src.core.types import UnifiedOrder, UnifiedPayment


# Exchange code mapping
EXCHANGE_CODES = {
    "binance": "BI",
    "bybit": "BY",
    "okx": "OK",
    "bitget": "BT",
    "mexc": "ME",
    "kucoin": "KU",
    "htx": "HT",
}

# Reverse mapping for lookup
CODE_TO_EXCHANGE = {v: k for k, v in EXCHANGE_CODES.items()}

# Reference pattern: 2 letters + 6 digits
REFERENCE_PATTERN = re.compile(r'\b([A-Z]{2})(\d{6})\b')


@dataclass
class ReferenceMatchResult:
    """Result of reference matching."""
    matched: bool
    reference_found: str | None  # The reference found in payment
    expected_reference: str | None  # The expected reference from order
    exchange: str | None
    order_suffix: str | None
    reason: str = ""


def generate_reference(exchange: str, order_id: str) -> str:
    """
    Generate payment reference from exchange and order ID.
    
    Args:
        exchange: Exchange name (binance, bybit, etc.)
        order_id: Full order ID
        
    Returns:
        Reference string like "BI123456"
    """
    code = EXCHANGE_CODES.get(exchange.lower(), "XX")
    
    # Extract last 6 digits from order ID
    digits = re.sub(r'\D', '', order_id)  # Remove non-digits
    suffix = digits[-6:] if len(digits) >= 6 else digits.zfill(6)
    
    return f"{code}{suffix}"


def extract_reference(text: str) -> str | None:
    """
    Extract payment reference from text (payment reference field, memo, etc.)
    
    Args:
        text: Text to search for reference
        
    Returns:
        Reference string if found, None otherwise
    """
    if not text:
        return None
    
    # Search for pattern
    match = REFERENCE_PATTERN.search(text.upper())
    if match:
        return match.group(0)
    
    return None


def parse_reference(reference: str) -> tuple[str | None, str | None]:
    """
    Parse a reference into exchange and order suffix.
    
    Args:
        reference: Reference string like "BI123456"
        
    Returns:
        (exchange_name, order_suffix) or (None, None)
    """
    match = REFERENCE_PATTERN.match(reference.upper())
    if not match:
        return None, None
    
    code = match.group(1)
    suffix = match.group(2)
    
    exchange = CODE_TO_EXCHANGE.get(code)
    return exchange, suffix


class ReferenceMatcher:
    """
    Matches payment references to orders.
    
    This is the PRIMARY matching method - if reference matches,
    name/amount requirements can be relaxed.
    """
    
    def match(
        self,
        order: UnifiedOrder,
        payment: UnifiedPayment,
        exchange: str = "binance"
    ) -> ReferenceMatchResult:
        """
        Check if payment reference matches order.
        
        Args:
            order: The P2P order
            payment: The bank payment
            exchange: Exchange name for code generation
            
        Returns:
            ReferenceMatchResult with match status
        """
        # Generate expected reference from order
        order_id = order.id if hasattr(order, 'id') else ""
        if hasattr(order, 'external_id'):
            # Use external_id if available as it is the source of truth for reference
            order_id = order.external_id
            
        expected_ref = generate_reference(exchange, order_id)
        
        # Debug reference generation
        if "212416" in order_id or "521853" in expected_ref:
             print(f"DEBUG REF: IDs: {getattr(order, 'id', 'N/A')} / {getattr(order, 'external_id', 'N/A')}")
             print(f"DEBUG REF: Expected: {expected_ref}, Calculated from: {order_id}")
        
        # Extract reference from payment
        payment_ref = self._extract_payment_reference(payment)
        
        if not payment_ref:
            return ReferenceMatchResult(
                matched=False,
                reference_found=None,
                expected_reference=expected_ref,
                exchange=exchange,
                order_suffix=expected_ref[2:] if expected_ref else None,
                reason="No reference found in payment"
            )
        
        # Compare references
        if payment_ref.upper() == expected_ref.upper():
            return ReferenceMatchResult(
                matched=True,
                reference_found=payment_ref,
                expected_reference=expected_ref,
                exchange=exchange,
                order_suffix=expected_ref[2:],
                reason="Reference matches exactly"
            )
        
        # Check if just the suffix matches (user might use wrong exchange code)
        expected_suffix = expected_ref[2:]
        found_suffix = payment_ref[2:] if len(payment_ref) >= 8 else None
        
        if found_suffix == expected_suffix:
            return ReferenceMatchResult(
                matched=True,  # Still accept - suffix is correct
                reference_found=payment_ref,
                expected_reference=expected_ref,
                exchange=exchange,
                order_suffix=expected_suffix,
                reason=f"Suffix matches (expected {expected_ref}, got {payment_ref})"
            )
        
        return ReferenceMatchResult(
            matched=False,
            reference_found=payment_ref,
            expected_reference=expected_ref,
            exchange=exchange,
            order_suffix=expected_suffix,
            reason=f"Reference mismatch: expected {expected_ref}, got {payment_ref}"
        )
    
    def find_order_by_reference(
        self,
        reference: str,
        orders: list[UnifiedOrder],
        exchange: str = "binance"
    ) -> UnifiedOrder | None:
        """
        Find an order by its reference suffix.
        
        Args:
            reference: Reference from payment (e.g., "BI123456")
            orders: List of orders to search
            exchange: Exchange name
            
        Returns:
            Matching order or None
        """
        _, suffix = parse_reference(reference)
        if not suffix:
            return None
        
        for order in orders:
            order_digits = re.sub(r'\D', '', order.id)
            if order_digits.endswith(suffix):
                return order
        
        return None
    
    def _extract_payment_reference(self, payment: UnifiedPayment) -> str | None:
        """Extract reference from payment fields."""
        # Check reference field
        if hasattr(payment, 'reference') and payment.reference:
            ref = extract_reference(payment.reference)
            if ref:
                return ref
        
        # Check raw data for reference/memo fields
        if hasattr(payment, 'raw') and payment.raw:
            for field in ['reference', 'memo', 'description', 'remittanceInfo', 'message']:
                value = payment.raw.get(field)
                if value:
                    ref = extract_reference(str(value))
                    if ref:
                        return ref
        
        return None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def match_reference(
    order: UnifiedOrder,
    payment: UnifiedPayment,
    exchange: str = "binance"
) -> ReferenceMatchResult:
    """Quick helper to match payment reference to order."""
    matcher = ReferenceMatcher()
    return matcher.match(order, payment, exchange)
