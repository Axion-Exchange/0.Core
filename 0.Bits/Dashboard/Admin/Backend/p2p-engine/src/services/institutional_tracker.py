"""
INSTITUTIONAL TRACKER
=====================
Tracks EUR→USDC (Januar) → USDC→USDT (Binance) flow
and creates synthetic FIFO BUY lots for P&L tracking.

Pipeline runs every 5 min:
  1. Poll Januar for USDC outgoing payments → save as pending
  2. Poll Binance for USDC deposits → fuzzy-match to Januar
  3. Poll Binance spot + convert trades (USDC→USDT) → match to deposit
  4. Create FIFO BUY lot when fully matched
"""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger("institutional")

# Match tolerance: Januar outgoing vs Binance deposit
AMOUNT_TOLERANCE_PCT = 0.02   # 2% (network fees)
TIME_WINDOW_SECONDS = 1800    # 30 min

# Convert match: Binance deposit vs spot/convert trade
CONVERT_TOLERANCE_PCT = 0.005  # 0.5%
CONVERT_TIME_WINDOW = 3600     # 1 hour


@dataclass
class InstitutionalBuy:
    """A tracked institutional EUR→USDC→USDT buy."""
    id: str
    januar_tx_id: str
    eur_amount: Decimal
    usdc_sent: Decimal
    usdc_received: Decimal = Decimal("0")
    usdt_amount: Decimal = Decimal("0")
    binance_deposit_id: str = ""
    binance_trade_id: str = ""
    eur_per_usdt: Decimal = Decimal("0")
    status: str = "pending_deposit"
    source: str = ""  # "spot" or "convert"
    created_at: datetime = field(default_factory=datetime.now)
    matched_at: datetime | None = None


class InstitutionalTracker:
    """
    Tracks institutional buys: EUR→USDC via Januar → USDC deposit to Binance
    → USDC→USDT via spot/convert → synthetic FIFO BUY lot.
    """

    def __init__(self, db_path: str = "/data/PearV2/data/institutional.db"):
        self.db_path = Path(db_path)
        self._init_table()
        self._last_poll: datetime | None = None
        self._poll_cooldown = 300  # 5 min

    def _init_table(self):
        """Create institutional_buys table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS institutional_buys (
                    id TEXT PRIMARY KEY,
                    januar_tx_id TEXT UNIQUE NOT NULL,
                    eur_amount TEXT NOT NULL,
                    usdc_sent TEXT NOT NULL,
                    usdc_received TEXT DEFAULT '0',
                    usdt_amount TEXT DEFAULT '0',
                    binance_deposit_id TEXT,
                    binance_trade_id TEXT,
                    eur_per_usdt TEXT DEFAULT '0',
                    status TEXT DEFAULT 'pending_deposit',
                    source TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    matched_at TEXT
                )
            """)
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_inst_januar_tx
                ON institutional_buys(januar_tx_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inst_status
                ON institutional_buys(status)
            """)

    # =========================================================================
    # MAIN PIPELINE
    # =========================================================================

    async def run_pipeline(self, force: bool = False) -> int:
        """
        Run the full matching pipeline.
        Returns number of newly matched buys.
        """
        if not force and self._last_poll:
            elapsed = (datetime.now() - self._last_poll).total_seconds()
            if elapsed < self._poll_cooldown:
                return 0

        from src.core.registry import registry

        binance = registry.get_exchange_api("binance")
        bank = registry.get_bank("januar")

        if not binance or not bank:
            logger.warning("Missing Binance or Januar client for institutional tracking")
            return 0

        matched = 0

        try:
            # Step 1: Discover new Januar USDC outgoing payments
            new_januar = await self._poll_januar_usdc(bank)
            if new_januar:
                logger.info("Institutional: Found %d new Januar USDC outflows", new_januar)

            # Step 2: Match pending deposits to Binance USDC deposits
            deposit_matches = await self._match_deposits(binance)
            if deposit_matches:
                logger.info("Institutional: Matched %d deposits", deposit_matches)

            # Step 3: Match deposits to spot/convert trades
            convert_matches = await self._match_conversions(binance)
            if convert_matches:
                logger.info("Institutional: Matched %d conversions", convert_matches)
                matched = convert_matches

        except Exception as e:
            logger.error("Institutional pipeline error: %s", e, exc_info=True)

        self._last_poll = datetime.now()
        return matched

    # =========================================================================
    # STEP 1: POLL JANUAR FOR USDC OUTFLOWS
    # =========================================================================

    async def _poll_januar_usdc(self, bank) -> int:
        """Find new USDC outgoing payments from Januar."""
        try:
            outgoing = await bank.get_outgoing_payments(currency="USDC")
        except Exception as e:
            logger.error("Januar USDC poll error: %s", e)
            return 0

        new_count = 0
        for payment in outgoing:
            if not payment.completed_at:
                continue  # Skip pending

            jan_tx_id = payment.external_id
            if not jan_tx_id or self._januar_tx_exists(jan_tx_id):
                continue

            # For USDC outgoing, the payment amount = USDC sent
            # The EUR amount is in the raw data (original purchase)
            raw = payment.raw or {}
            usdc_amount = Decimal(str(payment.amount))

            # Try to find the EUR cost from the raw transaction
            # Januar stores the conversion details in the raw data
            eur_amount = Decimal(str(raw.get("fiatAmount", raw.get("eurAmount", "0"))))
            if eur_amount <= 0:
                # Fallback: check if there's a rate field
                rate = raw.get("rate", raw.get("exchangeRate", "0"))
                if rate and float(rate) > 0:
                    eur_amount = usdc_amount * Decimal(str(rate))

            if eur_amount <= 0:
                logger.warning(
                    "Institutional: Januar tx %s has no EUR amount in raw data, skipping. Raw keys: %s",
                    jan_tx_id, list(raw.keys())
                )
                continue

            buy = InstitutionalBuy(
                id=f"inst_{uuid4().hex[:12]}",
                januar_tx_id=jan_tx_id,
                eur_amount=eur_amount,
                usdc_sent=usdc_amount,
                created_at=payment.completed_at or datetime.now(),
            )
            self._save_buy(buy)
            new_count += 1
            logger.info(
                "Institutional: New Januar USDC outflow: %s USDC for €%s (tx %s)",
                usdc_amount, eur_amount, jan_tx_id[:16]
            )

        return new_count

    # =========================================================================
    # STEP 2: MATCH JANUAR → BINANCE DEPOSIT
    # =========================================================================

    async def _match_deposits(self, binance) -> int:
        """Match pending Januar outflows to Binance USDC deposits."""
        pending = self._get_by_status("pending_deposit")
        if not pending:
            return 0

        try:
            deposits = await binance.get_deposit_history(coin="USDC", status=1)
        except Exception as e:
            logger.error("Binance deposit history error: %s", e)
            return 0

        matched = 0
        used_deposit_ids = set(self._get_used_deposit_ids())

        for buy in pending:
            for dep in deposits:
                dep_id = str(dep.get("txId", dep.get("id", "")))
                if dep_id in used_deposit_ids:
                    continue

                dep_amount = Decimal(str(dep.get("amount", "0")))
                dep_time = datetime.fromtimestamp(
                    dep.get("completeTime", dep.get("insertTime", 0)) / 1000
                ) if dep.get("completeTime") or dep.get("insertTime") else None

                if not dep_time:
                    continue

                # Fuzzy match: amount within tolerance + time window
                if self._amounts_match(buy.usdc_sent, dep_amount, AMOUNT_TOLERANCE_PCT):
                    time_diff = abs((dep_time - buy.created_at).total_seconds())
                    if time_diff <= TIME_WINDOW_SECONDS:
                        # Match found!
                        buy.usdc_received = dep_amount
                        buy.binance_deposit_id = dep_id
                        buy.status = "pending_convert"
                        self._update_buy(buy)
                        used_deposit_ids.add(dep_id)
                        matched += 1
                        logger.info(
                            "Institutional: Matched Januar %s USDC → Binance deposit %s USDC (fee: %s)",
                            buy.usdc_sent, dep_amount, buy.usdc_sent - dep_amount
                        )
                        break

        return matched

    # =========================================================================
    # STEP 3: MATCH DEPOSIT → SPOT/CONVERT TRADE
    # =========================================================================

    async def _match_conversions(self, binance) -> int:
        """Match pending_convert buys to USDC→USDT spot or convert trades."""
        pending = self._get_by_status("pending_convert")
        if not pending:
            return 0

        import time
        now_ms = int(time.time() * 1000)
        lookback_ms = now_ms - (86400 * 7 * 1000)  # 7 days

        # Fetch both convert and spot histories
        convert_trades = []
        spot_trades = []
        try:
            convert_trades = await binance.get_convert_history(
                start_time=lookback_ms, end_time=now_ms
            )
        except Exception as e:
            logger.warning("Convert history fetch error: %s", e)

        try:
            spot_trades = await binance.get_spot_trades(
                symbol="USDCUSDT",
                start_time=lookback_ms,
                end_time=now_ms,
                limit=200
            )
        except Exception as e:
            logger.warning("Spot trades fetch error: %s", e)

        # Normalize all trades into a unified list
        all_trades = []

        for ct in convert_trades:
            from_asset = ct.get("fromAsset", "")
            to_asset = ct.get("toAsset", "")
            if from_asset == "USDC" and to_asset == "USDT":
                all_trades.append({
                    "trade_id": str(ct.get("quoteId", ct.get("orderId", ""))),
                    "usdc_amount": Decimal(str(ct.get("fromAmount", "0"))),
                    "usdt_amount": Decimal(str(ct.get("toAmount", "0"))),
                    "timestamp": ct.get("createTime", 0),
                    "source": "convert",
                })

        for st in spot_trades:
            # For USDCUSDT pair: if isBuyer=False, you sold USDC for USDT
            if not st.get("isBuyer", True):
                all_trades.append({
                    "trade_id": str(st.get("id", "")),
                    "usdc_amount": Decimal(str(st.get("qty", "0"))),
                    "usdt_amount": Decimal(str(st.get("quoteQty", "0"))),
                    "timestamp": st.get("time", 0),
                    "source": "spot",
                })

        if not all_trades:
            return 0

        used_trade_ids = set(self._get_used_trade_ids())
        matched = 0

        for buy in pending:
            for trade in all_trades:
                tid = trade["trade_id"]
                if tid in used_trade_ids:
                    continue

                # Match: USDC amount within tolerance
                if self._amounts_match(buy.usdc_received, trade["usdc_amount"], CONVERT_TOLERANCE_PCT):
                    trade_time = datetime.fromtimestamp(trade["timestamp"] / 1000) if trade["timestamp"] else None
                    if trade_time:
                        time_diff = abs((trade_time - buy.created_at).total_seconds())
                        if time_diff > CONVERT_TIME_WINDOW * 24:  # generous: 24 hours
                            continue

                    # Fully matched!
                    buy.usdt_amount = trade["usdt_amount"]
                    buy.binance_trade_id = tid
                    buy.source = trade["source"]
                    buy.status = "matched"
                    buy.matched_at = datetime.now()

                    # Calculate effective cost basis
                    if buy.usdt_amount > 0:
                        buy.eur_per_usdt = (buy.eur_amount / buy.usdt_amount).quantize(
                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                        )

                    self._update_buy(buy)
                    used_trade_ids.add(tid)
                    matched += 1
                    logger.info(
                        "Institutional: FULLY MATCHED — €%s → %s USDT @ €%s/USDT (via %s, trade %s)",
                        buy.eur_amount, buy.usdt_amount, buy.eur_per_usdt,
                        buy.source, tid[:16]
                    )
                    break

        return matched

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _amounts_match(a: Decimal, b: Decimal, tolerance: float) -> bool:
        """Check if two amounts are within tolerance %."""
        if a == 0 or b == 0:
            return False
        diff = abs(a - b) / max(a, b)
        return float(diff) <= tolerance

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def _januar_tx_exists(self, tx_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM institutional_buys WHERE januar_tx_id = ?", (tx_id,)
            ).fetchone()
            return row is not None

    def _save_buy(self, buy: InstitutionalBuy):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO institutional_buys
                (id, januar_tx_id, eur_amount, usdc_sent, usdc_received,
                 usdt_amount, binance_deposit_id, binance_trade_id,
                 eur_per_usdt, status, source, created_at, matched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                buy.id, buy.januar_tx_id,
                str(buy.eur_amount), str(buy.usdc_sent), str(buy.usdc_received),
                str(buy.usdt_amount), buy.binance_deposit_id, buy.binance_trade_id,
                str(buy.eur_per_usdt), buy.status, buy.source,
                buy.created_at.isoformat(),
                buy.matched_at.isoformat() if buy.matched_at else None,
            ))

    def _update_buy(self, buy: InstitutionalBuy):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE institutional_buys SET
                    usdc_received = ?, usdt_amount = ?,
                    binance_deposit_id = ?, binance_trade_id = ?,
                    eur_per_usdt = ?, status = ?, source = ?,
                    matched_at = ?
                WHERE id = ?
            """, (
                str(buy.usdc_received), str(buy.usdt_amount),
                buy.binance_deposit_id, buy.binance_trade_id,
                str(buy.eur_per_usdt), buy.status, buy.source,
                buy.matched_at.isoformat() if buy.matched_at else None,
                buy.id,
            ))

    def _get_by_status(self, status: str) -> list[InstitutionalBuy]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM institutional_buys WHERE status = ? ORDER BY created_at",
                (status,)
            ).fetchall()
        return [self._row_to_buy(r) for r in rows]

    def _get_used_deposit_ids(self) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT binance_deposit_id FROM institutional_buys WHERE binance_deposit_id IS NOT NULL AND binance_deposit_id != ''"
            ).fetchall()
        return [r[0] for r in rows]

    def _get_used_trade_ids(self) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT binance_trade_id FROM institutional_buys WHERE binance_trade_id IS NOT NULL AND binance_trade_id != ''"
            ).fetchall()
        return [r[0] for r in rows]

    def get_matched_buys(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[InstitutionalBuy]:
        """Get all fully matched institutional buys in a date range."""
        query = "SELECT * FROM institutional_buys WHERE status = 'matched'"
        params: list = []
        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date.isoformat())
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date.isoformat())
        query += " ORDER BY created_at ASC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_buy(r) for r in rows]

    def get_pending_count(self) -> dict[str, int]:
        """Get counts by status."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM institutional_buys GROUP BY status"
            ).fetchall()
        return {r[0]: r[1] for r in rows}

    @staticmethod
    def _row_to_buy(row) -> InstitutionalBuy:
        return InstitutionalBuy(
            id=row["id"],
            januar_tx_id=row["januar_tx_id"],
            eur_amount=Decimal(row["eur_amount"]),
            usdc_sent=Decimal(row["usdc_sent"]),
            usdc_received=Decimal(row["usdc_received"] or "0"),
            usdt_amount=Decimal(row["usdt_amount"] or "0"),
            binance_deposit_id=row["binance_deposit_id"] or "",
            binance_trade_id=row["binance_trade_id"] or "",
            eur_per_usdt=Decimal(row["eur_per_usdt"] or "0"),
            status=row["status"],
            source=row["source"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            matched_at=datetime.fromisoformat(row["matched_at"]) if row["matched_at"] else None,
        )


# Singleton
_tracker: InstitutionalTracker | None = None

def get_institutional_tracker() -> InstitutionalTracker:
    global _tracker
    if _tracker is None:
        _tracker = InstitutionalTracker()
    return _tracker
