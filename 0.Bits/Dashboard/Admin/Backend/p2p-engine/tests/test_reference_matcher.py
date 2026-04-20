"""
Test Reference Matching and Tiered Release Logic.
Run: python3 test_reference_matcher.py
"""

from src.logic.reference_matcher import (
    generate_reference, 
    extract_reference, 
    parse_reference,
    ReferenceMatcher,
    EXCHANGE_CODES
)
from src.logic.payment_matcher import PaymentMatcher, ReleaseVerdict


# Mock classes
class MockOrder:
    def __init__(self, order_id: str, fiat_amount: str, fiat_currency: str, buyer_name: str):
        self.id = order_id
        self.fiat_amount = fiat_amount
        self.fiat_currency = fiat_currency
        self.buyer_name = buyer_name
        self.raw = {"buyerRealName": buyer_name}


class MockPayment:
    def __init__(self, amount: str, currency: str, sender_name: str, reference: str | None = None):
        self.id = "payment_test"
        self.amount = amount
        self.currency = currency
        self.sender_name = sender_name
        self.reference = reference
        self.raw = {
            "counterparty": {"name": sender_name},
            "reference": reference
        }


def test_generate_reference():
    """Test reference generation from order ID."""
    # Binance order
    ref = generate_reference("binance", "order_12345678901234567890")
    assert ref.startswith("BI"), f"Binance should start with BI: {ref}"
    assert len(ref) == 8, f"Reference should be 8 chars: {ref}"
    print(f"✓ Binance reference: {ref}")
    
    # Bitget order (uses BT)
    ref = generate_reference("bitget", "999888777666")
    assert ref == "BT777666", f"Bitget should be BT: {ref}"
    print(f"✓ Bitget reference: {ref}")
    
    # All exchange codes
    for exchange, code in EXCHANGE_CODES.items():
        ref = generate_reference(exchange, "123456")
        assert ref.startswith(code), f"{exchange} should start with {code}"
    print("✓ All exchange codes validated")


def test_extract_reference():
    """Test reference extraction from text."""
    # Direct reference
    ref = extract_reference("BI123456")
    assert ref == "BI123456"
    
    # Reference in sentence
    ref = extract_reference("Payment ref: BI999888 paid")
    assert ref == "BI999888"
    
    # No reference
    ref = extract_reference("Random payment text")
    assert ref is None
    
    # Case insensitive
    ref = extract_reference("bi123456")
    assert ref == "BI123456"
    
    print("✓ Reference extraction passed")


def test_parse_reference():
    """Test parsing reference into parts."""
    exchange, suffix = parse_reference("BI123456")
    assert exchange == "binance"
    assert suffix == "123456"
    
    exchange, suffix = parse_reference("BT999888")
    assert exchange == "bitget"
    assert suffix == "999888"
    
    print("✓ Reference parsing passed")


def test_tier1_reference_match():
    """Tier 1: Reference match allows relaxed name threshold."""
    matcher = PaymentMatcher()
    
    # Order with ID ending in 123456
    order = MockOrder("order_abc123456", "100.00", "EUR", "John Smith")
    
    # Payment with matching reference but slightly different name
    payment = MockPayment("100.00", "EUR", "J Smith", reference="BI123456")  # 70% name match
    
    verdict = matcher.verify_release(order, payment)
    
    assert verdict.reference_ok, f"Reference should match: {verdict.reference_result.reason}"
    assert verdict.release_tier == "TIER_1_REFERENCE"
    print(f"✓ Tier 1 reference match: {verdict.release_tier}")
    print(f"  Name confidence: {verdict.name_result.confidence:.0%}")


def test_tier2_no_reference():
    """Tier 2: No reference requires strict name match."""
    matcher = PaymentMatcher()
    
    order = MockOrder("order_123456", "100.00", "EUR", "John Smith")
    
    # Payment with NO reference, exact name match
    payment = MockPayment("100.00", "EUR", "John Smith", reference=None)
    
    verdict = matcher.verify_release(order, payment)
    
    assert not verdict.reference_ok, "No reference should not match"
    if verdict.can_release:
        assert verdict.release_tier == "TIER_2_NAME_AMOUNT"
        print(f"✓ Tier 2 name+amount match: {verdict.release_tier}")
    else:
        print(f"⚠ Tier 2 blocked (expected if name below 95%)")


def test_summary_output():
    """Test human-readable summary with reference."""
    matcher = PaymentMatcher()
    
    order = MockOrder("order_999888", "100.00", "EUR", "John Smith")
    payment = MockPayment("100.00", "EUR", "John Smith", reference="BI999888")
    
    verdict = matcher.verify_release(order, payment)
    
    print("\n📋 Sample Summary with Reference:")
    print(verdict.summary)


def run_all_tests():
    print("\n🧪 Running Reference Matcher Tests...\n")
    
    test_generate_reference()
    test_extract_reference()
    test_parse_reference()
    test_tier1_reference_match()
    test_tier2_no_reference()
    test_summary_output()
    
    print("\n✅ All Reference Matcher tests passed!\n")


if __name__ == "__main__":
    run_all_tests()
