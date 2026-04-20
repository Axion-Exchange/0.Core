"""
Market Intelligence — competitor spread monitoring and revenue target tracking.
Telegram commands: /competitors, /target
"""

import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger("market_intel")


class MarketIntel:
    """Competitor monitoring and revenue targets."""

    def __init__(self, db_path: str = "data/pnl.db"):
        self.db_path = Path(db_path)
        self._daily_target = float(os.getenv("DAILY_PNL_TARGET", "100"))
        self._weekly_target = float(os.getenv("WEEKLY_PNL_TARGET", "500"))

    def _get_client(self):
        """Get Binance API client."""
        try:
            from src.core.registry import registry
            return registry.get_exchange_api("binance")
        except Exception:
            pass
        try:
            from src.exchanges.binance.api_client import BinanceApiClient
            return BinanceApiClient(
                api_key=os.getenv("BINANCE_API_KEY"),
                api_secret=os.getenv("BINANCE_API_SECRET"),
            )
        except Exception:
            return None

    # ─── COMPETITOR SPREAD MONITOR ────────────────────────────────────────

    async def get_competitor_analysis(self) -> str:
        """Fetch top market ads and compare with our ads."""
        client = self._get_client()
        if not client:
            return "\u274c Cannot connect to Binance API"

        # Fetch our ads
        our_ads = await client.get_ads()

        # trade_type BUY = I want to buy, show me sellers (our SELL competitors)
        # trade_type SELL = I want to sell, show me buyers (our BUY competitors)
        sell_market = await client.search_market_ads(
            trade_type="BUY", asset="USDT", fiat="EUR", rows=10
        )
        buy_market = await client.search_market_ads(
            trade_type="SELL", asset="USDT", fiat="EUR", rows=10
        )

        lines = ["\U0001f4ca <b>Competitor Spread Analysis</b>", ""]

        # Our ads
        our_sell_price = None
        our_buy_price = None
        for ad in our_ads:
            if ad.fiat_currency.value == "EUR":
                price = float(ad.price)
                side = ad.side.value.upper()
                avail = ad.available_amount
                if side == "SELL":
                    our_sell_price = price
                    lines.append("\U0001f7e2 Our SELL: <b>\u20ac{:.4f}</b> ({} USDT avail)".format(price, avail))
                elif side == "BUY":
                    our_buy_price = price
                    lines.append("\U0001f534 Our BUY:  <b>\u20ac{:.4f}</b> ({} USDT avail)".format(price, avail))

        if our_sell_price and our_buy_price:
            our_spread = ((our_sell_price - our_buy_price) / our_buy_price) * 100 if our_buy_price > 0 else 0
            lines.append("\U0001f4b0 Our spread: <b>{:.2f}%</b>".format(our_spread))

        # Market SELL ads (other sellers = our competitors when we sell)
        lines.extend(["", "\U0001f3ea <b>Market SELL Ads (top 5):</b>"])
        sell_prices = []
        for i, ad in enumerate(sell_market[:5]):
            price = float(ad.price)
            sell_prices.append(price)
            avail = ad.available_amount
            marker = ""
            if our_sell_price:
                diff_bps = ((our_sell_price - price) / price) * 10000 if price > 0 else 0
                if diff_bps > 0:
                    marker = " (\U0001f7e2 we're {:.0f}bps higher)".format(diff_bps)
                elif diff_bps < 0:
                    marker = " (\U0001f534 we're {:.0f}bps lower)".format(abs(diff_bps))
                else:
                    marker = " (\u2705 same)"
            lines.append("  {}. \u20ac{:.4f} ({} USDT){}".format(i + 1, price, avail, marker))

        # Market BUY ads (other buyers = our competitors when we buy)
        lines.extend(["", "\U0001f3ea <b>Market BUY Ads (top 5):</b>"])
        buy_prices = []
        for i, ad in enumerate(buy_market[:5]):
            price = float(ad.price)
            buy_prices.append(price)
            avail = ad.available_amount
            marker = ""
            if our_buy_price:
                diff_bps = ((our_buy_price - price) / price) * 10000 if price > 0 else 0
                if diff_bps > 0:
                    marker = " (\U0001f7e2 we're {:.0f}bps higher)".format(diff_bps)
                elif diff_bps < 0:
                    marker = " (\U0001f534 we're {:.0f}bps lower)".format(abs(diff_bps))
                else:
                    marker = " (\u2705 same)"
            lines.append("  {}. \u20ac{:.4f} ({} USDT){}".format(i + 1, price, avail, marker))

        # Market spread
        if sell_prices and buy_prices:
            best_sell = min(sell_prices)
            best_buy = max(buy_prices)
            market_spread = ((best_sell - best_buy) / best_buy) * 100 if best_buy > 0 else 0
            lines.extend([
                "",
                "\U0001f4c8 <b>Market spread:</b> {:.2f}% (best sell {:.4f} vs best buy {:.4f})".format(
                    market_spread, best_sell, best_buy
                ),
            ])

            if our_sell_price and our_buy_price:
                our_s = ((our_sell_price - our_buy_price) / our_buy_price) * 100 if our_buy_price > 0 else 0
                diff = our_s - market_spread
                if diff > 0.1:
                    lines.append("\U0001f4a1 <b>Tip:</b> Your spread is {:.2f}% wider than market. Could tighten to attract volume.".format(diff))
                elif diff < -0.1:
                    lines.append("\U0001f4a1 <b>Tip:</b> Your spread is {:.2f}% tighter than market. Great for volume, watch margin.".format(abs(diff)))
                else:
                    lines.append("\U0001f4a1 <b>Tip:</b> Your spread matches market \u2014 competitive positioning!")

        # Position ranking
        if our_sell_price and sell_prices:
            rank = sum(1 for p in sell_prices if p < our_sell_price) + 1
            lines.append("")
            lines.append("\U0001f3c6 SELL rank: <b>#{}</b> of {} (lower price = better for buyer)".format(rank, len(sell_prices)))

        if our_buy_price and buy_prices:
            rank = sum(1 for p in buy_prices if p > our_buy_price) + 1
            lines.append("\U0001f3c6 BUY rank:  <b>#{}</b> of {} (higher price = better for seller)".format(rank, len(buy_prices)))

        return "\n".join(lines)

    # ─── REVENUE TARGET TRACKER ───────────────────────────────────────────

    def get_target_progress(self) -> str:
        """Show progress toward daily and weekly revenue targets."""
        from src.services.pnl_tracker import get_fifo_tracker
        tracker = get_fifo_tracker()

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())

        # Today's P&L
        today_summary = tracker.compute_fifo(from_date=today_start, to_date=now)
        today_pnl = float(today_summary.realized_pnl)

        # Week P&L
        week_summary = tracker.compute_fifo(from_date=week_start, to_date=now)
        week_pnl = float(week_summary.realized_pnl)

        # Progress bars
        daily_pct = min(today_pnl / self._daily_target * 100, 100) if self._daily_target > 0 else 0
        weekly_pct = min(week_pnl / self._weekly_target * 100, 100) if self._weekly_target > 0 else 0

        daily_bar = self._progress_bar(daily_pct)
        weekly_bar = self._progress_bar(weekly_pct)

        lines = ["\U0001f3af <b>Revenue Target Progress</b>", ""]

        # Daily
        daily_emoji = "\u2705" if daily_pct >= 100 else "\U0001f7e1" if daily_pct >= 50 else "\U0001f534"
        lines.append("{} <b>Daily: \u20ac{:.0f} / \u20ac{:.0f}</b>".format(daily_emoji, today_pnl, self._daily_target))
        lines.append("   {} {:.0f}%".format(daily_bar, daily_pct))

        # Remaining today
        if daily_pct < 100:
            remaining = self._daily_target - today_pnl
            hours_left = max(24 - now.hour - now.minute / 60, 0.1)
            rate_needed = remaining / hours_left
            lines.append("   \u20ac{:.0f} remaining \u2014 need \u20ac{:.0f}/hr".format(remaining, rate_needed))

        lines.append("")

        # Weekly
        weekly_emoji = "\u2705" if weekly_pct >= 100 else "\U0001f7e1" if weekly_pct >= 50 else "\U0001f534"
        lines.append("{} <b>Weekly: \u20ac{:.0f} / \u20ac{:.0f}</b>".format(weekly_emoji, week_pnl, self._weekly_target))
        lines.append("   {} {:.0f}%".format(weekly_bar, weekly_pct))

        # Remaining this week
        if weekly_pct < 100:
            remaining_w = self._weekly_target - week_pnl
            days_left = max(7 - now.weekday() - now.hour / 24, 0.1)
            daily_needed = remaining_w / days_left
            lines.append("   \u20ac{:.0f} remaining \u2014 need \u20ac{:.0f}/day".format(remaining_w, daily_needed))

        # Volume context
        lines.extend([
            "",
            "\U0001f4ca <b>Today's Activity:</b>",
            "   {} trades, \u20ac{:.0f} total volume".format(
                today_summary.buy_count + today_summary.sell_count,
                float(today_summary.buy_volume_eur + today_summary.sell_volume_eur),
            ),
        ])

        if float(today_summary.avg_spread_pct) > 0:
            lines.append("   {:.2f}% avg spread".format(float(today_summary.avg_spread_pct)))

        # Streak / daily averages
        daily_avg = week_pnl / max(now.weekday() + 1, 1) if (now.weekday() + 1) > 0 else 0
        lines.extend([
            "",
            "\U0001f4c8 Daily avg this week: <b>\u20ac{:.0f}</b>".format(daily_avg),
        ])

        if daily_avg >= self._daily_target:
            lines.append("\U0001f525 On target pace!")
        elif daily_avg >= self._daily_target * 0.7:
            lines.append("\U0001f7e1 Close to pace \u2014 pick up volume")
        else:
            lines.append("\U0001f534 Below pace \u2014 need to increase activity")

        return "\n".join(lines)

    def set_targets(self, daily: float | None = None, weekly: float | None = None) -> str:
        """Update targets. Returns confirmation message."""
        changes = []
        if daily is not None:
            self._daily_target = daily
            changes.append("Daily: \u20ac{:.0f}".format(daily))
        if weekly is not None:
            self._weekly_target = weekly
            changes.append("Weekly: \u20ac{:.0f}".format(weekly))

        if changes:
            return "\u2705 Targets updated: " + ", ".join(changes)
        return "\u274c No changes. Usage: /target 150 (daily) or /target 150 700 (daily + weekly)"

    def _progress_bar(self, pct: float) -> str:
        """Generate a progress bar."""
        filled = int(pct / 100 * 15)
        empty = 15 - filled
        if pct >= 100:
            return "\u2588" * 15
        return "\u2588" * filled + "\u2591" * empty


# Singleton
_market_intel: MarketIntel | None = None

def get_market_intel() -> MarketIntel:
    global _market_intel
    if _market_intel is None:
        _market_intel = MarketIntel()
    return _market_intel
