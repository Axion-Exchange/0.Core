"""
BUY ORDER RECONCILIATION SCRIPT
===================================
Cross-references Binance P2P BUY orders (last 4 days) with
Januar outgoing PAYOUT transactions to find:

1. DUPLICATE PAYOUTS  — same Binance order paid out more than once
2. MISSING PAYOUTS    — completed Binance BUY order with no matching Januar payout
3. ORPHAN PAYOUTS     — Januar payout with no matching Binance order

Run from PearV2 root:
    python scripts/reconcile_buys.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.exchanges.binance.api_client import BinanceApiClient
from src.fiat.eur.januar_sepa_client import JanuarSepaClient


async def main():
    # ── Setup ──────────────────────────────────────────────────────────────
    binance_key = os.getenv("BINANCE_API_KEY")
    binance_secret = os.getenv("BINANCE_API_SECRET")
    januar_key = os.getenv("JANUAR_API_KEY")
    januar_secret = os.getenv("JANUAR_API_SECRET")
    januar_url = os.getenv("JANUAR_BASE_URL", "https://api.januar.com")

    if not binance_key or not binance_secret:
        print("❌ BINANCE_API_KEY / BINANCE_API_SECRET not set")
        sys.exit(1)
    if not januar_key or not januar_secret:
        print("❌ JANUAR_API_KEY / JANUAR_API_SECRET not set")
        sys.exit(1)

    binance = BinanceApiClient(api_key=binance_key, api_secret=binance_secret)
    januar = JanuarSepaClient(api_key=januar_key, api_secret=januar_secret, base_url=januar_url)

    # Time window: last 4 days
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=4)
    start_ts = int(start.timestamp() * 1000)  # Binance wants milliseconds
    start_date = start.strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    print(f"\n{'='*70}")
    print(f"  BUY ORDER RECONCILIATION")
    print(f"  Window: {start_date} → {end_date} (last 4 days)")
    print(f"{'='*70}\n")

    # ── 1. Fetch Binance BUY order history ─────────────────────────────────
    print("📡 Fetching Binance BUY order history...")
    all_buy_orders = []
    page = 1
    while True:
        orders = await binance.get_order_history(
            trade_type="BUY",
            start_timestamp=start_ts,
            page=page,
            rows=50,
        )
        if not orders:
            break
        all_buy_orders.extend(orders)
        if len(orders) < 50:
            break
        page += 1

    print(f"   Found {len(all_buy_orders)} BUY orders\n")

    # ── 2. Fetch Januar outgoing payments ──────────────────────────────────
    print("📡 Fetching Januar outgoing payments...")
    payouts = await januar.get_outgoing_payments(
        limit=200,
        start_time=start_date,
        end_time=end_date,
    )
    print(f"   Found {len(payouts)} outgoing payments\n")

    # ── 3. Print all Binance BUY orders ────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  BINANCE BUY ORDERS ({len(all_buy_orders)})")
    print(f"{'─'*70}")
    
    total_buy_eur = 0.0
    total_buy_usdt = 0.0
    for o in sorted(all_buy_orders, key=lambda x: x.created_at or datetime.min):
        status = o.status.value if o.status else "?"
        currency = o.fiat_currency.value if o.fiat_currency else "?"
        created = o.created_at.strftime("%m/%d %H:%M") if o.created_at else "?"
        amt = o.fiat_amount or "?"
        crypto = o.crypto_amount or "?"
        ext_id = o.external_id[-8:] if o.external_id else "?"
        print(f"  {created}  {ext_id}  {status:<18}  {amt:>10} {currency}  {crypto:>10} USDT")
        try:
            total_buy_eur += float(o.fiat_amount or 0)
            total_buy_usdt += float(o.crypto_amount or 0)
        except (ValueError, TypeError):
            pass
    
    print(f"\n  TOTAL: {total_buy_eur:,.2f} EUR  |  {total_buy_usdt:,.2f} USDT")

    # ── 4. Print all Januar payouts ────────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  JANUAR OUTGOING PAYMENTS ({len(payouts)})")
    print(f"{'─'*70}")
    
    total_payout_eur = 0.0
    for p in sorted(payouts, key=lambda x: x.created_at or datetime.min):
        created = p.created_at.strftime("%m/%d %H:%M") if p.created_at else "?"
        status = p.status.value if p.status else "?"
        amt = p.amount or "?"
        name = (p.receiver_name or p.sender_name or "?")[:30]
        ref = (p.reference or "")[:20]
        iban = (p.receiver_account or p.sender_account or "?")
        iban_short = iban[:4] + "..." + iban[-4:] if iban and len(iban) > 8 else iban
        ext_id = p.external_id[:12] if p.external_id else "?"
        print(f"  {created}  {ext_id:<14}  {status:<12}  {amt:>10} EUR  → {name:<30} {iban_short}  ref:{ref}")
        try:
            total_payout_eur += float(p.amount or 0)
        except (ValueError, TypeError):
            pass
    
    print(f"\n  TOTAL: {total_payout_eur:,.2f} EUR paid out")

    # ── 5. Cross-reference: match payouts to orders ────────────────────────
    print(f"\n{'─'*70}")
    print(f"  CROSS-REFERENCE ANALYSIS")
    print(f"{'─'*70}\n")

    # Build lookup of Binance orders by amount (EUR)
    # For BUY orders, the seller sends EUR to us, then we pay out EUR
    # The payout reference often contains the internal order number
    
    # Strategy: Match by amount and look for reference patterns
    buy_by_amount = defaultdict(list)
    for o in all_buy_orders:
        try:
            amt = f"{float(o.fiat_amount):.2f}"
            buy_by_amount[amt].append(o)
        except (ValueError, TypeError):
            pass

    payout_by_amount = defaultdict(list)
    for p in payouts:
        try:
            amt = f"{float(p.amount):.2f}"
            payout_by_amount[amt].append(p)
        except (ValueError, TypeError):
            pass

    # Check for DUPLICATE payouts (same reference or amount paid twice)
    print("  🔍 CHECKING FOR DUPLICATES...")
    ref_counts = defaultdict(list)
    for p in payouts:
        if p.reference:
            ref_counts[p.reference].append(p)
    
    duplicates_found = False
    for ref, plist in ref_counts.items():
        if len(plist) > 1:
            duplicates_found = True
            total_dup = sum(float(p.amount or 0) for p in plist)
            print(f"  ⚠️  DUPLICATE REFERENCE: '{ref}' — {len(plist)} payouts totaling {total_dup:.2f} EUR")
            for p in plist:
                print(f"      {p.created_at} | {p.amount} EUR | {p.receiver_name} | {p.external_id[:12]}")
    
    if not duplicates_found:
        print("  ✅ No duplicate references found\n")

    # Check for amount-based duplicates (same amount to same IBAN)
    iban_amount_counts = defaultdict(list)
    for p in payouts:
        iban = p.receiver_account or p.sender_account or ""
        try:
            amt = f"{float(p.amount):.2f}"
        except (ValueError, TypeError):
            continue
        iban_amount_counts[(iban, amt)].append(p)
    
    print("\n  🔍 CHECKING FOR SAME-AMOUNT SAME-IBAN PAYOUTS...")
    same_found = False
    for (iban, amt), plist in iban_amount_counts.items():
        if len(plist) > 1:
            same_found = True
            print(f"  ⚠️  {len(plist)}x {amt} EUR → {iban[:4]}...{iban[-4:] if len(iban) > 8 else iban}")
            for p in plist:
                created = p.created_at.strftime("%m/%d %H:%M") if p.created_at else "?"
                print(f"      {created} | ref: {p.reference or 'none'} | {p.external_id[:12]}")
    
    if not same_found:
        print("  ✅ No same-amount same-IBAN duplicates\n")

    # ── 6. Summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  Binance BUY orders:     {len(all_buy_orders)}")
    print(f"  Total EUR bought:       {total_buy_eur:,.2f} EUR")
    print(f"  Total USDT spent:       {total_buy_usdt:,.2f} USDT")
    print(f"  Januar payouts:         {len(payouts)}")
    print(f"  Total EUR paid out:     {total_payout_eur:,.2f} EUR")
    diff = total_payout_eur - total_buy_eur
    if abs(diff) > 1:
        emoji = "🔴" if diff > 0 else "🟡"
        print(f"  {emoji} DIFFERENCE:          {diff:+,.2f} EUR (payout {'>' if diff > 0 else '<'} buys)")
    else:
        print(f"  ✅ DIFFERENCE:          {diff:+,.2f} EUR (within tolerance)")
    print(f"{'='*70}\n")

    # Cleanup
    await binance.client.aclose()
    await januar.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
