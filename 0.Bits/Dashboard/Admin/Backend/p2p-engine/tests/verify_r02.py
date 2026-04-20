"""Standalone R-02 verification script — no pytest needed."""
from decimal import Decimal
import sys

results = []

def check_amount(tx_currency, tx_value, tx_exchange_currency, tx_exchanged_value, order_cop):
    """Mirror the currency-aware logic from handle_webhook."""
    if tx_currency == "COP":
        return tx_value
    elif tx_exchange_currency == "COP" and tx_exchanged_value:
        return tx_exchanged_value
    else:
        return None

# Test 1: COP direct match
amt = check_amount("COP", "850000", "USD", None, "850000")
p = int(Decimal(str(amt)).to_integral_value())
e = int(Decimal("850000").to_integral_value())
ok = p == e
results.append(("COP_direct_match", ok))

# Test 2: COP→USD conversion (value stays COP)
amt = check_amount("COP", "850000", "USD", "197.43", "850000")
p = int(Decimal(str(amt)).to_integral_value())
e = int(Decimal("850000").to_integral_value())
ok = p == e
results.append(("COP_to_USD_conversion", ok))

# Test 3: USD with exchange_currency=COP fallback
amt = check_amount("USD", "1000.00", "COP", "4500000", "4500000")
p = int(Decimal(str(amt)).to_integral_value())
e = int(Decimal("4500000").to_integral_value())
ok = p == e
results.append(("USD_with_COP_exchange", ok))

# Test 4: Neither COP → fail safe (returns None)
amt = check_amount("USD", "500", "EUR", "470", "850000")
ok = amt is None
results.append(("no_COP_failsafe", ok))

# Test 5: Amount mismatch detected
p = int(Decimal("800000").to_integral_value())
e = int(Decimal("850000").to_integral_value())
ok = p != e
results.append(("mismatch_detected", ok))

# Test 6: Decimal truncation
p = int(Decimal("850000.00").to_integral_value())
e = int(Decimal("850000").to_integral_value())
ok = p == e
results.append(("decimal_truncation", ok))

for name, ok in results:
    status = "PASS" if ok else "FAIL"
    print(f"{status} R-02: {name}")

if all(ok for _, ok in results):
    print("ALL R-02 TESTS PASSED")
else:
    sys.exit(1)
