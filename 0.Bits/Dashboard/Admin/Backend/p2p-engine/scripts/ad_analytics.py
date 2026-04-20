"""
MARKET-WIDE AD ANALYTICS — Binance P2P
========================================
Scans the ENTIRE Binance P2P marketplace across multiple fiat currencies
and shows which pairs have the most ads, plus 30-day completed order counts.

Usage:
    python -m scripts.ad_analytics

Output:
    1. Total ad count per fiat (BUY + SELL)
    2. Detailed breakdown per fiat/side
    3. Your completed orders (30-day) per fiat
"""

import asyncio
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.exchanges.binance.api_client import BinanceApiClient


# Fiat currencies to scan on Binance P2P
FIATS_TO_SCAN = [
    "EUR", "GBP", "USD", "COP", "BRL", "TRY", "ARS", "MXN",
    "NGN", "KES", "GHS", "ZAR", "INR", "PKR", "BDT", "VND",
    "IDR", "MYR", "PHP", "THB", "UAH", "RUB", "PLN", "RON",
    "CZK", "HUF", "SEK", "NOK", "DKK", "CHF", "AED", "SAR",
    "EGP", "MAD", "PEN", "CLP", "UYU", "DOP", "VES", "BOB",
]

ASSETS = ["USDT", "USDC", "BTC", "ETH", "BNB"]


def fmt(val) -> str:
    try:
        return f"{float(val):,.2f}"
    except (ValueError, TypeError):
        return str(val) if val else "-"


async def count_all_ads_for_pair(client, trade_type: str, asset: str, fiat: str) -> int:
    """Count all pages of ads for a given pair. Returns total count."""
    total = 0
    page = 1
    while True:
        try:
            batch = await client.search_market_ads(
                trade_type=trade_type, asset=asset, fiat=fiat,
                page=page, rows=20,
            )
        except Exception:
            break
        total += len(batch)
        if len(batch) < 20:
            break
        page += 1
        # Safety cap — don't hammer the API beyond 10 pages (200 ads)
        if page > 10:
            break
    return total


async def main():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("ERROR: BINANCE_API_KEY / BINANCE_API_SECRET not set in .env")
        sys.exit(1)

    client = BinanceApiClient(api_key, api_secret)

    # ─── 1. Scan ALL fiat currencies for USDT ads ────────────────────
    print("\n>> Scanning Binance P2P marketplace (USDT pairs)...")
    print("   This will take a minute — scanning", len(FIATS_TO_SCAN), "fiats x 2 sides...\n")

    results: dict[str, dict] = {}

    for i, fiat in enumerate(FIATS_TO_SCAN):
        buy_count = await count_all_ads_for_pair(client, "BUY", "USDT", fiat)
        sell_count = await count_all_ads_for_pair(client, "SELL", "USDT", fiat)

        if buy_count > 0 or sell_count > 0:
            results[fiat] = {
                "buy": buy_count,
                "sell": sell_count,
                "total": buy_count + sell_count,
            }

        progress = f"[{i+1}/{len(FIATS_TO_SCAN)}]"
        if buy_count > 0 or sell_count > 0:
            print(f"  {progress} {fiat}: {buy_count} BUY ads, {sell_count} SELL ads")
        else:
            print(f"  {progress} {fiat}: no ads")

        # Small delay to avoid rate limits
        await asyncio.sleep(0.3)

    # ─── 2. Summary table — sorted by total ads ─────────────────────
    print(f"\n{'='*70}")
    print(f" BINANCE P2P MARKETPLACE — USDT ADS BY FIAT (ALL TRADERS)")
    print(f"{'='*70}")
    print(f"{'Rank':<6} {'Fiat':<8} {'Total Ads':<12} {'BUY Ads':<12} {'SELL Ads':<12}")
    print(f"{'─'*6} {'─'*8} {'─'*12} {'─'*12} {'─'*12}")

    sorted_fiats = sorted(results, key=lambda f: results[f]["total"], reverse=True)
    for rank, fiat in enumerate(sorted_fiats, 1):
        r = results[fiat]
        print(f"{rank:<6} {fiat:<8} {r['total']:<12} {r['buy']:<12} {r['sell']:<12}")

    grand_total = sum(r["total"] for r in results.values())
    print(f"{'─'*70}")
    print(f"{'':6} {'TOTAL':<8} {grand_total:<12}")

    # ─── 3. Your completed orders (30 days) per fiat ─────────────────
    print(f"\n>> Fetching YOUR 30-day order history...")
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    start_ts = int(thirty_days_ago.timestamp() * 1000)
    end_ts = int(now.timestamp() * 1000)

    all_orders = []
    for trade_type in ["BUY", "SELL"]:
        page = 1
        while True:
            batch = await client.get_order_history(
                trade_type=trade_type,
                start_timestamp=start_ts,
                end_timestamp=end_ts,
                page=page,
                rows=100,
            )
            if not batch:
                break
            all_orders.extend(batch)
            if len(batch) < 100:
                break
            page += 1

    from src.core.types import OrderStatus
    completed = [o for o in all_orders if o.status in (
        OrderStatus.COMPLETED, "completed", "5"
    )]

    fiat_stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0, "buy": 0, "sell": 0,
        "buy_vol": 0.0, "sell_vol": 0.0, "total_vol": 0.0,
    })

    for o in completed:
        fiat = o.fiat_currency.value
        s = fiat_stats[fiat]
        s["count"] += 1
        vol = float(o.fiat_amount)
        s["total_vol"] += vol
        if o.side.value.upper() == "BUY":
            s["buy"] += 1
            s["buy_vol"] += vol
        else:
            s["sell"] += 1
            s["sell_vol"] += vol

    print(f"\n{'='*90}")
    print(f" YOUR COMPLETED ORDERS — PAST 30 DAYS ({len(completed)} total)")
    print(f"{'='*90}")
    print(f"{'Fiat':<8} {'Orders':<9} {'BUY':<8} {'SELL':<8} {'BUY Vol':<16} {'SELL Vol':<16} {'Total Vol':<16}")
    print(f"{'─'*8} {'─'*9} {'─'*8} {'─'*8} {'─'*16} {'─'*16} {'─'*16}")

    for fiat in sorted(fiat_stats, key=lambda f: fiat_stats[f]["count"], reverse=True):
        s = fiat_stats[fiat]
        print(
            f"{fiat:<8} {s['count']:<9} {s['buy']:<8} {s['sell']:<8} "
            f"{fmt(s['buy_vol']):<16} {fmt(s['sell_vol']):<16} {fmt(s['total_vol']):<16}"
        )

    total_orders = sum(s["count"] for s in fiat_stats.values())
    total_buy = sum(s["buy"] for s in fiat_stats.values())
    total_sell = sum(s["sell"] for s in fiat_stats.values())
    print(f"{'─'*90}")
    print(f"{'TOTAL':<8} {total_orders:<9} {total_buy:<8} {total_sell:<8}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
