"""
DYNAMIC PRICING ENGINE
======================
Sets SELL ad prices based on the actual Weighted Average Cost (WAC) of
acquiring USDT from both Binance P2P BUY orders and Bitget OTC fills.

Target: net 0.5% margin after accounting for Januar transaction fees.

Formula:
    sell_price = WAC × (1 + target_net_margin + fee_buffer)
    
    Where:
        WAC = blended cost basis from unified_fifo_tracker
        target_net_margin = 0.5% (configurable via PRICING_TARGET_NET_MARGIN)
        fee_buffer = 0.2% (covers Januar's 0.1% in + 0.1% out)

Constraints:
    - BUY ad prices can be updated anytime ✅
    - SELL ad prices can ONLY be updated when no orders are in-deal
      (Binance returns error 187049 otherwise)
    - All ads use fixed prices (priceType=0)
"""

import asyncio
import logging
import os
import sqlite3
import time
from datetime import datetime
from typing import Any

from src.core.types import ExchangeId, OrderSide

logger = logging.getLogger("pricing_engine")


class PricingEngine:
    """
    Dynamically adjusts P2P ad prices based on real acquisition cost.

    Runs as a supervised background task alongside AdRebalancer.
    """

    def __init__(self, registry, db_path: str = "data/orders.db", pnl_db_path: str = "data/pnl.db"):
        self._registry = registry
        self._db_path = db_path
        self._pnl_db_path = pnl_db_path
        self._binance = None

        # ── Config from env vars ──
        self.enabled = os.getenv("PRICING_ENGINE_ENABLED", "false").lower() in ("true", "1", "yes")
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        self.update_interval = float(os.getenv("PRICING_UPDATE_INTERVAL", "60"))

        # Target margins (as decimals, e.g., 0.5 = 0.5%)
        self.target_net_margin = float(os.getenv("PRICING_TARGET_NET_MARGIN", "0.5")) / 100.0
        self.fee_buffer = float(os.getenv("PRICING_FEE_BUFFER", "0.2")) / 100.0

        # Ad IDs
        self.sell_ad_ids = [
            s.strip() for s in os.getenv("PRICING_SELL_AD_IDS", "").split(",") if s.strip()
        ]

        # Safety: minimum and maximum allowed SELL prices (EUR per USDT)
        self.min_sell_price = float(os.getenv("PRICING_MIN_SELL_PRICE", "0.840"))
        self.max_sell_price = float(os.getenv("PRICING_MAX_SELL_PRICE", "0.900"))

        # Internal state
        self._last_wac: float = 0.0
        self._last_sell_price: float = 0.0
        self._consecutive_blocked: int = 0
        self._price_update_threshold = 0.001  # Only update if price changes by >0.1%

        logger.info(
            "PricingEngine initialized: enabled=%s, dry_run=%s, interval=%ss, "
            "net_margin=%.2f%%, fee_buffer=%.2f%%, sell_ads=%s",
            self.enabled, self.dry_run, self.update_interval,
            self.target_net_margin * 100, self.fee_buffer * 100,
            self.sell_ad_ids,
        )

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    async def run_loop(self):
        """Main pricing loop — runs as a supervised task."""
        from src.core.health import task_registry

        if not self.enabled:
            logger.info("PricingEngine disabled (PRICING_ENGINE_ENABLED != true)")
            return

        logger.info("PricingEngine loop started (interval=%ss)", self.update_interval)

        while True:
            try:
                await self._pricing_tick()
                task_registry.heartbeat("pricing_engine")
            except Exception as e:
                logger.error("Pricing tick error: %s", e, exc_info=True)

            await asyncio.sleep(self.update_interval)

    async def _pricing_tick(self):
        """Single pricing cycle."""
        binance = self._get_binance()
        if not binance:
            logger.warning("PricingEngine: Binance client not available")
            return

        # Step 1: Calculate current WAC
        wac = self._get_current_wac()
        if wac is None or wac <= 0:
            logger.warning("PricingEngine: WAC unavailable or invalid (%.4f)", wac or 0)
            return

        self._last_wac = wac

        # Step 2: Calculate target SELL price
        target_sell = wac * (1.0 + self.target_net_margin + self.fee_buffer)

        # Clamp to safety bounds
        target_sell = max(self.min_sell_price, min(self.max_sell_price, target_sell))

        # Round to 3 decimal places (Binance priceScale for EUR/USDT)
        target_sell = round(target_sell, 3)

        logger.info(
            "PRICING: WAC=€%.4f → sell=€%.3f (+%.2f%%)",
            wac, target_sell, ((target_sell / wac) - 1) * 100
        )

        # Step 3: Update SELL ads (if possible)
        await self._update_sell_ads(binance, target_sell)

    # =========================================================================
    # WAC CALCULATION
    # =========================================================================

    def _get_current_wac(self) -> float | None:
        """
        Read the Weighted Average Cost of RECENT inventory only.

        Uses the last 3 days of P2P buys + Bitget fills — this reflects
        the actual cost of the USDT we're currently selling, not the
        lifetime average which is diluted by old historical trades.

        Falls back to 7 days if no data in last 3 days.
        """
        try:
            conn = sqlite3.connect(self._pnl_db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Try last 7 days first, fall back to 30 days
            for lookback_days in [3, 7]:
                # P2P BUY orders (EUR only, recent)
                c.execute("""
                    SELECT SUM(fiat_amount) as total_eur, SUM(crypto_amount) as total_usdt
                    FROM trades
                    WHERE side='buy' AND fiat_currency='EUR'
                      AND created_at >= date('now', ?)
                """, (f'-{lookback_days} days',))
                p2p = c.fetchone()
                p2p_eur = float(p2p['total_eur'] or 0)
                p2p_usdt = float(p2p['total_usdt'] or 0)

                # Bitget fills (recent)
                bg_eur = 0.0
                bg_usdt = 0.0
                try:
                    cutoff_ms = int((time.time() - lookback_days * 86400) * 1000)
                    c.execute("""
                        SELECT SUM(amount) as total_eur, SUM(net_usdt) as total_usdt
                        FROM bitget_fills
                        WHERE timestamp_ms >= ?
                    """, (cutoff_ms,))
                    bg = c.fetchone()
                    bg_eur = float(bg['total_eur'] or 0)
                    bg_usdt = float(bg['total_usdt'] or 0)
                except Exception:
                    pass  # Table may not exist

                total_eur = p2p_eur + bg_eur
                total_usdt = p2p_usdt + bg_usdt

                if total_usdt > 0:
                    wac = total_eur / total_usdt
                    logger.info(
                        "WAC (%dd): P2P %.0f EUR/%.0f USDT + Bitget %.0f EUR/%.0f USDT = €%.4f/USDT",
                        lookback_days, p2p_eur, p2p_usdt, bg_eur, bg_usdt, wac
                    )
                    conn.close()
                    return wac

            conn.close()
            logger.warning("WAC: no recent inventory data found")
            return None

        except Exception as e:
            logger.error("WAC calculation error: %s", e)
            return None

    # =========================================================================
    # SELL AD UPDATES
    # =========================================================================

    async def _update_sell_ads(self, binance, target_sell: float):
        """
        Update SELL ad prices using fixed-price API calls.

        Binance blocks ALL SELL ad updates (fixed or floating) when orders
        are in TRADING or BUYER_PAYED state (error 187049). We only attempt
        the update when no orders are in-deal.
        """
        if not self.sell_ad_ids:
            return

        # Check if price actually changed enough to warrant an update
        if self._last_sell_price > 0:
            change_pct = abs(target_sell - self._last_sell_price) / self._last_sell_price
            if change_pct < self._price_update_threshold:
                logger.debug("SELL price unchanged (€%.3f, %.3f%% change)", target_sell, change_pct * 100)
                return

        # Check if SELL ads have active in-deal orders
        can_update = await self._can_update_sell_ads(binance)
        if not can_update:
            self._consecutive_blocked += 1
            if self._consecutive_blocked % 10 == 1:  # Log every 10th block
                logger.info(
                    "SELL price update blocked (%d consecutive): orders in-deal. "
                    "Target price: €%.3f (will apply when orders clear)",
                    self._consecutive_blocked, target_sell
                )
            return

        self._consecutive_blocked = 0

        for ad_id in self.sell_ad_ids:
            if self.dry_run:
                logger.info(
                    "DRY RUN: would set SELL ad %s → €%.3f",
                    ad_id, target_sell
                )
                continue

            try:
                success = await binance.update_ad_price(ad_id, str(target_sell))
                if success:
                    logger.info("✅ SELL ad %s updated → €%.3f", ad_id, target_sell)
                    self._last_sell_price = target_sell
                else:
                    logger.error("❌ SELL ad %s update failed (187049 = orders in-deal)", ad_id)
            except Exception as e:
                logger.error("SELL ad %s update exception: %s", ad_id, e)

    async def _can_update_sell_ads(self, binance) -> bool:
        """
        Check if SELL ads can be updated.

        Binance blocks updates when orders are in TRADING or BUYER_PAYED state.
        """
        try:
            orders = await binance.get_active_orders()
            for order in orders:
                if order.side == OrderSide.SELL and order.status.value in (
                    "pending", "paid", "trading"
                ):
                    return False
            return True
        except Exception as e:
            logger.warning("Failed to check active orders: %s — assuming blocked", e)
            return False

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_binance(self):
        """Lazy-resolve Binance client."""
        if not self._binance:
            self._binance = self._registry.get_exchange_api(ExchangeId.BINANCE)
        return self._binance

    def get_status(self) -> dict[str, Any]:
        """Return current pricing state for health/API endpoints."""
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "last_wac": round(self._last_wac, 4),
            "last_sell_price": round(self._last_sell_price, 3),
            "target_net_margin": f"{self.target_net_margin * 100:.2f}%",
            "fee_buffer": f"{self.fee_buffer * 100:.2f}%",
            "consecutive_blocked": self._consecutive_blocked,
            "sell_ad_ids": self.sell_ad_ids,
        }
