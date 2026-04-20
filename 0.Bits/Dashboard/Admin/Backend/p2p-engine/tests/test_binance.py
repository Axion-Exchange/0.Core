#!/usr/bin/env python3
"""
Quick test script for Binance P2P API connection.
Run: python test_binance.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

from src.exchanges.binance.api_translator import BinanceApiTranslator


async def main():
    # Get credentials
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    
    if not api_key or not api_secret:
        print("❌ Missing BINANCE_API_KEY or BINANCE_API_SECRET in .env")
        return
    
    print(f"🔑 Using API key: {api_key[:8]}...{api_key[-4:]}")
    
    # Initialize translator
    translator = BinanceApiTranslator(api_key, api_secret)
    
    # Test 1: Check connectivity
    print("\n1. Testing connectivity...")
    try:
        ready = await translator.is_ready()
        if ready:
            print("   ✅ Connected to Binance API")
        else:
            print("   ❌ Connection failed")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Get balances
    print("\n2. Fetching balances...")
    try:
        balances = await translator.get_balances()
        if balances:
            print(f"   ✅ Found {len(balances)} balances with value:")
            for b in balances[:5]:
                print(f"      {b.asset}: {b.available} available")
        else:
            print("   ⚠️ No balances with value found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get P2P orders
    print("\n3. Fetching P2P orders...")
    try:
        orders = await translator.get_orders(page=1, rows=5)
        if orders:
            print(f"   ✅ Found {len(orders)} orders:")
            for o in orders:
                print(f"      {o.side.value} {o.crypto_amount} {o.crypto_asset.value} @ {o.price} - {o.status.value}")
        else:
            print("   ⚠️ No orders found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get ads
    print("\n4. Fetching P2P ads...")
    try:
        ads = await translator.get_ads(page=1, rows=5)
        if ads:
            print(f"   ✅ Found {len(ads)} ads:")
            for a in ads:
                status = "🟢" if a.active else "🔴"
                print(f"      {status} {a.side.value} {a.crypto_asset.value}/{a.fiat_currency.value} @ {a.price}")
        else:
            print("   ⚠️ No ads found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
