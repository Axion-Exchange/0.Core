"""
Integration test: Wire Name Matcher to compare Januar payments with Binance orders.

This test:
1. Fetches pending orders from Binance
2. Fetches incoming payments from Januar
3. Uses PaymentMatcher to find matches by name
4. Reports matches and confidence levels

Run: python3 test_payment_matching.py
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from src.exchanges.binance.api_translator import BinanceApiTranslator
from src.banks.januar.payment_translator import JanuarPaymentTranslator
from src.logic.payment_matcher import PaymentMatcher
from src.core.types import UnifiedOrder, UnifiedPayment, OrderStatus, BankProvider, PaymentDirection, PaymentStatus


async def test_payment_matching():
    print("\n🔗 Payment Matching Integration Test\n")
    print("=" * 60)
    
    # Initialize translators
    binance = BinanceApiTranslator(
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET")
    )
    
    januar = JanuarPaymentTranslator(
        api_key=os.getenv("JANUAR_API_KEY"),
        api_secret=os.getenv("JANUAR_API_SECRET"),
        base_url=os.getenv("JANUAR_BASE_URL")
    )
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    matcher = PaymentMatcher(gemini_api_key=gemini_key)
    
    # Step 1: Get pending Binance orders
    print("\n📋 Step 1: Fetching Binance P2P Orders...")
    try:
        # Use correct parameter names: trade_type and status (int)
        # status: 1=pending, 2=paid
        all_orders = await binance.get_orders(
            trade_type="SELL",  # We're selling crypto, buyer pays us
            status=1,  # Pending orders
            rows=50
        )
        
        # Also get paid orders
        paid_orders = await binance.get_orders(
            trade_type="SELL",
            status=2,  # Paid orders
            rows=50
        )
        
        pending_orders = all_orders + paid_orders
        
        print(f"   Pending: {len(all_orders)}, Paid: {len(paid_orders)}")
        print(f"   Total to match: {len(pending_orders)}")
        
        for order in pending_orders[:5]:  # Show first 5
            buyer = order.raw.get('buyerRealName', 'Unknown') if order.raw else 'Unknown'
            print(f"   - {order.id}: {order.fiat_amount} {order.fiat_currency} | Buyer: {buyer}")
            
    except Exception as e:
        print(f"   ❌ Failed to fetch Binance orders: {e}")
        pending_orders = []
    
    # Step 2: Get Januar incoming payments
    print("\n💶 Step 2: Fetching Januar Incoming Payments...")
    try:
        # First get the account ID
        accounts = await januar._request("GET", "/accounts")
        if accounts.get("data"):
            januar.account_id = accounts["data"][0]["id"]
        
        # Fetch PAYIN transactions - only EUR
        txns = await januar._request(
            "GET",
            f"/accounts/{januar.account_id}/transactions",
            {"pageSize": 50, "types": "PAYIN", "currencies": "EUR"}
        )
        
        # Convert to UnifiedPayment format (EUR only)
        incoming_payments = []
        for tx in txns.get("data", []):
            # Filter EUR only (skip DKK etc)
            if tx.get("currency") != "EUR":
                continue
                
            payment = UnifiedPayment(
                id=tx["id"],
                external_id=tx["id"],
                provider=BankProvider.JANUAR,
                direction=PaymentDirection.INCOMING,
                status=PaymentStatus.COMPLETED if tx.get("status") == "COMPLETED" else PaymentStatus.PENDING,
                amount=tx["amount"].replace("-", ""),  # Remove negative sign
                currency="EUR",
                sender_name=tx.get("counterparty", {}).get("name"),
                sender_account=tx.get("counterparty", {}).get("accountNumber"),
                payment_method="SEPA",
                created_at=datetime.fromisoformat(tx.get("initiatedTime", "2024-01-01T00:00:00Z").replace("Z", "+00:00")),
                raw=tx
            )
            incoming_payments.append(payment)
        
        print(f"   Total EUR PAYINs: {len(incoming_payments)}")
        for p in incoming_payments[:5]:
            sender = p.sender_name or "Unknown"
            print(f"   - {p.id[:8]}...: {p.amount} {p.currency} | Sender: {sender}")
            
    except Exception as e:
        print(f"   ❌ Failed to fetch Januar payments: {e}")
        incoming_payments = []
    
    # Step 3: Match payments to orders
    print("\n🔍 Step 3: Matching Payments to Orders...")
    if not pending_orders:
        print("   ⚠ No pending orders to match")
    elif not incoming_payments:
        print("   ⚠ No incoming payments to match")
    else:
        matches = matcher.find_matches(pending_orders, incoming_payments)
        
        if matches:
            print(f"\n✅ Found {len(matches)} matches:")
            for m in matches:
                print(f"\n   📎 Match:")
                print(f"      Order: {m.order.id}")
                print(f"      Payment: {m.payment.id}")
                print(f"      Confidence: {m.match_result.confidence:.0%}")
                print(f"      Method: {m.match_result.method}")
                print(f"      Auto-release OK: {'✓' if m.is_confident else '✗'}")
        else:
            print("   ⚠ No matches found")
    
    print("\n" + "=" * 60)
    print("✅ Integration test complete!\n")


if __name__ == "__main__":
    asyncio.run(test_payment_matching())
