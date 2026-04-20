"""
Test Amount Matcher logic.
Run: python3 test_amount_matcher.py
"""

from decimal import Decimal
from src.logic.amount_matcher import AmountMatcher, verify_amount, AmountMatchResult

# Mock order and payment classes for testing
class MockOrder:
    def __init__(self, fiat_amount: str, fiat_currency: str):
        self.fiat_amount = fiat_amount
        self.fiat_currency = fiat_currency

class MockPayment:
    def __init__(self, amount: str, currency: str):
        self.amount = amount
        self.currency = currency


def test_exact_match():
    """Test exact amount match."""
    matcher = AmountMatcher()
    order = MockOrder("100.00", "EUR")
    payment = MockPayment("100.00", "EUR")
    
    result = matcher.match(order, payment)
    assert result.matched, f"Exact match should pass: {result.reason}"
    assert result.is_exact
    print("✓ Exact match passed")


def test_overpayment_acceptable():
    """Test small overpayment is accepted."""
    matcher = AmountMatcher()
    order = MockOrder("100.00", "EUR")
    payment = MockPayment("100.50", "EUR")
    
    result = matcher.match(order, payment)
    assert result.matched, f"Small overpayment should pass: {result.reason}"
    assert result.is_overpaid
    print("✓ Small overpayment accepted")


def test_overpayment_suspicious():
    """Test large overpayment is rejected."""
    matcher = AmountMatcher()
    order = MockOrder("100.00", "EUR")
    payment = MockPayment("105.00", "EUR")  # +5 EUR is suspicious
    
    result = matcher.match(order, payment)
    assert not result.matched, f"Large overpayment should fail: {result.reason}"
    print("✓ Large overpayment rejected")


def test_underpayment_tolerance():
    """Test tiny underpayment within tolerance."""
    matcher = AmountMatcher()
    order = MockOrder("100.00", "EUR")
    payment = MockPayment("99.99", "EUR")  # 0.01 short
    
    result = matcher.match(order, payment)
    assert result.matched, f"0.01 underpayment should be tolerated: {result.reason}"
    print("✓ Tiny underpayment tolerated")


def test_underpayment_rejected():
    """Test underpayment is rejected."""
    matcher = AmountMatcher()
    order = MockOrder("100.00", "EUR")
    payment = MockPayment("95.00", "EUR")  # 5 EUR short
    
    result = matcher.match(order, payment)
    assert not result.matched, f"Underpayment should fail: {result.reason}"
    assert result.is_underpaid
    print("✓ Underpayment rejected")


def test_currency_mismatch():
    """Test currency mismatch is rejected."""
    matcher = AmountMatcher()
    order = MockOrder("100.00", "EUR")
    payment = MockPayment("100.00", "USD")
    
    result = matcher.match(order, payment)
    assert not result.matched, f"Currency mismatch should fail: {result.reason}"
    assert "Currency mismatch" in result.reason
    print("✓ Currency mismatch rejected")


def test_currency_enum_handling():
    """Test handling of Currency.EUR enum format."""
    matcher = AmountMatcher()
    order = MockOrder("100.00", "Currency.EUR")
    payment = MockPayment("100.00", "EUR")
    
    result = matcher.match(order, payment)
    assert result.matched, f"Currency enum should be normalized: {result.reason}"
    print("✓ Currency enum handling passed")


def run_all_tests():
    print("\n🧪 Running Amount Matcher Tests...\n")
    
    test_exact_match()
    test_overpayment_acceptable()
    test_overpayment_suspicious()
    test_underpayment_tolerance()
    test_underpayment_rejected()
    test_currency_mismatch()
    test_currency_enum_handling()
    
    print("\n✅ All Amount Matcher tests passed!\n")


if __name__ == "__main__":
    run_all_tests()
