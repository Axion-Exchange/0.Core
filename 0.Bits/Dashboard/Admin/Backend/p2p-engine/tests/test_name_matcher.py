"""
Test script for Name Matcher.
Run: python test_name_matcher.py
"""

from src.logic.name_matcher import NameMatcher, create_name_matcher


def test_exact_match():
    """Test exact name matches."""
    matcher = NameMatcher()
    
    # Exact match
    result = matcher.match("Adam Goldman", "Adam Goldman", "pay_001")
    assert result.matched, f"Exact match should pass: {result.details}"
    assert result.confidence == 1.0
    print("✓ Exact match passed")


def test_order_independent():
    """Test that word order doesn't matter."""
    matcher = NameMatcher()
    
    # Different order - should match
    result = matcher.match("Adam Bart Goldman", "Goldman Adam Bart", "pay_002")
    assert result.matched, f"Order-independent match should pass: {result.details}"
    print("✓ Order-independent match passed")
    
    # Different order with 4 names
    result = matcher.match("Adam Bart Matthew Goldman", "Matthew Goldman Adam Bart", "pay_003")
    assert result.matched, f"4-name order-independent match should pass: {result.details}"
    print("✓ 4-name order-independent match passed")


def test_spelling_tolerance():
    """Test 1-letter spelling tolerance."""
    matcher = NameMatcher()
    
    # One letter off
    result = matcher.match("Adam Goldman", "Adm Goldman", "pay_004")  # 'a' missing
    assert result.matched, f"1-letter tolerance should pass: {result.details}"
    print("✓ 1-letter tolerance passed")
    
    # One letter substitution
    result = matcher.match("Adam Goldman", "Adem Goldman", "pay_005")  # 'a' -> 'e'
    assert result.matched, f"1-letter substitution should pass: {result.details}"
    print("✓ 1-letter substitution passed")
    
    # Two letters off in SAME word - should FAIL  
    result = matcher.match("Adam Goldman", "Adm Goldm", "pay_006")  # 2 letters wrong in one word
    assert not result.matched, f"2-letter tolerance on single word should fail: {result.details}"
    print("✓ 2-letter tolerance correctly rejected")


def test_missing_name():
    """Test that missing names cause failure."""
    matcher = NameMatcher()
    
    # Missing one name - should fail
    result = matcher.match("Adam Bart Goldman", "Adam Goldman", "pay_007")
    assert not result.matched, f"Missing name should fail: {result.details}"
    print("✓ Missing name correctly rejected")


def test_extra_names_in_payment():
    """Test that extra names in payment are OK."""
    matcher = NameMatcher()
    
    # Payment has more names than Binance - should match
    result = matcher.match("Adam Goldman", "Adam Bart Goldman", "pay_008")
    assert result.matched, f"Extra names in payment should pass: {result.details}"
    print("✓ Extra names in payment passed")


def test_case_insensitive():
    """Test case insensitivity."""
    matcher = NameMatcher()
    
    result = matcher.match("ADAM GOLDMAN", "adam goldman", "pay_009")
    assert result.matched, f"Case insensitive should pass: {result.details}"
    print("✓ Case insensitive match passed")


def test_caching():
    """Test that Gemini results are cached."""
    matcher = NameMatcher()
    
    # Manually cache a result
    from src.logic.name_matcher import MatchResult
    fake_result = MatchResult(
        matched=True,
        confidence=0.97,
        method="gemini",
        binance_name="Test Name",
        payment_name="Test Payment",
        details="Cached test"
    )
    matcher.cache.cache_result("pay_cache_001", "Test Name", fake_result)
    
    # Should return cached result
    result = matcher.match("Test Name", "Different Name", "pay_cache_001")
    assert result.cached, "Should return cached result"
    assert result.method == "gemini"
    print("✓ Cache retrieval passed")


def run_all_tests():
    print("\n🧪 Running Name Matcher Tests...\n")
    
    test_exact_match()
    test_order_independent()
    test_spelling_tolerance()
    test_missing_name()
    test_extra_names_in_payment()
    test_case_insensitive()
    test_caching()
    
    print("\n✅ All Name Matcher tests passed!\n")


if __name__ == "__main__":
    run_all_tests()
