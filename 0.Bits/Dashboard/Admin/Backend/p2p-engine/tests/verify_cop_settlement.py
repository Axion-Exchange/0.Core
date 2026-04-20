"""Verify COP-only settlement change."""
import sys

with open(r'C:\Users\Woek\Documents\PearV1\src\fiat\cop\facilitapay_client.py', encoding='utf-8') as f:
    source = f.read()

errors = []

# 1. SETTLEMENT_CURRENCY is COP
if 'SETTLEMENT_CURRENCY = "COP"' not in source:
    errors.append('FAIL: SETTLEMENT_CURRENCY not set to COP')
else:
    print('PASS: SETTLEMENT_CURRENCY = "COP"')

# 2. No value_usd references remain
lines = source.split('\n')
usd_refs = [(i+1, line.strip()) for i, line in enumerate(lines) if 'value_usd' in line]
if usd_refs:
    for ln, content in usd_refs:
        errors.append(f'FAIL: value_usd at line {ln}: {content}')
else:
    print('PASS: No value_usd references remain')

# 3. max_payout_cop exists
if 'max_payout_cop' not in source:
    errors.append('FAIL: max_payout_cop missing')
else:
    print('PASS: max_payout_cop parameter exists')

# 4. No max_payout_usd references remain  
if 'max_payout_usd' in source:
    errors.append('FAIL: max_payout_usd still present')
else:
    print('PASS: No max_payout_usd references')

# 5. Payout exchange_currency uses SETTLEMENT_CURRENCY
if 'exchange_currency="COP"' in source.replace(' ', ''):
    errors.append('FAIL: Hardcoded exchange_currency="COP" in payout persistence')
else:
    print('PASS: Payout uses self.SETTLEMENT_CURRENCY for exchange_currency')

if errors:
    print('\nERRORS:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
else:
    print('\nALL COP SETTLEMENT CHECKS PASSED')
