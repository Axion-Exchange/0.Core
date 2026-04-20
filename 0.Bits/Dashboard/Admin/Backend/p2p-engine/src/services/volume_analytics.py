"""
VOLUME ANALYTICS — Institutional-Grade Hourly Heatmap
=====================================================
Queries the existing order_history + orders tables to produce:

1. A 24×7 heatmap matrix (orders/volume by hour-of-day × day-of-week)
2. Summary statistics (peak hour, busiest window, weekday vs weekend)

Zero new tables — pure read-only analytics over existing data.
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from src.core.persistence import order_db

logger = logging.getLogger(__name__)

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class VolumeAnalytics:
    """
    Institutional-grade volume analytics for P2P order flow.

    Queries SQLite order_history (state transitions) joined with
    orders (side, amounts) to produce hourly volume heatmaps.
    """

    def __init__(self, db=None):
        self._db = db or order_db
        self._tz = os.getenv("ANALYTICS_TZ", "UTC")

    def get_heatmap(self, days: int = 30) -> dict[str, Any]:
        """
        Build a 24×7 heatmap of completed orders.

        Returns:
            {
                "period_days": 30,
                "timezone": "UTC",
                "heatmap": [{"day": "Mon", "hour": 14, "orders": 12, "usdt": 3420.5, "fiat_eur": 2890.0}, ...],
                "peak": {"day": "Wed", "hour": 15, "orders": 18},
                "total_orders": 847,
                "generated_at": "2026-02-21T16:55:00Z"
            }
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Query: completed orders with timestamps and amounts
        rows = self._query_completions(cutoff)

        # Build 24×7 matrix
        matrix = defaultdict(lambda: {"orders": 0, "usdt": 0.0, "fiat_eur": 0.0})

        for row in rows:
            ts = row["timestamp"]
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00") if "Z" in ts else ts)
            except (ValueError, TypeError):
                continue

            day = dt.weekday()  # 0=Mon, 6=Sun
            hour = dt.hour
            key = (day, hour)

            matrix[key]["orders"] += 1

            # Parse order_data for amounts
            order_data = row.get("order_data")
            if order_data:
                try:
                    od = json.loads(order_data) if isinstance(order_data, str) else order_data
                    crypto_amt = float(od.get("crypto_amount", 0) or 0)
                    fiat_amt = float(od.get("fiat_amount", 0) or 0)
                    matrix[key]["usdt"] += crypto_amt
                    matrix[key]["fiat_eur"] += fiat_amt
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

        # Flatten to list
        heatmap = []
        for day_idx in range(7):
            for hour in range(24):
                cell = matrix.get((day_idx, hour), {"orders": 0, "usdt": 0.0, "fiat_eur": 0.0})
                heatmap.append({
                    "day": DAY_NAMES[day_idx],
                    "day_index": day_idx,
                    "hour": hour,
                    "orders": cell["orders"],
                    "usdt": round(cell["usdt"], 2),
                    "fiat_eur": round(cell["fiat_eur"], 2),
                })

        # Find peak
        peak = max(heatmap, key=lambda x: x["orders"]) if heatmap else None
        total = sum(c["orders"] for c in heatmap)

        return {
            "period_days": days,
            "timezone": self._tz,
            "heatmap": heatmap,
            "peak": {"day": peak["day"], "hour": peak["hour"], "orders": peak["orders"]} if peak else None,
            "total_orders": total,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    def get_stats(self, days: int = 30) -> dict[str, Any]:
        """
        Summary statistics from the heatmap data.

        Returns peak hour, busiest 3-hour window, weekday vs weekend comparison.
        """
        heatmap_data = self.get_heatmap(days)
        cells = heatmap_data["heatmap"]
        total = heatmap_data["total_orders"]

        if total == 0:
            return {
                "period_days": days,
                "total_orders": 0,
                "total_usdt": 0.0,
                "total_fiat_eur": 0.0,
                "avg_orders_per_hour": 0.0,
                "peak_hour": None,
                "peak_day": None,
                "busiest_window": None,
                "quietest_window": None,
                "weekday_vs_weekend": None,
                "hourly_breakdown": [],
                "daily_breakdown": [],
                "generated_at": heatmap_data["generated_at"],
            }

        total_usdt = sum(c["usdt"] for c in cells)
        total_fiat = sum(c["fiat_eur"] for c in cells)

        # ── Hourly aggregation (across all days) ──
        hourly = defaultdict(lambda: {"orders": 0, "usdt": 0.0})
        for c in cells:
            hourly[c["hour"]]["orders"] += c["orders"]
            hourly[c["hour"]]["usdt"] += c["usdt"]

        hourly_breakdown = [
            {"hour": h, "orders": hourly[h]["orders"], "usdt": round(hourly[h]["usdt"], 2)}
            for h in range(24)
        ]

        peak_hour = max(range(24), key=lambda h: hourly[h]["orders"])

        # ── Daily aggregation (across all hours) ──
        daily = defaultdict(lambda: {"orders": 0, "usdt": 0.0})
        for c in cells:
            daily[c["day_index"]]["orders"] += c["orders"]
            daily[c["day_index"]]["usdt"] += c["usdt"]

        daily_breakdown = [
            {"day": DAY_NAMES[d], "orders": daily[d]["orders"], "usdt": round(daily[d]["usdt"], 2)}
            for d in range(7)
        ]

        peak_day_idx = max(range(7), key=lambda d: daily[d]["orders"])

        # ── Busiest/quietest 3-hour window ──
        best_window, best_count = 0, 0
        worst_window, worst_count = 0, float("inf")
        for start in range(24):
            window_count = sum(hourly[(start + i) % 24]["orders"] for i in range(3))
            if window_count > best_count:
                best_count = window_count
                best_window = start
            if window_count < worst_count:
                worst_count = window_count
                worst_window = start

        # ── Weekday vs weekend ──
        weekday_orders = sum(daily[d]["orders"] for d in range(5))
        weekend_orders = sum(daily[d]["orders"] for d in range(5, 7))
        # Normalize: weekdays have 5 days, weekends have 2
        num_weeks = max(days / 7, 1)

        return {
            "period_days": days,
            "total_orders": total,
            "total_usdt": round(total_usdt, 2),
            "total_fiat_eur": round(total_fiat, 2),
            "avg_orders_per_hour": round(total / (days * 24), 2),
            "peak_hour": peak_hour,
            "peak_hour_label": f"{peak_hour:02d}:00 UTC",
            "peak_day": DAY_NAMES[peak_day_idx],
            "busiest_window": f"{best_window:02d}:00-{(best_window + 3) % 24:02d}:00 UTC",
            "busiest_window_orders": best_count,
            "quietest_window": f"{worst_window:02d}:00-{(worst_window + 3) % 24:02d}:00 UTC",
            "quietest_window_orders": worst_count,
            "weekday_vs_weekend": {
                "weekday_avg_per_day": round(weekday_orders / (5 * num_weeks), 1),
                "weekend_avg_per_day": round(weekend_orders / (2 * num_weeks), 1),
                "weekday_total": weekday_orders,
                "weekend_total": weekend_orders,
            },
            "hourly_breakdown": hourly_breakdown,
            "daily_breakdown": daily_breakdown,
            "generated_at": heatmap_data["generated_at"],
        }

    def _query_completions(self, cutoff_iso: str) -> list[dict]:
        """
        Query completed orders from order_history joined with orders table.

        Returns list of dicts with: timestamp, order_data (JSON string).
        """
        with self._db._connect() as conn:
            cursor = conn.execute("""
                SELECT h.timestamp, o.order_data
                FROM order_history h
                JOIN orders o ON o.id = h.order_id
                WHERE h.to_state = 'COMPLETED'
                  AND h.timestamp >= ?
                ORDER BY h.timestamp
            """, (cutoff_iso,))

            return [
                {"timestamp": row[0], "order_data": row[1]}
                for row in cursor.fetchall()
            ]
