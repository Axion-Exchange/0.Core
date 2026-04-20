"""
EUR AD REBALANCER + SELL AD AUTO-TOPUP
======================================
Two features in one service:

Feature 1 (poll-based, every 5 min):
    Update Binance P2P BUY EUR ad quantity based on Januar EUR balance.
    If balance drops below minimum, disable the ad. Re-enable when it recovers.

Feature 2 (event-driven):
    When a BUY order completes (seller releases USDT to us), automatically
    top up the active SELL EUR ad with the received USDT.

    SAFETY: 5-layer guard architecture:
    1. At-most-once DB claim (prevent double-topup)
    2. Balance verification (never exceed funding wallet)
    3. Sequential processing lock (prevent race conditions)
    4. Settlement delay (wait for USDT to arrive in wallet)
    5. Dry-run gate (global DRY_RUN flag)
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any

from src.core.types import OrderSide, ExchangeId

logger = logging.getLogger(__name__)


class AdRebalancer:
    """
    Manages Binance P2P ad quantities based on real balances.

    - BUY EUR ads: sized to match Januar EUR balance (poll-based)
    - SELL EUR ads: topped up when BUY orders complete (event-driven)
    """

    def __init__(self, registry, persistence_db):
        """
        Args:
            registry: ClientRegistry with Binance + Januar clients
            persistence_db: OrderDB instance for at-most-once guard table
        """
        self._registry = registry
        self._db = persistence_db

        # Clients (resolved lazily to handle registration order)
        self._binance = None
        self._januar = None

        # Feature 2: Sequential processing lock — prevents race conditions
        # when multiple BUY orders complete simultaneously
        self._topup_lock = asyncio.Lock()

        # ── Config from env vars ──
        # Feature 1: BUY ad rebalance
        self.rebalance_interval = float(os.getenv("AD_REBALANCE_INTERVAL", "300"))
        self.eur_reserve = float(os.getenv("AD_REBALANCE_EUR_RESERVE", "50"))
        self.min_eur_active = float(os.getenv("AD_REBALANCE_MIN_EUR", "100"))
        self.update_threshold = float(os.getenv("AD_REBALANCE_UPDATE_THRESHOLD", "10"))

        # Feature 2: SELL ad monitoring + Telegram alerts
        self.target_sell_ad_id = os.getenv("SELL_AD_TARGET_AD_ID", "")  # Optional override
        self.sell_alert_threshold = float(os.getenv("SELL_AD_ALERT_THRESHOLD", "200"))
        self.topup_enabled = os.getenv("SELL_AD_TOPUP_ENABLED", "true").lower() in ("true", "1", "yes")

        # Telegram alert config
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.telegram_alert_cooldown = float(os.getenv("TELEGRAM_ALERT_COOLDOWN", "900"))  # 15 min
        self._last_sell_alert_time: float = 0

        # ── Config: Dynamic pricing tiers for BUY ads ──
        # Format: (eur_threshold, floating_ratio)
        # When EUR balance >= threshold, use that ratio. First match wins.
        # Ad NEVER goes offline — just gets less aggressive pricing.
        self.buy_price_tiers = [
            (5000, float(os.getenv("AD_PRICE_TIER_5000", "99.95"))),
            (3875, float(os.getenv("AD_PRICE_TIER_3875", "99.84"))),
            (2750, float(os.getenv("AD_PRICE_TIER_2750", "99.73"))),
            (1625, float(os.getenv("AD_PRICE_TIER_1625", "99.62"))),
            (500,  float(os.getenv("AD_PRICE_TIER_500",  "99.50"))),
            (0,    float(os.getenv("AD_PRICE_TIER_0",    "98.50"))),
        ]  # Lowest tier catches everything — ad never disabled

        # Global dry-run
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

        # Track disabled ads for re-enabling
        self._disabled_ads: set[str] = set()

        logger.info(
            "AdRebalancer initialized: interval=%ss, reserve=€%.0f, min_active=€%.0f, "
            "sell_alert_threshold=%.0f, telegram=%s, dry_run=%s, price_tiers=%s",
            self.rebalance_interval, self.eur_reserve, self.min_eur_active,
            self.sell_alert_threshold, bool(self.telegram_bot_token), self.dry_run,
            [(t, r) for t, r in self.buy_price_tiers],
        )

    def _get_binance(self):
        """Lazy-resolve Binance client."""
        if not self._binance:
            self._binance = self._registry.get_exchange_api(ExchangeId.BINANCE)
        return self._binance

    def _get_januar(self):
        """Lazy-resolve Januar client."""
        if not self._januar:
            self._januar = self._registry.get_bank("januar")
        return self._januar

    # =========================================================================
    # FEATURE 1: BUY EUR AD DYNAMIC PRICING (poll-based)
    # =========================================================================

    async def run_loop(self):
        """
        Main poll loop — runs as a supervised task.
        Every N seconds, checks Januar EUR balance and updates BUY ad quantity.
        """
        from src.core.health import task_registry

        logger.info("Ad Rebalancer loop started (interval=%ss)", self.rebalance_interval)

        while True:
            try:
                await self._rebalance_buy_ads()
                # Also check if SELL ad can be topped up from excess funding USDT
                if self.topup_enabled:
                    await self._rebalance_sell_ads()
                task_registry.heartbeat("ad_topup")  # Must match task name in main.py
            except Exception as e:
                logger.error("Ad rebalance error: %s", e, exc_info=True)

            await asyncio.sleep(self.rebalance_interval)

    def _get_target_ratio(self, usable_eur: float) -> float:
        """
        Determine the target floating price ratio based on EUR balance.
        Returns the ratio for the first tier where usable_eur >= threshold.
        Always returns a value — ad never disabled.
        """
        for threshold, ratio in self.buy_price_tiers:
            if usable_eur >= threshold:
                return ratio
        # Fallback: lowest configured tier
        return self.buy_price_tiers[-1][1]

    async def _rebalance_buy_ads(self):
        """
        DYNAMIC PRICING for BUY EUR ads based on Januar EUR balance.

        Since Binance API cannot change BUY ad surplus quantity, we instead
        adjust the floating price ratio to control order flow:
          - High EUR → aggressive price (attract more sellers)
          - Low EUR  → conservative price (slow down orders)
          - Critical → disable the ad entirely

        Ad capacity should be set high (e.g. 500k) manually on Binance.
        """
        januar = self._get_januar()
        binance = self._get_binance()

        if not januar or not binance:
            logger.warning("Rebalance skipped: missing Januar or Binance client")
            return

        # Step 1: Get EUR balance
        eur_balance = await self._get_januar_eur_balance()
        if eur_balance is None:
            logger.warning("Rebalance skipped: failed to fetch Januar balance")
            return

        logger.info("BUY rebalance: Januar EUR balance = €%.2f", eur_balance)

        # Step 2: Get our ads
        try:
            ads = await binance.get_ads()
        except Exception as e:
            logger.error("Failed to fetch ads: %s", e)
            return

        # Filter: BUY side + EUR + (active OR disabled by us)
        buy_eur_ads = [
            ad for ad in ads
            if ad.side == OrderSide.BUY
            and str(ad.fiat_currency).upper().replace("CURRENCY.", "") == "EUR"
            and (ad.active or ad.external_id in self._disabled_ads)
        ]

        if not buy_eur_ads:
            logger.debug("No BUY EUR ads found — nothing to rebalance")
            return

        # Step 3: Calculate usable EUR and target price tier
        usable_eur = max(0, eur_balance - self.eur_reserve)
        target_ratio = self._get_target_ratio(usable_eur)

        for ad in buy_eur_ads:
            ad_id = ad.external_id
            current_ratio = float(ad.raw.get("priceFloatingRatio", 0)) if ad.raw else 0

            # ADJUST PRICE if ratio changed
            if abs(current_ratio - target_ratio) >= 0.01:
                logger.info(
                    "BUY PRICE: Ad %s %.2f%% → %.2f%% (EUR=€%.2f) → %s",
                    ad_id, current_ratio, target_ratio, usable_eur,
                    "UPDATING" if not self.dry_run else "WOULD UPDATE (dry run)",
                )
                if not self.dry_run:
                    success = await binance.update_ad_price(ad_id, target_ratio)
                    if success:
                        logger.info("✅ BUY AD PRICE: ad=%s, %.2f%% → %.2f%%", ad_id, current_ratio, target_ratio)
                    else:
                        logger.error("Failed to update ad %s price", ad_id)
                else:
                    logger.info("DRY RUN: would set ad %s price to %.2f%%", ad_id, target_ratio)
            else:
                logger.debug(
                    "BUY rebalance: Ad %s — price %.2f%% at target, no update",
                    ad_id, current_ratio,
                )

    async def _get_januar_eur_balance(self) -> float | None:
        """Fetch EUR balance from Januar. Returns None on failure."""
        januar = self._get_januar()
        if not januar:
            return None
        try:
            balances = await januar.get_balances()
            for bal in balances:
                # UnifiedBalance.asset is a string like "EUR"
                if bal.asset.upper() == "EUR":
                    return float(bal.available)
            return 0.0  # No EUR balance found but API worked
        except Exception as e:
            logger.error("Failed to fetch Januar balance: %s", e)
            return None

    # =========================================================================
    # FEATURE 2: SELL AD AUTO-TOPUP (event-driven)
    # =========================================================================

    async def on_buy_order_completed(self, order_id: str, usdt_amount: float):
        """
        Called when a BUY order completes (seller released USDT to us).
        Automatically tops up the active SELL EUR ad.

        SAFETY: 5-layer guard architecture (see module docstring).

        Args:
            order_id: External order ID of the completed BUY order
            usdt_amount: Amount of USDT received from this order
        """
        if not self.topup_enabled:
            logger.debug("SELL topup disabled — skipping for order %s", order_id[-8:])
            return

        logger.info(
            "SELL AD TOPUP triggered: order=%s, usdt=%.2f",
            order_id[-8:], usdt_amount,
        )

        # GUARD 3: Sequential processing — only one topup at a time
        async with self._topup_lock:
            await self._execute_topup(order_id, usdt_amount)

    async def _execute_topup(self, order_id: str, usdt_amount: float):
        """
        Execute the SELL ad topup with all safety guards.

        Must be called under self._topup_lock.
        """
        binance = self._get_binance()
        if not binance:
            logger.error("SELL topup: Binance client not available")
            return

        # ── GUARD 1: At-most-once DB claim ──
        if not self._db.try_claim_sell_topup(order_id):
            logger.warning(
                "SELL topup GUARD: order %s already claimed — skipping (prevents double-topup)",
                order_id[-8:],
            )
            return

        # ── GUARD 4: Settlement delay ──
        logger.info(
            "SELL topup: waiting %.0fs for USDT to settle (order %s)",
            self.settle_delay, order_id[-8:],
        )
        await asyncio.sleep(self.settle_delay)

        # ── GUARD 2: Balance verification ──
        try:
            funding_balances = await binance.get_funding_balance("USDT")
            funding_usdt = funding_balances.get("USDT", 0.0)
        except Exception as e:
            logger.error("SELL topup: failed to fetch funding balance: %s", e)
            self._db.record_sell_topup(
                order_id, "", usdt_amount, 0, 0, 0, success=False, error=str(e)
            )
            return

        if funding_usdt <= 0:
            logger.warning(
                "SELL topup: funding USDT balance = %.2f — USDT may not have arrived yet "
                "(order %s, expected +%.2f)",
                funding_usdt, order_id[-8:], usdt_amount,
            )
            self._db.record_sell_topup(
                order_id, "", usdt_amount, 0, 0, funding_usdt,
                success=False, error="zero_funding_balance",
            )
            return

        # Find the SELL EUR ad to top up
        sell_ad = await self._get_sell_eur_ad()
        if not sell_ad:
            logger.warning("SELL topup: no active SELL EUR ad found — skipping")
            self._db.record_sell_topup(
                order_id, "", usdt_amount, 0, 0, funding_usdt,
                success=False, error="no_sell_ad_found",
            )
            return

        ad_id = sell_ad.external_id
        current_qty = float(sell_ad.available_amount) if sell_ad.available_amount else 0

        # Calculate new quantity — cap at actual funding balance
        new_qty = current_qty + usdt_amount
        if new_qty > funding_usdt:
            logger.warning(
                "SELL topup: capping new_qty from %.2f to funding balance %.2f "
                "(prevents over-allocation)",
                new_qty, funding_usdt,
            )
            new_qty = funding_usdt

        # ── GUARD 5: Dry-run gate ──
        if self.dry_run:
            logger.info(
                "DRY RUN SELL TOPUP: order=%s, ad=%s, +%.2f USDT, "
                "current=%.2f → target=%.2f, funding=%.2f",
                order_id[-8:], ad_id, usdt_amount,
                current_qty, new_qty, funding_usdt,
            )
            self._db.record_sell_topup(
                order_id, ad_id, usdt_amount, current_qty, new_qty, funding_usdt,
                success=True, error="dry_run",
            )
            return

        # ── Execute the update with decremental retry ──
        final_qty, success = await self._update_ad_quantity_with_retry(
            binance, ad_id, new_qty
        )

        if success:
            logger.info(
                "✅ SELL AD TOPPED UP: order=%s, ad=%s, +%.2f USDT "
                "(%.2f → %.2f), funding=%.2f",
                order_id[-8:], ad_id, usdt_amount,
                current_qty, final_qty, funding_usdt,
            )
        else:
            logger.error(
                "SELL topup: all retries exhausted — order=%s, ad=%s, "
                "tried %.2f down to %.2f",
                order_id[-8:], ad_id, new_qty, final_qty,
            )

        # Record outcome for audit
        self._db.record_sell_topup(
            order_id, ad_id, usdt_amount, current_qty, final_qty, funding_usdt,
            success=success,
        )

    async def _get_sell_eur_ad(self):
        """
        Find the active SELL EUR ad to top up.

        Priority:
        1. SELL_AD_TARGET_AD_ID env var (explicit override)
        2. First active SELL EUR ad from get_ads()
        """
        binance = self._get_binance()
        if not binance:
            return None

        try:
            ads = await binance.get_ads()
        except Exception as e:
            logger.error("Failed to fetch ads for SELL lookup: %s", e)
            return None

        # Filter: SELL side + EUR currency + active
        sell_eur_ads = [
            ad for ad in ads
            if ad.side == OrderSide.SELL
            and str(ad.fiat_currency).upper().replace("CURRENCY.", "") == "EUR"
            and ad.active
        ]

        if not sell_eur_ads:
            return None

        # If explicit target set, find it
        if self.target_sell_ad_id:
            for ad in sell_eur_ads:
                if ad.external_id == self.target_sell_ad_id:
                    return ad
            logger.warning(
                "SELL_AD_TARGET_AD_ID=%s not found among active SELL EUR ads",
                self.target_sell_ad_id,
            )

        # Default: first active SELL EUR ad
        return sell_eur_ads[0]

    # =========================================================================
    # SHARED: Decremental retry for ad quantity updates
    # =========================================================================

    async def _update_ad_quantity_with_retry(
        self, binance, ad_id: str, target_qty: float
    ) -> tuple[float, bool]:
        """
        Try to update ad quantity, stepping down by `qty_step_down` on failure.

        Some USDT may be locked in escrow for active orders. Binance rejects
        setting the ad quantity higher than available (unlocked) balance.
        This method retries with progressively lower quantities:
            1000 → 990 → 980 → 970 ... until success or qty drops below step size.

        Returns:
            (final_qty_attempted, success)
        """
        attempt_qty = target_qty
        step = self.qty_step_down

        while attempt_qty >= step:
            try:
                success = await binance.update_ad_quantity(ad_id, attempt_qty)
                if success:
                    if attempt_qty < target_qty:
                        logger.info(
                            "Ad %s updated at %.2f (stepped down from %.2f due to locked USDT)",
                            ad_id, attempt_qty, target_qty,
                        )
                    return attempt_qty, True
                else:
                    # API returned False (rejected) — step down
                    logger.warning(
                        "Ad %s rejected qty=%.2f — stepping down by %.0f (locked USDT?)",
                        ad_id, attempt_qty, step,
                    )
                    attempt_qty -= step
            except Exception as e:
                logger.warning(
                    "Ad %s update failed at qty=%.2f: %s — stepping down by %.0f",
                    ad_id, attempt_qty, e, step,
                )
                attempt_qty -= step

        logger.error(
            "Ad %s: all decremental retries exhausted (target=%.2f, step=%.0f)",
            ad_id, target_qty, step,
        )
        return attempt_qty + step, False  # Return last attempted qty

    # =========================================================================
    # FEATURE 3: SELL AD PERIODIC REBALANCE (poll-based)
    # =========================================================================

    async def _rebalance_sell_ads(self):
        """
        Monitor SELL EUR ad surplus and send Telegram alerts when low.

        NOTE: Binance P2P API's totalTradableAmount update returns success
        but does NOT actually change the ad surplus. Manual topup via
        Binance app/website is required. This method monitors and alerts only.
        """
        binance = self._get_binance()
        if not binance:
            return

        # Find SELL ad
        sell_ad = await self._get_sell_eur_ad()
        if not sell_ad:
            logger.debug("SELL monitor: no active SELL EUR ad found")
            return

        raw = sell_ad.raw or {}
        surplus = float(raw.get("surplusAmount", 0))

        # Get funding balance for context
        try:
            funding_balances = await binance.get_funding_balance("USDT")
            funding_usdt = funding_balances.get("USDT", 0.0)
        except Exception:
            funding_usdt = 0.0

        logger.info(
            "SELL monitor: surplus=%.2f USDT, funding_free=%.2f USDT",
            surplus, funding_usdt,
        )

        # Alert if surplus is below threshold
        if surplus < self.sell_alert_threshold:
            await self._send_sell_alert(surplus, funding_usdt)

    async def _send_sell_alert(self, surplus: float, funding_free: float):
        """Send Telegram alert when SELL ad surplus is low. Respects cooldown."""
        now = time.time()
        elapsed = now - self._last_sell_alert_time
        if elapsed < self.telegram_alert_cooldown:
            logger.debug(
                "SELL alert suppressed: %.0fs remaining in cooldown",
                self.telegram_alert_cooldown - elapsed,
            )
            return

        emoji = "🔴" if surplus < 50 else "🟡"
        msg = (
            f"{emoji} *SELL AD LOW SURPLUS*\n\n"
            f"Surplus: `{surplus:.2f} USDT`\n"
            f"Funding free: `{funding_free:.2f} USDT`\n"
            f"Threshold: `{self.sell_alert_threshold:.0f} USDT`\n\n"
            f"⚠️ Manual topup required via Binance app"
        )

        sent = await self._send_telegram(msg)
        if sent:
            self._last_sell_alert_time = now
            logger.warning(
                "SELL ALERT SENT: surplus=%.2f < threshold=%.0f",
                surplus, self.sell_alert_threshold,
            )

    async def _send_telegram(self, message: str) -> bool:
        """Send a message via Telegram Bot API."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing)")
            return False

        import httpx

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    logger.info("Telegram alert sent successfully")
                    return True
                else:
                    logger.error("Telegram API error: %d %s", resp.status_code, resp.text[:200])
                    return False
        except Exception as e:
            logger.error("Telegram send failed: %s", e)
            return False
