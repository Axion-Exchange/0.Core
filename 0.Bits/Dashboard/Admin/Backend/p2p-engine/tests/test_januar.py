"""
Test Januar API connectivity and basic operations.
Run: python3 test_januar.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from src.banks.januar.payment_translator import JanuarPaymentTranslator


async def test_januar():
    print("\n🏦 Testing Januar API (Sandbox)...\n")
    
    api_key = os.getenv("JANUAR_API_KEY")
    api_secret = os.getenv("JANUAR_API_SECRET")
    base_url = os.getenv("JANUAR_BASE_URL")
    
    if not api_key or not api_secret:
        print("❌ Missing JANUAR_API_KEY or JANUAR_API_SECRET in .env")
        return
    
    print(f"📍 Base URL: {base_url}")
    print(f"🔑 API Key: {api_key[:8]}...")
    
    translator = JanuarPaymentTranslator(api_key, api_secret, base_url)
    
    # Test 1: Get accounts
    print("\n--- Test 1: List Accounts ---")
    try:
        accounts = await translator._request("GET", "/accounts")
        print(f"✅ Got {len(accounts.get('data', []))} accounts")
        
        if accounts.get("data"):
            account = accounts["data"][0]
            translator.account_id = account["id"]
            print(f"   Account ID: {account['id']}")
            print(f"   Name: {account.get('name', 'N/A')}")
            print(f"   Balances: {account.get('balances', {})}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return
    
    # Test 2: Get transactions (incoming payments)
    print("\n--- Test 2: List Transactions ---")
    try:
        if translator.account_id:
            txns = await translator._request(
                "GET", 
                f"/accounts/{translator.account_id}/transactions",
                {"pageSize": 5, "types": "PAYIN"}
            )
            data = txns.get("data", [])
            print(f"✅ Got {len(data)} transactions")
            for tx in data[:3]:
                counterparty = tx.get("counterparty", {})
                print(f"   - {tx.get('type')}: {tx.get('amount')} {tx.get('currency')} from {counterparty.get('name', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n✅ Januar API test complete!\n")


if __name__ == "__main__":
    asyncio.run(test_januar())
