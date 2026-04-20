"""
2026 P2P PnL CALCULATOR
========================
Pulls ALL completed BUY + SELL orders from Binance P2P for 2026,
then calculates spread-based PnL.

PnL formula (per-order):
  BUY:  rate = EUR_paid / USDT_received  (cost)
  SELL: rate = EUR_received / USDT_sold  (revenue)

  Spread PnL = Σ(sell EUR) - Σ(buy EUR) for matched USDT volume

Run:  python scripts/pnl_2026.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.exchanges.binance.api_client import BinanceApiClient


async def fetch_all_orders(client, trade_type, start_ts):
    """Fetch all pages of order history."""
    all_orders = []
    page = 1
    while True:
        orders = await client.get_order_history(
            trade_type=trade_type,
            start_timestamp=start_ts,
            page=page,
            rows=50,
        )
        if not orders:
            break
        all_orders.extend(orders)
        if len(orders) < 50:
            break
        page += 1
        await asyncio.sleep(0.2)  # Rate limit
    return all_orders


async def main():
    binance_key = os.getenv("BINANCE_API_KEY")
    binance_secret = os.getenv("BINANCE_API_SECRET")
    if not binance_key or not binance_secret:
        print("ERROR: BINANCE_API_KEY / BINANCE_API_SECRET not set")
        sys.exit(1)

    client = BinanceApiClient(api_key=binance_key, api_secret=binance_secret)

    # 2026 start = Jan 1 00:00 UTC
    start_2026 = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

    print(f"\n{'='*75}")
    print(f"  P2P PnL REPORT - 2026 (Jan 1 - Feb 15)")
    print(f"{'='*75}\n")

    # ── Fetch all orders ───────────────────────────────────────────────────
    print("Fetching BUY orders...")
    buys = await fetch_all_orders(client, "BUY", start_2026)
    print(f"  -> {len(buys)} total BUY orders")

    print("Fetching SELL orders...")
    sells = await fetch_all_orders(client, "SELL", start_2026)
    print(f"  -> {len(sells)} total SELL orders\n")

    # Filter to completed only
    completed_buys = [o for o in buys if o.status and o.status.value == "completed"]
    completed_sells = [o for o in sells if o.status and o.status.value == "completed"]

    print(f"Completed BUYs:  {len(completed_buys)}")
    print(f"Completed SELLs: {len(completed_sells)}\n")

    # ── BUY analysis ──────────────────────────────────────────────────────
    total_buy_eur = 0.0
    total_buy_usdt = 0.0
    buy_by_currency = defaultdict(lambda: {"eur": 0.0, "usdt": 0.0, "count": 0})

    print(f"{'─'*75}")
    print(f"  COMPLETED BUY ORDERS (we pay fiat, receive USDT)")
    print(f"{'─'*75}")
    print(f"  {'Date':<14} {'ID':>10} {'Fiat Amt':>12} {'Cur':<5} {'USDT':>12} {'Rate':>8}")
    print(f"  {'-'*14} {'-'*10} {'-'*12} {'-'*5} {'-'*12} {'-'*8}")

    for o in sorted(completed_buys, key=lambda x: x.created_at or datetime.min):
        fiat = float(o.fiat_amount or 0)
        usdt = float(o.crypto_amount or 0)
        cur = o.fiat_currency.value if o.fiat_currency else "?"
        rate = fiat / usdt if usdt > 0 else 0
        created = o.created_at.strftime("%m/%d %H:%M") if o.created_at else "?"
        ext_id = o.external_id[-8:] if o.external_id else "?"

        print(f"  {created:<14} {ext_id:>10} {fiat:>12,.2f} {cur:<5} {usdt:>12,.2f} {rate:>8.4f}")

        total_buy_eur += fiat
        total_buy_usdt += usdt
        buy_by_currency[cur]["eur"] += fiat
        buy_by_currency[cur]["usdt"] += usdt
        buy_by_currency[cur]["count"] += 1

    avg_buy_rate = total_buy_eur / total_buy_usdt if total_buy_usdt > 0 else 0
    print(f"\n  TOTAL BUY:  {total_buy_eur:>12,.2f} fiat  |  {total_buy_usdt:>12,.2f} USDT  |  Avg rate: {avg_buy_rate:.4f}")
    for cur, d in sorted(buy_by_currency.items()):
        r = d["eur"] / d["usdt"] if d["usdt"] > 0 else 0
        print(f"    {cur}: {d['count']} orders  |  {d['eur']:>12,.2f}  |  {d['usdt']:>12,.2f} USDT  |  Avg: {r:.4f}")

    # ── SELL analysis ─────────────────────────────────────────────────────
    total_sell_eur = 0.0
    total_sell_usdt = 0.0
    sell_by_currency = defaultdict(lambda: {"eur": 0.0, "usdt": 0.0, "count": 0})

    print(f"\n{'─'*75}")
    print(f"  COMPLETED SELL ORDERS (we sell USDT, receive fiat)")
    print(f"{'─'*75}")
    print(f"  {'Date':<14} {'ID':>10} {'Fiat Amt':>12} {'Cur':<5} {'USDT':>12} {'Rate':>8}")
    print(f"  {'-'*14} {'-'*10} {'-'*12} {'-'*5} {'-'*12} {'-'*8}")

    for o in sorted(completed_sells, key=lambda x: x.created_at or datetime.min):
        fiat = float(o.fiat_amount or 0)
        usdt = float(o.crypto_amount or 0)
        cur = o.fiat_currency.value if o.fiat_currency else "?"
        rate = fiat / usdt if usdt > 0 else 0
        created = o.created_at.strftime("%m/%d %H:%M") if o.created_at else "?"
        ext_id = o.external_id[-8:] if o.external_id else "?"

        print(f"  {created:<14} {ext_id:>10} {fiat:>12,.2f} {cur:<5} {usdt:>12,.2f} {rate:>8.4f}")

        total_sell_eur += fiat
        total_sell_usdt += usdt
        sell_by_currency[cur]["eur"] += fiat
        sell_by_currency[cur]["usdt"] += usdt
        sell_by_currency[cur]["count"] += 1

    avg_sell_rate = total_sell_eur / total_sell_usdt if total_sell_usdt > 0 else 0
    print(f"\n  TOTAL SELL: {total_sell_eur:>12,.2f} fiat  |  {total_sell_usdt:>12,.2f} USDT  |  Avg rate: {avg_sell_rate:.4f}")
    for cur, d in sorted(sell_by_currency.items()):
        r = d["eur"] / d["usdt"] if d["usdt"] > 0 else 0
        print(f"    {cur}: {d['count']} orders  |  {d['eur']:>12,.2f}  |  {d['usdt']:>12,.2f} USDT  |  Avg: {r:.4f}")

    # ── PnL CALCULATION ───────────────────────────────────────────────────
    # EUR-only PnL (clean spread)
    eur_buy = buy_by_currency.get("EUR", {"eur": 0, "usdt": 0, "count": 0})
    eur_sell = sell_by_currency.get("EUR", {"eur": 0, "usdt": 0, "count": 0})
    
    eur_buy_rate = eur_buy["eur"] / eur_buy["usdt"] if eur_buy["usdt"] > 0 else 0
    eur_sell_rate = eur_sell["eur"] / eur_sell["usdt"] if eur_sell["usdt"] > 0 else 0
    eur_matched = min(eur_buy["usdt"], eur_sell["usdt"])
    eur_spread = eur_sell_rate - eur_buy_rate
    eur_pnl = eur_spread * eur_matched

    # COP PnL (need EUR equivalent - use EUR rate as proxy)
    cop_buy = buy_by_currency.get("COP", {"eur": 0, "usdt": 0, "count": 0})
    cop_sell = sell_by_currency.get("COP", {"eur": 0, "usdt": 0, "count": 0})
    cop_matched = min(cop_buy["usdt"], cop_sell["usdt"])
    # For COP, margin is in COP — convert using approximate COP/EUR rate
    cop_buy_rate = cop_buy["eur"] / cop_buy["usdt"] if cop_buy["usdt"] > 0 else 0
    cop_sell_rate = cop_sell["eur"] / cop_sell["usdt"] if cop_sell["usdt"] > 0 else 0
    cop_spread_cop = cop_sell_rate - cop_buy_rate
    cop_pnl_cop = cop_spread_cop * cop_matched
    # Convert COP PnL to EUR (approximate: 1 EUR ~ 4500 COP)
    cop_eur_rate = 4500
    cop_pnl_eur = cop_pnl_cop / cop_eur_rate if cop_buy["count"] > 0 else 0

    print(f"\n{'='*75}")
    print(f"  P&L SUMMARY - 2026")
    print(f"{'='*75}")
    
    print(f"\n  --- EUR P2P ---")
    print(f"  Buy orders:  {eur_buy['count']}  |  {eur_buy['eur']:>12,.2f} EUR  |  {eur_buy['usdt']:>12,.2f} USDT  |  Avg buy rate:  {eur_buy_rate:.4f}")
    print(f"  Sell orders: {eur_sell['count']}  |  {eur_sell['eur']:>12,.2f} EUR  |  {eur_sell['usdt']:>12,.2f} USDT  |  Avg sell rate: {eur_sell_rate:.4f}")
    print(f"  Matched vol: {eur_matched:>12,.2f} USDT")
    print(f"  Spread:      {eur_spread:.4f} EUR/USDT")
    print(f"  EUR PnL:     {eur_pnl:>12,.2f} EUR")

    if cop_buy["count"] > 0 or cop_sell["count"] > 0:
        print(f"\n  --- COP P2P ---")
        print(f"  Buy orders:  {cop_buy['count']}  |  {cop_buy['eur']:>12,.0f} COP  |  {cop_buy['usdt']:>12,.2f} USDT  |  Avg buy rate:  {cop_buy_rate:,.0f}")
        print(f"  Sell orders: {cop_sell['count']}  |  {cop_sell['eur']:>12,.0f} COP  |  {cop_sell['usdt']:>12,.2f} USDT  |  Avg sell rate: {cop_sell_rate:,.0f}")
        print(f"  Matched vol: {cop_matched:>12,.2f} USDT")
        print(f"  Spread:      {cop_spread_cop:,.0f} COP/USDT")
        print(f"  COP PnL:     {cop_pnl_cop:>12,.0f} COP  (~{cop_pnl_eur:,.2f} EUR)")

    total_pnl_eur = eur_pnl + cop_pnl_eur
    print(f"\n  ================================")
    print(f"  TOTAL P&L:   {total_pnl_eur:>12,.2f} EUR")
    print(f"  ================================\n")

    # ── USDT inventory position ───────────────────────────────────────────
    net_usdt = total_buy_usdt - total_sell_usdt
    print(f"  Net USDT position: {net_usdt:>+,.2f} USDT ({'surplus' if net_usdt > 0 else 'deficit'})")
    print(f"  (buy {total_buy_usdt:,.2f} - sell {total_sell_usdt:,.2f})\n")

    await client.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
