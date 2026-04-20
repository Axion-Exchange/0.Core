"""
Test Januar SEPA Payout (Sandbox)
=================================
Sends 100 EUR test payout to verify integration works.

Run: python3 tests/test_januar_payout.py
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.banks.januar.payment_translator import JanuarPaymentTranslator


# Sandbox config
SANDBOX_URL = "https://api.test.januar.com"

# Test recipient (use a test IBAN for sandbox)
TEST_IBAN = "DE89370400440532013000"  # German test IBAN
TEST_NAME = "Test Recipient"
TEST_AMOUNT = "100.00"
TEST_REFERENCE = "BIN-12345678"  # Internal order number format


async def test_payout():
    print("\n" + "=" * 60)
    print("JANUAR SEPA PAYOUT TEST (SANDBOX)")
    print("=" * 60)
    
    api_key = os.getenv("JANUAR_API_KEY")
    api_secret = os.getenv("JANUAR_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ Missing JANUAR_API_KEY or JANUAR_API_SECRET in .env")
        return False
    
    print(f"\n📍 Base URL: {SANDBOX_URL}")
    print(f"🔑 API Key: {api_key[:8]}...")
    
    # Initialize translator with SANDBOX URL
    translator = JanuarPaymentTranslator(api_key, api_secret, SANDBOX_URL)
    
    # Step 1: Test connectivity
    print("\n--- Step 1: Test Connectivity ---")
    is_ready = await translator.is_ready()
    if is_ready:
        print("✅ API connected successfully")
    else:
        print("❌ API connection failed")
        return False
    
    # Step 2: Get accounts
    print("\n--- Step 2: Get Account Info ---")
    try:
        accounts = await translator._request("GET", "/accounts")
        account_list = accounts.get("data", [])
        
        if not account_list:
            print("❌ No accounts found")
            return False
        
        account = account_list[0]
        translator.account_id = account["id"]
        
        print(f"✅ Account: {account.get('name', 'N/A')}")
        print(f"   ID: {translator.account_id}")
        
        # Show balances
        balances = account.get("balances", account.get("currencies", {}))
        for currency, balance in balances.items():
            if isinstance(balance, dict):
                balance = balance.get("balance", "0")
            print(f"   {currency}: {balance}")
            
    except Exception as e:
        print(f"❌ Failed to get accounts: {e}")
        return False
    
    # Step 3: Initiate payout
    print("\n--- Step 3: Initiate Payout ---")
    print(f"   Amount: EUR {TEST_AMOUNT}")
    print(f"   To: {TEST_NAME}")
    print(f"   IBAN: {TEST_IBAN}")
    print(f"   Reference: {TEST_REFERENCE}")
    
    try:
        result = await translator.initiate_payout(
            amount=TEST_AMOUNT,
            currency="EUR",
            recipient_name=TEST_NAME,
            recipient_account=TEST_IBAN,
            payment_method="SEPA",
            reference=TEST_REFERENCE,
            internal_note="P2P Automation Test Payout",
            replay_id=f"test-payout-{TEST_REFERENCE}"  # Idempotency key
        )
        
        if result:
            print("\n✅ PAYOUT INITIATED SUCCESSFULLY!")
            print(f"   ID: {result.external_id}")
            print(f"   Status: {result.status.value}")
            print(f"   Amount: {result.currency.value} {result.amount}")
            print(f"   Reference: {result.reference}")
            return True
        else:
            print("❌ Payout failed - no result returned")
            return False
            
    except Exception as e:
        print(f"❌ Payout failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_payout()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Payout initiated successfully")
    else:
        print("❌ TEST FAILED")
    print("=" * 60 + "\n")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
