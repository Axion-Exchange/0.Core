"""
FIFO P&L Tracker
================
Tracks profit and loss using First-In-First-Out cost basis.
Syncs completed trades from Binance P2P order history API.

Usage:
    tracker = FifoPnLTracker()
    await tracker.sync_from_binance()       # Pull latest trades
    summary = tracker.get_summary("today")  # Get P&L summary
"""

import sqlite3
import logging
import asyncio
from collections import deque
from typing import Optional, List, Dict, Any

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

logger = logging.getLogger("pnl")


# =============================================================================
# TYPES
# =============================================================================

@dataclass
class Trade:
    """A completed P2P trade."""
    external_id: str
    side: str          # "buy" or "sell"
    crypto_amount: Decimal
    crypto_asset: str  # e.g. "USDT", "USDC"
    fiat_amount: Decimal
    fiat_currency: str # e.g. "EUR"
    price: Decimal     # fiat per crypto unit
    completed_at: datetime
    counterparty: str = ""
    exchange: str = "binance"


@dataclass
class BuyLot:
    """A FIFO inventory lot from a BUY trade."""
    qty: Decimal
    cost_per_unit: Decimal  # EUR per crypto unit
    date: datetime
    trade_id: str


@dataclass
class FifoMatch:
    """Result of matching a SELL to BUY lots."""
    sell_trade_id: str
    sell_qty: Decimal
    sell_revenue: Decimal
    cost_basis: Decimal
    realized_pnl: Decimal
    matched_at: datetime


@dataclass
class PnLSummary:
    """P&L summary for a period."""
    period: str
    period_start: datetime
    period_end: datetime

    buy_count: int = 0
    sell_count: int = 0
    buy_volume_eur: Decimal = Decimal("0")
    sell_volume_eur: Decimal = Decimal("0")
    buy_volume_crypto: Decimal = Decimal("0")
    sell_volume_crypto: Decimal = Decimal("0")

    realized_pnl: Decimal = Decimal("0")
    spread_pnl: Decimal = Decimal("0")
    institutional_pnl: Decimal = Decimal("0")
    avg_buy_price: Decimal = Decimal("0")
    avg_sell_price: Decimal = Decimal("0")
    avg_spread_pct: Decimal = Decimal("0")

    # Matched trade details
    matched_usdt: Decimal = Decimal("0")
    matched_revenue_eur: Decimal = Decimal("0")
    matched_cost_eur: Decimal = Decimal("0")

    # Inventory snapshot
    inventory_qty: Decimal = Decimal("0")
    inventory_avg_cost: Decimal = Decimal("0")


# =============================================================================
# FIFO P&L TRACKER
# =============================================================================

class FifoPnLTracker:
    """
    FIFO P&L engine with Binance sync.

    - Pulls completed orders from Binance P2P API
    - Stores in pnl.db (deduped by external_id)
    - Computes FIFO cost basis for sells
    - Provides date-range summaries
    """

    def __init__(self, db_path: str = "data/pnl.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._last_sync: Optional[datetime] = None
        self._sync_cooldown = 300  # 5 min cache

    def _init_db(self):
        """Create database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE NOT NULL,
                    side TEXT NOT NULL,
                    crypto_amount TEXT NOT NULL,
                    crypto_asset TEXT NOT NULL,
                    fiat_amount TEXT NOT NULL,
                    fiat_currency TEXT NOT NULL,
                    price TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    counterparty TEXT DEFAULT '',
                    exchange TEXT DEFAULT 'binance',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_completed
                ON trades(completed_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_side
                ON trades(side, completed_at)
            """)

    # ─── BINANCE SYNC ─────────────────────────────────────────────────────

    async def sync_from_binance(self, force: bool = False) -> int:
        """Pull completed orders from Binance and store in DB.
        Returns number of new trades inserted.
        """
        if not force and self._last_sync:
            elapsed = (datetime.now() - self._last_sync).total_seconds()
            if elapsed < self._sync_cooldown:
                return 0

        from src.core.registry import registry

        client = registry.get_exchange_api("binance")
        if not client:
            logger.warning("No Binance client available for PnL sync")
            return 0

        new_count = 0
        for trade_type in ["BUY", "SELL"]:
            page = 1
            while True:
                try:
                    orders = await client.get_order_history(
                        trade_type=trade_type,
                        page=page,
                        rows=50,
                    )
                except Exception as e:
                    logger.warning("Binance history fetch error (page %d): %s", page, e)
                    break

                if not orders:
                    break

                for order in orders:
                    # Only track genuinely completed orders
                    status = getattr(order, "status", None)
                    status_str = status.value if hasattr(status, "value") else str(status or "")
                    if status_str.upper() not in ("COMPLETED",):
                        continue
                    if self._upsert_trade(order):
                        new_count += 1

                if len(orders) < 50:
                    break
                page += 1

        self._last_sync = datetime.now()
        if new_count > 0:
            logger.info("PnL sync: %d new trades from Binance", new_count)
        return new_count

    def _upsert_trade(self, order) -> bool:
        """Insert a trade if not already in DB. Returns True if new."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO trades
                    (external_id, side, crypto_amount, crypto_asset,
                     fiat_amount, fiat_currency, price, completed_at,
                     counterparty, exchange)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order.external_id,
                    order.side.value if hasattr(order.side, 'value') else str(order.side),
                    str(order.crypto_amount or "0"),
                    order.crypto_asset.value if hasattr(order.crypto_asset, 'value') else str(order.crypto_asset or "USDT"),
                    str(order.fiat_amount or "0"),
                    order.fiat_currency.value if hasattr(order.fiat_currency, 'value') else str(order.fiat_currency or "EUR"),
                    str(order.price or "0"),
                    order.created_at.isoformat() if order.created_at else datetime.now().isoformat(),
                    order.counterparty.name if order.counterparty else "",
                    order.exchange.value if hasattr(order.exchange, 'value') else "binance",
                ))
                return conn.total_changes > 0
        except Exception as e:
            logger.debug("Trade upsert error: %s", e)
            return False

    # ─── TRADE RETRIEVAL ──────────────────────────────────────────────────

    def get_trades(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        side: Optional[str] = None,
    ) -> list[Trade]:
        """Get trades from DB with optional filters."""
        query = "SELECT * FROM trades WHERE 1=1"
        params: list = []

        if from_date:
            query += " AND completed_at >= ?"
            params.append(from_date.isoformat())
        if to_date:
            query += " AND completed_at <= ?"
            params.append(to_date.isoformat())
        if side:
            query += " AND side = ?"
            params.append(side)

        query += " ORDER BY completed_at ASC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_trade(r) for r in rows]

    def get_all_trades(self) -> list[Trade]:
        """Get ALL trades ordered by date."""
        return self.get_trades()

    def _row_to_trade(self, row) -> Trade:
        return Trade(
            external_id=row["external_id"],
            side=row["side"],
            crypto_amount=Decimal(row["crypto_amount"]),
            crypto_asset=row["crypto_asset"],
            fiat_amount=Decimal(row["fiat_amount"]),
            fiat_currency=row["fiat_currency"],
            price=Decimal(row["price"]),
            completed_at=datetime.fromisoformat(row["completed_at"]),
            counterparty=row["counterparty"] or "",
            exchange=row["exchange"] or "binance",
        )

    # ─── FIFO MATCHING ────────────────────────────────────────────────────

    def compute_fifo(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        currency: str = "EUR",
    ) -> PnLSummary:

        from src.services.unified_fifo_tracker import get_unified_fifo_summary
        
        try:
            # Route to True Unified Engine - from_date/to_date are already datetime objects
            return get_unified_fifo_summary(self.db_path, from_date, to_date)
        except Exception as _unified_err:
            import traceback as _tb
            _tb.print_exc()
            pass  # Fall back to old method

        """Compute P&L using Weighted Average Cost (WAC).

        Maintains a running average cost for USDT inventory.
        BUY: updates avg cost. SELL: profit = (sell_rate - avg_cost) * qty.
        """
        # Get trades for the period only
        period_trades = [
            t for t in self.get_trades(from_date=from_date, to_date=to_date)
            if t.fiat_currency.upper() == currency.upper()
        ]
        if not period_trades:
            now = datetime.now()
            return PnLSummary(
                period="empty",
                period_start=from_date or now,
                period_end=to_date or now,
            )

        # Inject institutional buys as synthetic BUY trades
        try:
            from src.services.institutional_tracker import get_institutional_tracker
            inst_tracker = get_institutional_tracker()
            inst_buys = inst_tracker.get_matched_buys(from_date=from_date, to_date=to_date)
            for ib in inst_buys:
                period_trades.append(Trade(
                    external_id=f"INST_{ib.id[:8]}",
                    side="buy",
                    crypto_amount=ib.usdt_amount,
                    crypto_asset="USDT",
                    fiat_amount=ib.eur_amount,
                    fiat_currency="EUR",
                    price=ib.eur_per_usdt,
                    completed_at=ib.created_at,
                    counterparty="Januar-Binance",
                    exchange="institutional",
                ))
            if inst_buys:
                # Re-sort to maintain FIFO chronological order
                period_trades.sort(key=lambda t: t.completed_at.replace(tzinfo=None) if t.completed_at.tzinfo else t.completed_at)
        except Exception as e:
            import logging
            logging.getLogger("pnl").debug("Institutional buy injection skipped: %s", e)

        # WAC: Weighted Average Cost engine
        inv_qty = Decimal("0")       # current inventory in USDT
        inv_avg_cost = Decimal("0")  # weighted avg EUR cost per USDT
        realized_pnl = Decimal("0")
        spread_pnl = Decimal("0")
        institutional_pnl = Decimal("0")
        total_matched_usdt = Decimal("0")
        total_matched_revenue = Decimal("0")
        total_matched_cost = Decimal("0")
        total_buy_count = 0
        total_sell_count = 0
        buy_volume_eur = Decimal("0")
        sell_volume_eur = Decimal("0")
        buy_volume_crypto = Decimal("0")
        sell_volume_crypto = Decimal("0")
        # Track institutional vs P2P inventory for split P&L
        inst_qty = Decimal("0")
        inst_cost_total = Decimal("0")

        for trade in period_trades:
            if trade.side == "buy":
                total_buy_count += 1
                buy_volume_eur += trade.fiat_amount
                buy_volume_crypto += trade.crypto_amount
                buy_rate = (trade.fiat_amount / trade.crypto_amount) if trade.crypto_amount > 0 else Decimal("0")

                # Update weighted average cost
                old_total_cost = inv_qty * inv_avg_cost
                new_total_cost = old_total_cost + trade.fiat_amount
                inv_qty += trade.crypto_amount
                inv_avg_cost = (new_total_cost / inv_qty) if inv_qty > 0 else Decimal("0")

                # Track institutional portion
                is_inst = trade.external_id.startswith("INST_")
                if is_inst:
                    inst_qty += trade.crypto_amount
                    inst_cost_total += trade.fiat_amount

            elif trade.side == "sell":
                total_sell_count += 1
                sell_volume_eur += trade.fiat_amount
                sell_volume_crypto += trade.crypto_amount
                sell_rate = (trade.fiat_amount / trade.crypto_amount) if trade.crypto_amount > 0 else Decimal("0")

                # P&L = (sell_rate - avg_cost) * qty_sold
                sell_qty = trade.crypto_amount
                cost_basis = inv_avg_cost * sell_qty
                revenue = trade.fiat_amount
                trade_pnl = revenue - cost_basis

                realized_pnl += trade_pnl
                total_matched_usdt += sell_qty
                total_matched_revenue += revenue
                total_matched_cost += cost_basis

                # Split P&L proportionally between institutional and spread
                if inv_qty > 0 and inst_qty > 0:
                    inst_ratio = inst_qty / inv_qty
                    institutional_pnl += trade_pnl * inst_ratio
                    spread_pnl += trade_pnl * (1 - inst_ratio)
                else:
                    spread_pnl += trade_pnl

                # Reduce inventory (avg cost stays the same for WAC)
                inv_qty = max(Decimal("0"), inv_qty - sell_qty)
                # Reduce institutional portion proportionally
                if inst_qty > 0 and sell_qty > 0:
                    inst_sold = min(inst_qty, sell_qty * (inst_qty / (inv_qty + sell_qty)) if (inv_qty + sell_qty) > 0 else Decimal("0"))
                    inst_qty = max(Decimal("0"), inst_qty - inst_sold)

        # Calculate averages
        avg_buy = (buy_volume_eur / buy_volume_crypto).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        ) if buy_volume_crypto > 0 else Decimal("0")

        avg_sell = (sell_volume_eur / sell_volume_crypto).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        ) if sell_volume_crypto > 0 else Decimal("0")

        spread = ((avg_sell - avg_buy) / avg_buy * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ) if avg_buy > 0 else Decimal("0")

        inv_cost = inv_avg_cost.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if inv_avg_cost > 0 else Decimal("0")
        now = datetime.now()
        return PnLSummary(
            period="custom",
            period_start=from_date or (period_trades[0].completed_at if period_trades else now),
            period_end=to_date or now,
            buy_count=total_buy_count,
            sell_count=total_sell_count,
            buy_volume_eur=buy_volume_eur,
            sell_volume_eur=sell_volume_eur,
            buy_volume_crypto=buy_volume_crypto,
            sell_volume_crypto=sell_volume_crypto,
            realized_pnl=realized_pnl,
            spread_pnl=spread_pnl,
            institutional_pnl=institutional_pnl,
            matched_usdt=total_matched_usdt,
            matched_revenue_eur=total_matched_revenue,
            matched_cost_eur=total_matched_cost,
            avg_buy_price=avg_buy,
            avg_sell_price=avg_sell,
            avg_spread_pct=spread,
            inventory_qty=inv_qty,
            inventory_avg_cost=inv_cost,
        )

    # ─── CONVENIENCE METHODS ──────────────────────────────────────────────

    def get_summary(self, period: str = "today") -> PnLSummary:
        """Get P&L summary for a named period (London/BST timezone)."""
        from zoneinfo import ZoneInfo
        london = ZoneInfo("Europe/London")
        now = datetime.now(london).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if period == "today":
            s = self.compute_fifo(from_date=today_start)
            s.period = "Today"
        elif period == "yesterday":
            yesterday = today_start - timedelta(days=1)
            s = self.compute_fifo(from_date=yesterday, to_date=today_start)
            s.period = "Yesterday"
        elif period == "week":
            week_start = today_start - timedelta(days=now.weekday())
            s = self.compute_fifo(from_date=week_start)
            s.period = "This Week"
        elif period == "month":
            month_start = today_start.replace(day=1)
            s = self.compute_fifo(from_date=month_start)
            s.period = now.strftime("%B %Y")
        elif period == "year":
            year_start = today_start.replace(month=1, day=1)
            s = self.compute_fifo(from_date=year_start)
            s.period = str(now.year)
        elif period == "all":
            s = self.compute_fifo()
            s.period = "All Time"
        else:
            s = self.compute_fifo(from_date=today_start)
            s.period = "Today"

        return s

    def format_summary(self, summary: PnLSummary) -> str:
        """Format P&L summary as a readable string for Telegram."""
        # Convert EUR P&L to USDT using avg sell rate
        avg_rate = summary.avg_sell_price if summary.avg_sell_price > 0 else summary.avg_buy_price
        if avg_rate > 0:
            pnl_usdt = summary.realized_pnl / avg_rate
            spread_usdt = summary.spread_pnl / avg_rate
            inst_usdt = summary.institutional_pnl / avg_rate
        else:
            pnl_usdt = summary.realized_pnl
            spread_usdt = summary.spread_pnl
            inst_usdt = summary.institutional_pnl

        lines = [
            f"📊 <b>P&L Report — {summary.period}</b>",
            f"<i>{summary.period_start.strftime('%b %d')} → {summary.period_end.strftime('%b %d, %Y')}</i>",
            "",
            f"📈 <b>P&L: {pnl_usdt:+.2f} USDT</b>",
            f"  💱 Spread: {spread_usdt:+.2f} USDT",
            f"  🏦 Institutional: {inst_usdt:+.2f} USDT",
            "",
            f"🔴 Sold: {summary.sell_volume_crypto:.2f} USDT → €{summary.sell_volume_eur:.2f}",
            f"🟢 Cost: {summary.matched_usdt:.2f} USDT ← €{summary.matched_cost_eur:.2f}",
            f"💰 Profit: €{summary.realized_pnl:.2f} ({summary.avg_spread_pct:.2f}% spread)",
        ]

        # Fee breakdown
        try:
            p2p_fees = getattr(summary, 'januar_p2p_fees', None)
            transfer_fees = getattr(summary, 'januar_transfer_fees', None)
            bitget_fees = getattr(summary, 'bitget_deposit_fees', None)
            total_rail = getattr(summary, 'total_rail_fees', None)
            if total_rail and total_rail > 0:
                lines.append('')
                lines.append('💸 <b>Fee Breakdown:</b>')
                lines.append(f"  Januar P2P Payouts: €{p2p_fees:.2f}")
                lines.append(f"  Januar Transfers: €{transfer_fees:.2f}")
                lines.append(f"  Bitget Deposits: €{bitget_fees:.2f}")
                lines.append(f"  <b>Total Fees: €{total_rail:.2f}</b>")
        except Exception:
            pass

        # Institutional buy stats
        try:
            inst = self.get_institutional_summary(summary.period_start, summary.period_end)
            if inst['count'] > 0:
                lines.append('')
                lines.append('🏦 <b>Institutional Buys:</b>')
                lines.append(f"  {inst['count']} transfers — {inst['usdt']:.2f} USDT (€{inst['eur']:.2f})")
                lines.append(f"  Avg rate: €{inst['avg_rate']:.4f}/USDT")
        except Exception:
            pass

        if summary.inventory_qty > 0:
            lines.extend([
                "",
                "💰 <b>Inventory:</b>",
                f"  {summary.inventory_qty:.2f} USDT (avg €{summary.inventory_avg_cost:.4f}/USDT)",
            ])

        return "\n".join(lines)


    # ─── HEATMAP ───────────────────────────────────────────────────────────

    def get_hourly_heatmap(self, days: int = 30) -> str:
        """Generate hourly volume heatmap for Telegram."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        trades = [t for t in self.get_trades(from_date=cutoff) if t.fiat_currency.upper() == "EUR"]

        if not trades:
            return "\U0001f4ca <b>No trade data</b> for the last " + str(days) + " days"

        hourly_vol = {h: 0.0 for h in range(24)}
        hourly_count = {h: 0 for h in range(24)}

        for t in trades:
            h = t.completed_at.hour
            hourly_vol[h] += float(t.fiat_amount)
            hourly_count[h] += 1

        max_vol = max(hourly_vol.values()) if hourly_vol else 1

        lines = ["\U0001f4ca <b>Volume Heatmap</b> (last " + str(days) + " days)", ""]
        lines.append("<pre>")

        for h in range(24):
            vol = hourly_vol[h]
            count = hourly_count[h]
            ratio = vol / max_vol if max_vol > 0 else 0
            bar_len = int(ratio * 12)
            bar = "\u2588" * bar_len + "\u2591" * (12 - bar_len)
            hour_str = str(h).zfill(2) + ":00"
            vol_str = "\u20ac" + str(int(vol))
            lines.append(hour_str + " " + bar + " " + vol_str + " (" + str(count) + ")")

        lines.append("</pre>")

        peak_h = max(hourly_vol, key=hourly_vol.get)
        dead_h = min(hourly_vol, key=hourly_vol.get)
        lines.append("")
        lines.append("\U0001f525 Peak: <b>" + str(peak_h).zfill(2) + ":00</b> (\u20ac" + str(int(hourly_vol[peak_h])) + ", " + str(hourly_count[peak_h]) + " orders)")
        lines.append("\U0001f4a4 Quiet: <b>" + str(dead_h).zfill(2) + ":00</b> (\u20ac" + str(int(hourly_vol[dead_h])) + ", " + str(hourly_count[dead_h]) + " orders)")

        return chr(10).join(lines)

    # ─── SPREAD ANALYSIS ──────────────────────────────────────────────────

    def get_spread_analysis(self, days: int = 30) -> str:
        """Analyze effective spreads and suggest optimizations."""
        from datetime import timedelta
        from collections import defaultdict
        cutoff = datetime.now() - timedelta(days=days)
        trades = [t for t in self.get_trades(from_date=cutoff) if t.fiat_currency.upper() == "EUR"]

        if not trades:
            return "\U0001f4ca <b>No trade data</b> for the last " + str(days) + " days"

        buys = [t for t in trades if t.side == "buy"]
        sells = [t for t in trades if t.side == "sell"]

        if not buys or not sells:
            return "\U0001f4ca <b>Need both buy and sell data</b> for spread analysis"

        avg_buy = sum(float(t.price) for t in buys) / len(buys)
        avg_sell = sum(float(t.price) for t in sells) / len(sells)
        overall_spread = ((avg_sell - avg_buy) / avg_buy) * 100 if avg_buy > 0 else 0

        # Daily spread breakdown
        daily_spreads = defaultdict(lambda: {"buy_prices": [], "sell_prices": [], "buy_vol": 0.0, "sell_vol": 0.0})

        for t in trades:
            day = t.completed_at.strftime("%Y-%m-%d")
            if t.side == "buy":
                daily_spreads[day]["buy_prices"].append(float(t.price))
                daily_spreads[day]["buy_vol"] += float(t.fiat_amount)
            else:
                daily_spreads[day]["sell_prices"].append(float(t.price))
                daily_spreads[day]["sell_vol"] += float(t.fiat_amount)

        spread_values = []
        for day, data in sorted(daily_spreads.items()):
            if data["buy_prices"] and data["sell_prices"]:
                day_avg_buy = sum(data["buy_prices"]) / len(data["buy_prices"])
                day_avg_sell = sum(data["sell_prices"]) / len(data["sell_prices"])
                day_spread = ((day_avg_sell - day_avg_buy) / day_avg_buy) * 100
                spread_values.append(day_spread)

        # Hourly spread
        hourly_buy = defaultdict(list)
        hourly_sell = defaultdict(list)
        for t in buys:
            hourly_buy[t.completed_at.hour].append(float(t.price))
        for t in sells:
            hourly_sell[t.completed_at.hour].append(float(t.price))

        best_hours = []
        for h in range(24):
            if hourly_buy.get(h) and hourly_sell.get(h):
                hb = sum(hourly_buy[h]) / len(hourly_buy[h])
                hs = sum(hourly_sell[h]) / len(hourly_sell[h])
                h_spread = ((hs - hb) / hb) * 100
                best_hours.append((h, h_spread, len(hourly_buy[h]) + len(hourly_sell[h])))

        best_hours.sort(key=lambda x: x[1], reverse=True)

        lines = ["\U0001f4ca <b>Spread Analysis</b> (last " + str(days) + " days)", ""]
        lines.append("\U0001f4b0 <b>Overall:</b>")
        lines.append("  Avg Buy:  \u20ac{:.4f}/unit".format(avg_buy))
        lines.append("  Avg Sell: \u20ac{:.4f}/unit".format(avg_sell))
        lines.append("  Spread:   <b>{:.2f}%</b>".format(overall_spread))
        lines.append("")

        if spread_values:
            min_s = min(spread_values)
            max_s = max(spread_values)
            avg_s = sum(spread_values) / len(spread_values)
            lines.append("\U0001f4c8 <b>Daily Range:</b>")
            lines.append("  Best:  {:.2f}%".format(max_s))
            lines.append("  Worst: {:.2f}%".format(min_s))
            lines.append("  Avg:   {:.2f}%".format(avg_s))
            lines.append("")

        if best_hours:
            lines.append("\u23f0 <b>Best Hours to Trade:</b>")
            for h, s, c in best_hours[:3]:
                lines.append("  " + str(h).zfill(2) + ":00 \u2014 {:.2f}% spread ({} trades)".format(s, c))
            lines.append("")
            if len(best_hours) >= 3:
                worst = list(reversed(best_hours[-3:]))
                lines.append("\u26a0\ufe0f <b>Worst Hours:</b>")
                for h, s, c in worst:
                    lines.append("  " + str(h).zfill(2) + ":00 \u2014 {:.2f}% spread ({} trades)".format(s, c))

        lines.append("")
        if overall_spread < 0.5:
            lines.append("\U0001f4a1 <b>Tip:</b> Spread is thin ({:.2f}%). Consider widening ask by 0.2-0.3%.".format(overall_spread))
        elif overall_spread > 1.5:
            lines.append("\U0001f4a1 <b>Tip:</b> Spread is wide ({:.2f}%). Tighten pricing to attract more volume.".format(overall_spread))
        else:
            lines.append("\U0001f4a1 <b>Tip:</b> Spread looks healthy at {:.2f}%. Focus on increasing volume during peak hours.".format(overall_spread))

        return chr(10).join(lines)






    def get_institutional_summary(self, from_date=None, to_date=None) -> dict:
        """Get institutional buy stats for a period."""
        try:
            from src.services.institutional_tracker import get_institutional_tracker
            tracker = get_institutional_tracker()
            buys = tracker.get_matched_buys(from_date=from_date, to_date=to_date)
            if not buys:
                return {"count": 0, "eur": Decimal("0"), "usdt": Decimal("0"), "avg_rate": Decimal("0")}
            total_eur = sum(b.eur_amount for b in buys)
            total_usdt = sum(b.usdt_amount for b in buys)
            avg_rate = (total_eur / total_usdt).quantize(Decimal("0.0001")) if total_usdt > 0 else Decimal("0")
            return {"count": len(buys), "eur": total_eur, "usdt": total_usdt, "avg_rate": avg_rate}
        except Exception:
            return {"count": 0, "eur": Decimal("0"), "usdt": Decimal("0"), "avg_rate": Decimal("0")}

# Singleton
_tracker: Optional[FifoPnLTracker] = None

def get_fifo_tracker() -> FifoPnLTracker:
    global _tracker
    if _tracker is None:
        _tracker = FifoPnLTracker()
    return _tracker
