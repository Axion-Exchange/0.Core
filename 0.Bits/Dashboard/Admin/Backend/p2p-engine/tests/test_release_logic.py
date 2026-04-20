"""
Test combined release logic (Name + Amount must both pass).
Run: python3 test_release_logic.py
"""

from decimal import Decimal
from src.logic.payment_matcher import PaymentMatcher, ReleaseVerdict


# Mock classes
class MockOrder:
    def __init__(self, fiat_amount: str, fiat_currency: str, buyer_name: str):
        self.id = "order_123"
        self.fiat_amount = fiat_amount
        self.fiat_currency = fiat_currency
        self.buyer_name = buyer_name
        self.raw = {"buyerRealName": buyer_name}


class MockPayment:
    def __init__(self, amount: str, currency: str, sender_name: str):
        self.id = "payment_456"
        self.amount = amount
        self.currency = currency
        self.sender_name = sender_name
        self.raw = {"counterparty": {"name": sender_name}}


def test_both_match():
    """Both name and amount match -> RELEASE OK."""
    matcher = PaymentMatcher()
    
    order = MockOrder("100.00", "EUR", "John Smith")
    payment = MockPayment("100.00", "EUR", "John Smith")
    
    verdict = matcher.verify_release(order, payment)
    
    assert verdict.can_release, f"Should release: {verdict.summary}"
    assert verdict.name_ok
    assert verdict.amount_ok
    print("✓ Both match -> RELEASE OK")


def test_name_only_match():
    """Name matches but amount underpaid -> BLOCKED."""
    matcher = PaymentMatcher()
    
    order = MockOrder("100.00", "EUR", "John Smith")
    payment = MockPayment("50.00", "EUR", "John Smith")  # Underpaid!
    
    verdict = matcher.verify_release(order, payment)
    
    assert not verdict.can_release, f"Should block: {verdict.summary}"
    assert verdict.name_ok  # Name is fine
    assert not verdict.amount_ok  # Amount failed
    print("✓ Name OK, Amount FAIL -> BLOCKED")


def test_amount_only_match():
    """Amount matches but name doesn't -> BLOCKED."""
    matcher = PaymentMatcher()
    
    order = MockOrder("100.00", "EUR", "John Smith")
    payment = MockPayment("100.00", "EUR", "Jane Doe")  # Wrong name!
    
    verdict = matcher.verify_release(order, payment)
    
    assert not verdict.can_release, f"Should block: {verdict.summary}"
    assert not verdict.name_ok  # Name failed
    # Amount may still be OK but release should be blocked
    print("✓ Name FAIL, Amount OK -> BLOCKED")


def test_neither_match():
    """Neither name nor amount match -> BLOCKED."""
    matcher = PaymentMatcher()
    
    order = MockOrder("100.00", "EUR", "John Smith")
    payment = MockPayment("50.00", "EUR", "Jane Doe")
    
    verdict = matcher.verify_release(order, payment)
    
    assert not verdict.can_release
    assert not verdict.name_ok
    assert not verdict.amount_ok
    print("✓ Neither match -> BLOCKED")


def test_fuzzy_name_exact_amount():
    """Fuzzy name match + exact amount -> RELEASE OK."""
    matcher = PaymentMatcher()
    
    order = MockOrder("100.00", "EUR", "Jon Smith")  # 1-letter typo
    payment = MockPayment("100.00", "EUR", "John Smith")
    
    verdict = matcher.verify_release(order, payment)
    
    assert verdict.can_release, f"Should release with fuzzy name: {verdict.summary}"
    print("✓ Fuzzy name + Exact amount -> RELEASE OK")


def test_summary_output():
    """Test human-readable summary."""
    matcher = PaymentMatcher()
    
    order = MockOrder("100.00", "EUR", "John Smith")
    payment = MockPayment("100.00", "EUR", "John Smith")
    
    verdict = matcher.verify_release(order, payment)
    
    print("\n📋 Sample Summary Output:")
    print(verdict.summary)
    print("")
    

def run_all_tests():
    print("\n🧪 Running Release Logic Tests...\n")
    
    test_both_match()
    test_name_only_match()
    test_amount_only_match()
    test_neither_match()
    test_fuzzy_name_exact_amount()
    test_summary_output()
    
    print("✅ All Release Logic tests passed!\n")


if __name__ == "__main__":
    run_all_tests()
