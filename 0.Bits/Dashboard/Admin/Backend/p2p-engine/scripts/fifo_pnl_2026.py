"""
FIFO P&L CALCULATOR - 2026
============================
Matches every SELL against the oldest available BUY lots (First-In, First-Out).

Buy-side sources (cost basis / inventory):
  1. Binance P2P BUY orders  → we pay EUR, receive USDT at rate X
  2. Januar EUR→USDC conversions → we convert EUR to USDC at rate Y

Sell-side (revenue):
  1. Binance P2P SELL orders → we sell USDT, receive EUR at rate Z

FIFO: each sell eats through the oldest buy lots first.
Realized PnL per match = (sell_rate - buy_rate) × matched_qty

Run:  python scripts/fifo_pnl_2026.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.exchanges.binance.api_client import BinanceApiClient
from src.fiat.eur.januar_sepa_client import JanuarSepaClient


@dataclass
class Lot:
    """A buy lot in the FIFO queue."""
    source: str        # "P2P BUY" or "Januar"
    date: datetime
    qty: float         # USDT quantity
    rate: float        # EUR per USDT (cost)
    remaining: float = 0.0  # remaining qty not yet matched
    ref: str = ""

    def __post_init__(self):
        self.remaining = self.qty


@dataclass
class FifoMatch:
    """A single FIFO match between a sell and a buy lot."""
    sell_date: datetime
    sell_id: str
    buy_source: str
    buy_date: datetime
    qty: float
    buy_rate: float
    sell_rate: float

    @property
    def pnl(self) -> float:
        return (self.sell_rate - self.buy_rate) * self.qty


async def fetch_all_orders(client, trade_type, start_ts):
    """Paginate through all Binance P2P order history."""
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
        await asyncio.sleep(0.2)
    return all_orders


async def main():
    binance_key = os.getenv("BINANCE_API_KEY")
    binance_secret = os.getenv("BINANCE_API_SECRET")
    januar_key = os.getenv("JANUAR_API_KEY")
    januar_secret = os.getenv("JANUAR_API_SECRET")
    januar_url = os.getenv("JANUAR_BASE_URL", "https://api.januar.com")

    if not all([binance_key, binance_secret, januar_key, januar_secret]):
        print("ERROR: Missing BINANCE or JANUAR API credentials")
        sys.exit(1)

    binance = BinanceApiClient(api_key=binance_key, api_secret=binance_secret)
    januar = JanuarSepaClient(api_key=januar_key, api_secret=januar_secret, base_url=januar_url)

    start_2026 = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    start_date = "2026-01-01"
    end_date = "2026-02-15"

    print(f"\n{'='*80}")
    print(f"  FIFO P&L REPORT - 2026")
    print(f"{'='*80}\n")

    # ── 1. Fetch data from both sources ────────────────────────────────────
    print("Fetching Binance P2P BUY orders...")
    p2p_buys = await fetch_all_orders(binance, "BUY", start_2026)
    completed_buys = [o for o in p2p_buys if o.status and o.status.value == "completed"]
    print(f"  -> {len(completed_buys)} completed BUY orders")

    print("Fetching Binance P2P SELL orders...")
    p2p_sells = await fetch_all_orders(binance, "SELL", start_2026)
    completed_sells = [o for o in p2p_sells if o.status and o.status.value == "completed"]
    print(f"  -> {len(completed_sells)} completed SELL orders")

    print("Fetching Januar outgoing payments (EUR payouts = our buy cost)...")
    januar_outgoing = await januar.get_outgoing_payments(
        limit=200,
        start_time=start_date,
        end_time=end_date,
    )
    print(f"  -> {len(januar_outgoing)} outgoing payments")

    print("Fetching Januar incoming payments (EUR received from P2P sellers)...")
    januar_incoming = await januar.get_incoming_payments(
        limit=200,
        start_time=start_date,
        end_time=end_date,
    )
    print(f"  -> {len(januar_incoming)} incoming payments\n")

    # ── 2. Build FIFO buy-lot queue ────────────────────────────────────────
    lots: list[Lot] = []

    # Source 1: P2P BUY orders (we pay EUR -> get USDT)
    # When we BUY on Binance P2P, we pay EUR and receive USDT
    # The rate = fiat_amount / crypto_amount = EUR per USDT
    for o in completed_buys:
        try:
            fiat = float(o.fiat_amount)
            usdt = float(o.crypto_amount)
            if o.fiat_currency and o.fiat_currency.value != "EUR":
                continue  # Only EUR buys for EUR FIFO
            if usdt <= 0:
                continue
            rate = fiat / usdt
            lots.append(Lot(
                source="P2P BUY",
                date=o.created_at or datetime.min,
                qty=usdt,
                rate=rate,
                ref=o.external_id[-8:] if o.external_id else "",
            ))
        except (ValueError, TypeError):
            continue

    # Source 2: Januar EUR->USDC conversions
    # These show up as outgoing payments to "Januar ApS" with ref containing "Conversion"
    # The amount is EUR spent, and we receive equivalent USDC (approximately 1:1 with EUR/USD rate)
    # We also need to check incoming USDC — for now, estimate from conversion payments
    eur_usd_rate = 1.05  # Approximate EUR/USD for 2026 so far
    for p in januar_outgoing:
        ref = (p.reference or "").lower()
        name = (p.receiver_name or "").lower()
        if "conversion" in ref or "januar" in name:
            try:
                eur_spent = abs(float(p.amount))
                if eur_spent < 10:
                    continue
                # EUR -> USDC: we spend EUR, get USDC at roughly EUR/USD rate
                # USDC ~= USDT, so cost per USDT = eur_spent / (eur_spent * eur_usd_rate)
                usdt_received = eur_spent * eur_usd_rate  # approximate
                rate = eur_spent / usdt_received  # = 1/eur_usd_rate ~ 0.952
                lots.append(Lot(
                    source="Januar Conv",
                    date=p.created_at or datetime.min,
                    qty=usdt_received,
                    rate=rate,
                    ref=p.reference[:20] if p.reference else "",
                ))
            except (ValueError, TypeError):
                continue

    # Sort lots by date (FIFO = oldest first)
    lots.sort(key=lambda x: x.date)

    total_inventory = sum(l.qty for l in lots)
    print(f"{'='*80}")
    print(f"  INVENTORY (BUY LOTS) - {len(lots)} lots, {total_inventory:,.2f} USDT total")
    print(f"{'='*80}")
    print(f"  {'Date':<14} {'Source':<14} {'Qty':>10} {'Rate':>8} {'Ref':<12}")
    print(f"  {'-'*14} {'-'*14} {'-'*10} {'-'*8} {'-'*12}")
    for lot in lots:
        d = lot.date.strftime("%m/%d %H:%M") if lot.date != datetime.min else "?"
        print(f"  {d:<14} {lot.source:<14} {lot.qty:>10,.2f} {lot.rate:>8.4f} {lot.ref:<12}")

    # ── 3. Build sell list ─────────────────────────────────────────────────
    sells_list = []
    for o in completed_sells:
        try:
            fiat = float(o.fiat_amount)
            usdt = float(o.crypto_amount)
            if o.fiat_currency and o.fiat_currency.value != "EUR":
                continue
            if usdt <= 0:
                continue
            rate = fiat / usdt
            sells_list.append({
                "date": o.created_at or datetime.min,
                "usdt": usdt,
                "eur": fiat,
                "rate": rate,
                "id": o.external_id[-8:] if o.external_id else "",
            })
        except (ValueError, TypeError):
            continue

    sells_list.sort(key=lambda x: x["date"])

    total_sell_usdt = sum(s["usdt"] for s in sells_list)
    total_sell_eur = sum(s["eur"] for s in sells_list)
    print(f"\n  Total sell volume: {total_sell_usdt:,.2f} USDT ({total_sell_eur:,.2f} EUR)")
    print(f"  Total buy inventory: {total_inventory:,.2f} USDT")
    if total_sell_usdt > total_inventory:
        print(f"  ** Sells exceed known inventory by {total_sell_usdt - total_inventory:,.2f} USDT")
        print(f"     (unmatched sells will use estimated rate from last known lot)\n")

    # ── 4. FIFO matching ──────────────────────────────────────────────────
    matches: list[FifoMatch] = []
    lot_idx = 0
    unmatched_sell_usdt = 0.0
    unmatched_sell_eur = 0.0

    for sell in sells_list:
        remaining = sell["usdt"]

        while remaining > 0.001 and lot_idx < len(lots):
            lot = lots[lot_idx]
            if lot.remaining <= 0.001:
                lot_idx += 1
                continue

            take = min(remaining, lot.remaining)
            matches.append(FifoMatch(
                sell_date=sell["date"],
                sell_id=sell["id"],
                buy_source=lot.source,
                buy_date=lot.date,
                qty=take,
                buy_rate=lot.rate,
                sell_rate=sell["rate"],
            ))
            lot.remaining -= take
            remaining -= take

            if lot.remaining <= 0.001:
                lot_idx += 1

        if remaining > 0.001:
            # No more buy lots — unmatched sell
            unmatched_sell_usdt += remaining
            unmatched_sell_eur += remaining * sell["rate"]

    # ── 5. Results ─────────────────────────────────────────────────────────
    matched_usdt = sum(m.qty for m in matches)
    total_pnl = sum(m.pnl for m in matches)
    total_cost = sum(m.buy_rate * m.qty for m in matches)
    total_revenue = sum(m.sell_rate * m.qty for m in matches)

    # Breakdown by source
    from collections import defaultdict
    source_stats = defaultdict(lambda: {"qty": 0.0, "cost": 0.0, "revenue": 0.0, "pnl": 0.0})
    for m in matches:
        s = source_stats[m.buy_source]
        s["qty"] += m.qty
        s["cost"] += m.buy_rate * m.qty
        s["revenue"] += m.sell_rate * m.qty
        s["pnl"] += m.pnl

    # Monthly breakdown
    monthly = defaultdict(lambda: {"qty": 0.0, "pnl": 0.0, "cost": 0.0, "revenue": 0.0})
    for m in matches:
        month_key = m.sell_date.strftime("%Y-%m") if m.sell_date != datetime.min else "unknown"
        monthly[month_key]["qty"] += m.qty
        monthly[month_key]["pnl"] += m.pnl
        monthly[month_key]["cost"] += m.buy_rate * m.qty
        monthly[month_key]["revenue"] += m.sell_rate * m.qty

    print(f"\n{'='*80}")
    print(f"  FIFO P&L RESULTS - 2026")
    print(f"{'='*80}")

    print(f"\n  Matched Volume:     {matched_usdt:>12,.2f} USDT")
    print(f"  Total Cost Basis:   {total_cost:>12,.2f} EUR")
    print(f"  Total Revenue:      {total_revenue:>12,.2f} EUR")
    print(f"  ─────────────────────────────────────")
    print(f"  REALIZED P&L:       {total_pnl:>12,.2f} EUR")
    if matched_usdt > 0:
        print(f"  Avg margin/USDT:    {total_pnl/matched_usdt:>12.4f} EUR")
        print(f"  Margin %:           {(total_pnl/total_cost)*100:>11.2f}%")

    print(f"\n  --- By Buy Source ---")
    for src, stats in sorted(source_stats.items()):
        avg_buy = stats["cost"] / stats["qty"] if stats["qty"] > 0 else 0
        avg_sell = stats["revenue"] / stats["qty"] if stats["qty"] > 0 else 0
        print(f"  {src:<14}  {stats['qty']:>10,.2f} USDT  |  buy@{avg_buy:.4f}  sell@{avg_sell:.4f}  |  PnL: {stats['pnl']:>+10,.2f} EUR")

    print(f"\n  --- By Month ---")
    for month, stats in sorted(monthly.items()):
        avg_margin = stats["pnl"] / stats["qty"] if stats["qty"] > 0 else 0
        print(f"  {month}  {stats['qty']:>10,.2f} USDT  |  Cost: {stats['cost']:>10,.2f}  Rev: {stats['revenue']:>10,.2f}  |  PnL: {stats['pnl']:>+10,.2f} EUR  ({avg_margin:+.4f}/USDT)")

    if unmatched_sell_usdt > 0.001:
        print(f"\n  --- Unmatched Sells (no known buy lot) ---")
        print(f"  {unmatched_sell_usdt:>12,.2f} USDT sold with no matching buy lot in our data")
        print(f"  Revenue from unmatched: {unmatched_sell_eur:>12,.2f} EUR")
        # Estimate PnL assuming a typical Januar cost of ~0.952 EUR/USDT
        est_cost = unmatched_sell_usdt * 0.952
        est_pnl = unmatched_sell_eur - est_cost
        print(f"  Estimated cost @0.952: {est_cost:>12,.2f} EUR")
        print(f"  Estimated PnL:         {est_pnl:>+12,.2f} EUR")
        print(f"\n  ================================")
        print(f"  TOTAL REALIZED:      {total_pnl:>+12,.2f} EUR  (matched)")
        print(f"  ESTIMATED UNMATCHED: {est_pnl:>+12,.2f} EUR")
        print(f"  COMBINED ESTIMATE:   {total_pnl + est_pnl:>+12,.2f} EUR")
        print(f"  ================================")
    else:
        print(f"\n  ================================")
        print(f"  TOTAL REALIZED P&L:  {total_pnl:>+12,.2f} EUR")
        print(f"  ================================")

    # Remaining inventory
    remaining_lots = [l for l in lots if l.remaining > 0.001]
    remaining_usdt = sum(l.remaining for l in remaining_lots)
    if remaining_usdt > 0.001:
        remaining_cost = sum(l.remaining * l.rate for l in remaining_lots)
        avg_remaining = remaining_cost / remaining_usdt
        print(f"\n  Unsold inventory: {remaining_usdt:>10,.2f} USDT (avg cost: {avg_remaining:.4f} EUR/USDT)")

    print()
    await binance.client.aclose()
    await januar.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
