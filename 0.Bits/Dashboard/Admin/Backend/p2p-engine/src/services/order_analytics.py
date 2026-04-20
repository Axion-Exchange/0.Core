"""
Order Analytics — comprehensive stats from Binance order history.
Tracks ALL orders (completed, cancelled, expired) for success rates and volume analysis.
"""

import sqlite3
import logging
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger("analytics")


class OrderAnalytics:
    """Pulls ALL order history from Binance for analytics (not just completed)."""

    def __init__(self, db_path: str = "data/pnl.db"):
        self.db_path = Path(db_path)
        self._init_analytics_table()
        self._last_sync: datetime | None = None
        self._sync_cooldown = 300

    def _init_analytics_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS all_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE NOT NULL,
                    side TEXT NOT NULL,
                    state TEXT NOT NULL,
                    crypto_amount TEXT DEFAULT '0',
                    crypto_asset TEXT DEFAULT 'USDT',
                    fiat_amount TEXT DEFAULT '0',
                    fiat_currency TEXT DEFAULT 'EUR',
                    price TEXT DEFAULT '0',
                    created_at TEXT NOT NULL,
                    counterparty TEXT DEFAULT '',
                    synced_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_all_orders_state
                ON all_orders(state, created_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_all_orders_side
                ON all_orders(side, state, created_at)
            """)

    async def sync_all_orders(self, force: bool = False) -> int:
        """Sync ALL orders (completed + cancelled + expired) from Binance."""
        if not force and self._last_sync:
            elapsed = (datetime.now() - self._last_sync).total_seconds()
            if elapsed < self._sync_cooldown:
                return 0

        try:
            from src.core.registry import registry
            client = registry.get_exchange_api("binance")
        except Exception:
            client = None

        if not client:
            # Try direct client
            try:
                import os
                from src.exchanges.binance.api_client import BinanceApiClient
                client = BinanceApiClient(
                    api_key=os.getenv("BINANCE_API_KEY"),
                    api_secret=os.getenv("BINANCE_API_SECRET"),
                )
            except Exception:
                logger.warning("No Binance client for analytics sync")
                return 0

        new_count = 0
        for trade_type in ["BUY", "SELL"]:
            page = 1
            while True:
                try:
                    orders = await client.get_order_history(
                        trade_type=trade_type, page=page, rows=50,
                    )
                except Exception as e:
                    logger.warning("Analytics sync error (page %d): %s", page, e)
                    break

                if not orders:
                    break

                for order in orders:
                    if self._upsert_all_order(order):
                        new_count += 1

                if len(orders) < 50:
                    break
                page += 1

        self._last_sync = datetime.now()
        if new_count > 0:
            logger.info("Analytics sync: %d new orders", new_count)
        return new_count

    def _upsert_all_order(self, order) -> bool:
        try:
            side = order.side.value if hasattr(order.side, 'value') else str(order.side)
            state = order.status.value if hasattr(order.status, 'value') else str(order.status or "unknown")
            with sqlite3.connect(self.db_path) as conn:
                # Try insert, if exists update state
                conn.execute("""
                    INSERT INTO all_orders
                    (external_id, side, state, crypto_amount, crypto_asset,
                     fiat_amount, fiat_currency, price, created_at, counterparty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(external_id) DO UPDATE SET state=excluded.state
                """, (
                    order.external_id,
                    side,
                    state,
                    str(order.crypto_amount or "0"),
                    order.crypto_asset.value if hasattr(order.crypto_asset, 'value') else str(order.crypto_asset or "USDT"),
                    str(order.fiat_amount or "0"),
                    order.fiat_currency.value if hasattr(order.fiat_currency, 'value') else str(order.fiat_currency or "EUR"),
                    str(order.price or "0"),
                    order.created_at.isoformat() if order.created_at else datetime.now().isoformat(),
                    order.counterparty.name if order.counterparty else "",
                ))
                return conn.total_changes > 0
        except Exception as e:
            logger.debug("Analytics upsert error: %s", e)
            return False

    def _get_orders(self, from_date=None, to_date=None, currency="EUR"):
        """Get all orders in period, filtered by currency."""
        query = "SELECT * FROM all_orders WHERE fiat_currency = ?"
        params = [currency]
        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date.isoformat())
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date.isoformat())
        query += " ORDER BY created_at ASC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchall()

    def get_stats(self, period: str = "today") -> str:
        """Generate comprehensive stats report for Telegram."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        periods = {
            "today": ("Today", today_start, now),
            "yesterday": ("Yesterday", today_start - timedelta(days=1), today_start),
            "week": ("This Week", today_start - timedelta(days=now.weekday()), now),
            "month": (now.strftime("%B"), today_start.replace(day=1), now),
            "year": (str(now.year), today_start.replace(month=1, day=1), now),
            "all": ("All Time", None, None),
        }

        label, from_d, to_d = periods.get(period, periods["today"])
        orders = self._get_orders(from_date=from_d, to_date=to_d)

        if not orders:
            return "\U0001f4ca <b>Stats \u2014 " + label + "</b>\n\nNo orders found."

        # Categorize
        buy_completed = []
        buy_cancelled = []
        buy_other = []
        sell_completed = []
        sell_cancelled = []
        sell_other = []

        # Only count orders that progressed past browsing.
        # awaiting_payment = someone just clicked the ad, not a real order attempt.
        # Only cancelled orders that were previously marked_as_paid count as "missed".
        real_states = {"completed", "released", "cancelled", "expired",
                       "cancelled_by_system", "buyer_cancelled",
                       "marked_as_paid", "appealed", "error",
                       "agent_required", "delayed", "releasing"}
        completed_states = {"completed", "released"}
        cancelled_states = {"cancelled", "expired", "cancelled_by_system", "buyer_cancelled"}
        active_states = {"marked_as_paid", "appealed", "releasing",
                         "agent_required", "delayed", "error"}

        for o in orders:
            side = o["side"]
            state = o["state"]
            fiat = float(o["fiat_amount"])

            # Skip awaiting_payment — not a real order attempt
            if state == "awaiting_payment":
                continue

            if side == "buy":
                if state in completed_states:
                    buy_completed.append(fiat)
                elif state in cancelled_states:
                    buy_cancelled.append(fiat)
                elif state in active_states:
                    buy_other.append(fiat)
            else:
                if state in completed_states:
                    sell_completed.append(fiat)
                elif state in cancelled_states:
                    sell_cancelled.append(fiat)
                elif state in active_states:
                    sell_other.append(fiat)

        # Calculate rates
        buy_total = len(buy_completed) + len(buy_cancelled) + len(buy_other)
        sell_total = len(sell_completed) + len(sell_cancelled) + len(sell_other)
        buy_rate = (len(buy_completed) / buy_total * 100) if buy_total > 0 else 0
        sell_rate = (len(sell_completed) / sell_total * 100) if sell_total > 0 else 0
        overall_total = buy_total + sell_total
        overall_completed = len(buy_completed) + len(sell_completed)
        overall_rate = (overall_completed / overall_total * 100) if overall_total > 0 else 0

        buy_completed_vol = sum(buy_completed)
        buy_cancelled_vol = sum(buy_cancelled)
        sell_completed_vol = sum(sell_completed)
        sell_cancelled_vol = sum(sell_cancelled)

        # Build output
        lines = [
            "\U0001f4ca <b>Order Stats \u2014 " + label + "</b>",
            "",
            "\U0001f3af <b>Completion Rates:</b>",
            "  Overall: <b>{:.0f}%</b> ({}/{})".format(overall_rate, overall_completed, overall_total),
            "  \U0001f7e2 BUY:  <b>{:.0f}%</b> ({}/{})".format(buy_rate, len(buy_completed), buy_total),
            "  \U0001f534 SELL: <b>{:.0f}%</b> ({}/{})".format(sell_rate, len(sell_completed), sell_total),
            "",
            "\U0001f4b0 <b>Volume \u2014 Completed:</b>",
            "  \U0001f7e2 BUY:  \u20ac{:,.0f} ({} orders)".format(buy_completed_vol, len(buy_completed)),
            "  \U0001f534 SELL: \u20ac{:,.0f} ({} orders)".format(sell_completed_vol, len(sell_completed)),
            "",
            "\U0001f6ab <b>Volume \u2014 Missed (cancelled/expired):</b>",
            "  \U0001f7e2 BUY:  \u20ac{:,.0f} ({} orders)".format(buy_cancelled_vol, len(buy_cancelled)),
            "  \U0001f534 SELL: \u20ac{:,.0f} ({} orders)".format(sell_cancelled_vol, len(sell_cancelled)),
        ]

        if buy_cancelled_vol + sell_cancelled_vol > 0:
            missed_total = buy_cancelled_vol + sell_cancelled_vol
            lines.append("  \u26a0\ufe0f Total missed: \u20ac{:,.0f}".format(missed_total))

        # Pending/active
        buy_pending = len(buy_other)
        sell_pending = len(sell_other)
        if buy_pending + sell_pending > 0:
            lines.extend([
                "",
                "\u23f3 <b>Pending/Active:</b>",
                "  \U0001f7e2 BUY:  {} orders (\u20ac{:,.0f})".format(buy_pending, sum(buy_other)),
                "  \U0001f534 SELL: {} orders (\u20ac{:,.0f})".format(sell_pending, sum(sell_other)),
            ])

        return "\n".join(lines)

    def get_heatmap(self, period: str = "all", show_type: str = "both") -> str:
        """Generate heatmaps for opened and completed orders."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        periods = {
            "today": ("Today", today_start, now),
            "week": ("This Week", today_start - timedelta(days=now.weekday()), now),
            "month": (now.strftime("%B"), today_start.replace(day=1), now),
            "year": (str(now.year), today_start.replace(month=1, day=1), now),
            "all": ("All Time", None, None),
        }

        label, from_d, to_d = periods.get(period, periods["all"])
        orders = self._get_orders(from_date=from_d, to_date=to_d)

        if not orders:
            return "\U0001f4ca <b>Heatmap \u2014 " + label + "</b>\n\nNo data."

        completed_states = {"completed", "released"}

        # Bucket by hour
        opened_vol = {h: 0.0 for h in range(24)}
        opened_count = {h: 0 for h in range(24)}
        completed_vol = {h: 0.0 for h in range(24)}
        completed_count = {h: 0 for h in range(24)}

        for o in orders:
            # Skip awaiting_payment — just ad clicks, not real orders
            if o["state"] == "awaiting_payment":
                continue
            try:
                dt = datetime.fromisoformat(o["created_at"])
            except Exception:
                continue
            h = dt.hour
            fiat = float(o["fiat_amount"])
            opened_vol[h] += fiat
            opened_count[h] += 1
            if o["state"] in completed_states:
                completed_vol[h] += fiat
                completed_count[h] += 1

        lines = ["\U0001f4ca <b>Volume Heatmap \u2014 " + label + "</b>"]

        # Opened heatmap
        max_opened = max(opened_vol.values()) or 1
        lines.extend(["", "\U0001f4e5 <b>All Orders (Opened):</b>", "<pre>"])
        for h in range(24):
            ratio = opened_vol[h] / max_opened if max_opened > 0 else 0
            bar_len = int(ratio * 10)
            bar = "\u2588" * bar_len + "\u2591" * (10 - bar_len)
            lines.append("{:02d}:00 {} \u20ac{:>6,.0f} ({})".format(
                h, bar, opened_vol[h], opened_count[h]
            ))
        lines.append("</pre>")

        # Completed heatmap
        max_completed = max(completed_vol.values()) or 1
        lines.extend(["", "\u2705 <b>Completed Orders:</b>", "<pre>"])
        for h in range(24):
            ratio = completed_vol[h] / max_completed if max_completed > 0 else 0
            bar_len = int(ratio * 10)
            bar = "\u2588" * bar_len + "\u2591" * (10 - bar_len)
            lines.append("{:02d}:00 {} \u20ac{:>6,.0f} ({})".format(
                h, bar, completed_vol[h], completed_count[h]
            ))
        lines.append("</pre>")

        # Summary
        peak_opened = max(opened_vol, key=opened_vol.get)
        peak_completed = max(completed_vol, key=completed_vol.get)
        dead_h = min(opened_vol, key=opened_vol.get)

        lines.extend([
            "",
            "\U0001f525 Peak opened: <b>{:02d}:00</b> (\u20ac{:,.0f}, {} orders)".format(
                peak_opened, opened_vol[peak_opened], opened_count[peak_opened]
            ),
            "\u2705 Peak completed: <b>{:02d}:00</b> (\u20ac{:,.0f}, {} orders)".format(
                peak_completed, completed_vol[peak_completed], completed_count[peak_completed]
            ),
            "\U0001f4a4 Quietest: <b>{:02d}:00</b> (\u20ac{:,.0f}, {} orders)".format(
                dead_h, opened_vol[dead_h], opened_count[dead_h]
            ),
        ])

        # Completion rate by hour
        best_rate_h = None
        worst_rate_h = None
        best_rate = 0
        worst_rate = 100
        for h in range(24):
            if opened_count[h] >= 3:  # minimum sample
                rate = (completed_count[h] / opened_count[h]) * 100
                if rate > best_rate:
                    best_rate = rate
                    best_rate_h = h
                if rate < worst_rate:
                    worst_rate = rate
                    worst_rate_h = h

        if best_rate_h is not None and worst_rate_h is not None:
            lines.extend([
                "",
                "\U0001f3af <b>Completion Rate by Hour:</b>",
                "  Best:  {:02d}:00 \u2014 {:.0f}%".format(best_rate_h, best_rate),
                "  Worst: {:02d}:00 \u2014 {:.0f}%".format(worst_rate_h, worst_rate),
            ])

        return "\n".join(lines)


# Singleton
_analytics: OrderAnalytics | None = None

def get_analytics() -> OrderAnalytics:
    global _analytics
    if _analytics is None:
        _analytics = OrderAnalytics()
    return _analytics
