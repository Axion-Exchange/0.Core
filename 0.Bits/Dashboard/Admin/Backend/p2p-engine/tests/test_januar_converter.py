"""
Test Januar Converter Translator.
Run: python3 test_januar_converter.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_converter():
    """Test Januar crypto conversion API."""
    from src.banks.januar.converter_translator import JanuarConverterTranslator
    
    # Load credentials
    api_key = os.getenv("JANUAR_API_KEY")
    api_secret = os.getenv("JANUAR_API_SECRET")
    base_url = os.getenv("JANUAR_BASE_URL", "https://api.test.januar.com")
    
    if not api_key or not api_secret:
        print("⚠ Missing JANUAR_API_KEY or JANUAR_API_SECRET in .env")
        return
    
    print("\n🔄 Januar Converter Test\n")
    print("=" * 60)
    
    converter = JanuarConverterTranslator(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url
    )
    
    # Step 1: Setup (fetch wallet/account IDs)
    print("\n📋 Step 1: Fetching wallet and account IDs...")
    try:
        await converter.setup()
        print(f"   Wallet ID: {converter.wallet_id}")
        print(f"   Account ID: {converter.account_id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   (Wallet/account may not exist in sandbox)")
    
    # Step 2: Get conversion details
    print("\n📊 Step 2: Checking conversion service status...")
    try:
        details = await converter.get_conversion_details()
        print(f"   Service Available: {details.get('serviceAvailable', 'unknown')}")
        
        assets = details.get("assets", [])
        if assets:
            print(f"   Available Assets: {[a.get('name') for a in assets[:5]]}")
        
        pairs = details.get("exchangePairs", [])
        if pairs:
            print(f"   Exchange Pairs: {len(pairs)} available")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 3: Get quote (initiate without confirm)
    print("\n💱 Step 3: Getting EUR -> USDC quote...")
    try:
        quote = await converter.get_conversion_rate(
            from_asset="EUR",
            to_asset="USDC",
            amount="100.00"
        )
        print(f"   Quote ID: {quote.get('quote_id', 'N/A')}")
        print(f"   Rate: {quote.get('rate', 'N/A')}")
        print(f"   From: {quote.get('from_amount', 'N/A')} EUR")
        print(f"   To: {quote.get('to_amount', 'N/A')} USDC")
        print(f"   Fee: {quote.get('fee', 'N/A')}")
        print(f"   Status: {quote.get('status', 'N/A')}")
        
        if quote.get("error"):
            print(f"   ⚠ Note: {quote.get('error')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 4: Get conversion history
    print("\n📜 Step 4: Fetching conversion history...")
    try:
        history = await converter.get_conversion_history(limit=5)
        print(f"   Found {len(history)} conversions")
        for conv in history[:3]:
            print(f"   - {conv.get('id', 'N/A')[:8]}... | {conv.get('fromAmount')} -> {conv.get('toAmount')} | {conv.get('status')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Januar Converter test complete!\n")


if __name__ == "__main__":
    asyncio.run(test_converter())
