"""
MXN Order Tracker
=================
SQLite-backed state machine for MXN P2P orders.
Mirrors cop_tracker.py with MXN-specific states and CURP-based dedup.

Safety tables:
- mxn_releases: P0-2 at-most-once release guard
- mxn_payout_claims: P0-3 at-most-once payout guard
- mxn_subjects: CURP → subject_id cache
- mxn_audit_log: full event history
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional

from .mxn_types import MXNOrder, MXNOrderState

logger = logging.getLogger("mxn_tracker")


class MXNOrderTracker:
    """SQLite-backed tracker for MXN orders."""

    def __init__(self, db_path: str = "data/mxn_orders.db"):
        self.db_path = db_path
        self._orders: dict[str, MXNOrder] = {}
        self._init_db()
        self._load_active_orders()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS mxn_orders (
                    binance_order_id TEXT PRIMARY KEY,
                    binance_external_id TEXT,
                    order_side TEXT DEFAULT 'SELL',
                    customer_name TEXT,
                    customer_curp TEXT,
                    customer_rfc TEXT,
                    customer_email TEXT,
                    customer_clabe TEXT,
                    amount_mxn TEXT,
                    amount_usdt TEXT,
                    facilitapay_subject_id TEXT,
                    facilitapay_tx_id TEXT,
                    dynamic_clabe TEXT,
                    state TEXT DEFAULT 'new',
                    binance_buyer_name TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    welcome_sent INTEGER DEFAULT 0,
                    seller_bank_account_id TEXT,
                    facilitapay_payout_tx_id TEXT,
                    payout_sent_at TEXT,
                    mark_paid_at TEXT,
                    mark_paid_retries INTEGER DEFAULT 0,
                    chat_messages TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS mxn_releases (
                    order_id TEXT PRIMARY KEY,
                    claimed_at TEXT DEFAULT (datetime('now')),
                    result TEXT
                );

                CREATE TABLE IF NOT EXISTS mxn_payout_claims (
                    order_id TEXT PRIMARY KEY,
                    claimed_at TEXT DEFAULT (datetime('now')),
                    result TEXT
                );

                CREATE TABLE IF NOT EXISTS mxn_subjects (
                    curp TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    name TEXT,
                    email TEXT,
                    binance_name TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS mxn_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    detail TEXT,
                    level TEXT DEFAULT 'INFO',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_mxn_audit_order
                    ON mxn_audit_log(order_id);
                CREATE INDEX IF NOT EXISTS idx_mxn_orders_state
                    ON mxn_orders(state);
            """)
            conn.commit()
            logger.info("MXN order tracker database initialized: %s", self.db_path)
        finally:
            conn.close()

    def _load_active_orders(self) -> None:
        """Load non-terminal orders into memory on startup."""
        terminal = {"completed", "cancelled", "failed"}
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM mxn_orders WHERE state NOT IN (?, ?, ?)",
                tuple(terminal)
            ).fetchall()
            for row in rows:
                order = self._row_to_order(dict(row))
                self._orders[order.binance_order_id] = order
            logger.info("Loaded %d active MXN orders from DB", len(self._orders))
        finally:
            conn.close()

    def _row_to_order(self, row: dict) -> MXNOrder:
        return MXNOrder(
            binance_order_id=row["binance_order_id"],
            binance_external_id=row.get("binance_external_id"),
            order_side=row.get("order_side", "SELL"),
            customer_name=row.get("customer_name"),
            customer_curp=row.get("customer_curp"),
            customer_rfc=row.get("customer_rfc"),
            customer_clabe=row.get("customer_clabe"),
            amount_mxn=row.get("amount_mxn"),
            amount_usdt=row.get("amount_usdt"),
            facilitapay_subject_id=row.get("facilitapay_subject_id"),
            facilitapay_tx_id=row.get("facilitapay_tx_id"),
            dynamic_clabe=row.get("dynamic_clabe"),
            state=MXNOrderState(row.get("state", "new")),
            binance_buyer_name=row.get("binance_buyer_name"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            welcome_sent=bool(row.get("welcome_sent", 0)),
            chat_messages=json.loads(row.get("chat_messages", "[]")) if row.get("chat_messages") else [],
            seller_bank_account_id=row.get("seller_bank_account_id"),
            facilitapay_payout_tx_id=row.get("facilitapay_payout_tx_id"),
            payout_sent_at=datetime.fromisoformat(row["payout_sent_at"]) if row.get("payout_sent_at") else None,
            mark_paid_at=datetime.fromisoformat(row["mark_paid_at"]) if row.get("mark_paid_at") else None,
            mark_paid_retries=row.get("mark_paid_retries", 0),
        )

    def _save(self, order: MXNOrder) -> None:
        """Persist order to DB and update in-memory cache."""
        self._orders[order.binance_order_id] = order
        conn = self._connect()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO mxn_orders
                    (binance_order_id, binance_external_id, order_side,
                     customer_name, customer_curp, customer_rfc, customer_clabe,
                     amount_mxn, amount_usdt, facilitapay_subject_id,
                     facilitapay_tx_id, dynamic_clabe, state, binance_buyer_name,
                     created_at, welcome_sent, seller_bank_account_id,
                     facilitapay_payout_tx_id, payout_sent_at, mark_paid_at,
                     mark_paid_retries, chat_messages)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order.binance_order_id, order.binance_external_id, order.order_side,
                order.customer_name, order.customer_curp, order.customer_rfc,
                order.customer_clabe, order.amount_mxn, order.amount_usdt,
                order.facilitapay_subject_id, order.facilitapay_tx_id,
                order.dynamic_clabe, order.state.value, order.binance_buyer_name,
                order.created_at.isoformat() if order.created_at else datetime.utcnow().isoformat(),
                1 if order.welcome_sent else 0, order.seller_bank_account_id,
                order.facilitapay_payout_tx_id,
                order.payout_sent_at.isoformat() if order.payout_sent_at else None,
                order.mark_paid_at.isoformat() if order.mark_paid_at else None,
                order.mark_paid_retries, json.dumps(order.chat_messages),
            ))
            conn.commit()
        finally:
            conn.close()

    # ─── ORDER MANAGEMENT ─────────────────────────────────────

    def create_order(self, binance_order_id: str, binance_external_id: str | None = None,
                     amount_mxn: str = "0", amount_usdt: str = "0",
                     binance_buyer_name: str = "",
                     order_side: str = "SELL") -> MXNOrder:
        order = MXNOrder(
            binance_order_id=binance_order_id,
            binance_external_id=binance_external_id or binance_order_id,
            order_side=order_side,
            amount_mxn=amount_mxn,
            amount_usdt=amount_usdt,
            binance_buyer_name=binance_buyer_name,
            created_at=datetime.utcnow(),
            state=MXNOrderState.NEW,
        )
        self._save(order)
        return order

    def get_order(self, order_id: str) -> MXNOrder | None:
        return self._orders.get(order_id)

    def get_all_active_orders(self) -> list[MXNOrder]:
        terminal = {MXNOrderState.COMPLETED, MXNOrderState.CANCELLED, MXNOrderState.FAILED}
        return [o for o in self._orders.values() if o.state not in terminal]

    def transition(self, order_id: str, new_state: MXNOrderState) -> None:
        order = self._orders.get(order_id)
        if not order:
            logger.warning(f"Cannot transition unknown order {order_id}")
            return
        old_state = order.state
        order.state = new_state
        self._save(order)
        logger.info(f"MXN {order_id}: {old_state.value} → {new_state.value}")

    def mark_welcome_sent(self, order_id: str) -> None:
        order = self._orders.get(order_id)
        if order:
            order.welcome_sent = True
            self._save(order)

    def add_message(self, order_id: str, message: str) -> None:
        order = self._orders.get(order_id)
        if order:
            order.chat_messages.append(message)
            self._save(order)

    def set_dynamic_clabe(self, order_id: str, subject_id: str,
                          tx_id: str, dynamic_clabe: str) -> None:
        order = self._orders.get(order_id)
        if order:
            order.facilitapay_subject_id = subject_id
            order.facilitapay_tx_id = tx_id
            order.dynamic_clabe = dynamic_clabe
            order.state = MXNOrderState.CLABE_SENT
            self._save(order)

    def set_buy_customer_info(self, order_id: str, name: str, curp: str,
                              clabe: str, rfc: str | None = None) -> None:
        order = self._orders.get(order_id)
        if order:
            order.customer_name = name
            order.customer_curp = curp
            order.customer_clabe = clabe
            order.customer_rfc = rfc
            self._save(order)

    # ─── GUARD TABLES ─────────────────────────────────────────

    def try_claim_release(self, order_id: str) -> bool:
        """P0-2: Atomic at-most-once release guard. Returns True if claimed."""
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO mxn_releases (order_id) VALUES (?)",
                (order_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def mark_release_result(self, order_id: str, success: bool) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE mxn_releases SET result = ? WHERE order_id = ?",
                ("success" if success else "failed", order_id)
            )
            conn.commit()
        finally:
            conn.close()

    def try_claim_payout(self, order_id: str) -> bool:
        """P0-3: Atomic at-most-once payout guard. Returns True if claimed."""
        conn = self._connect()
        try:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO mxn_payout_claims (order_id) VALUES (?)",
                (order_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def mark_payout_result(self, order_id: str, success: bool) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE mxn_payout_claims SET result = ? WHERE order_id = ?",
                ("success" if success else "failed", order_id)
            )
            conn.commit()
        finally:
            conn.close()

    # ─── SUBJECT CACHE ────────────────────────────────────────

    def cache_subject(self, curp: str, subject_id: str,
                      name: str | None = None, email: str | None = None) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO mxn_subjects (curp, subject_id, name, email) VALUES (?, ?, ?, ?)",
                (curp, subject_id, name, email)
            )
            conn.commit()
        finally:
            conn.close()

    def get_subject_by_curp(self, curp: str) -> str | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT subject_id FROM mxn_subjects WHERE curp = ?", (curp,)
            ).fetchone()
            return row["subject_id"] if row else None
        finally:
            conn.close()

    def check_curp_different_account(self, curp: str, binance_name: str) -> str | None:
        """Check if CURP was used by a different Binance account. Returns prev name or None."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT binance_name FROM mxn_subjects WHERE curp = ? AND binance_name IS NOT NULL",
                (curp,)
            ).fetchone()
            if row and row["binance_name"] and row["binance_name"] != binance_name:
                return row["binance_name"]
            # Update binance_name if not set
            if not row or not row.get("binance_name"):
                conn.execute(
                    "UPDATE mxn_subjects SET binance_name = ? WHERE curp = ?",
                    (binance_name, curp)
                )
                conn.commit()
            return None
        finally:
            conn.close()

    # ─── AUDIT LOG ────────────────────────────────────────────

    def log_audit(self, order_id: str, event: str, detail: str = "",
                  level: str = "INFO") -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO mxn_audit_log (order_id, event, detail, level) VALUES (?, ?, ?, ?)",
                (order_id, event, detail, level)
            )
            conn.commit()
        finally:
            conn.close()
        if level in ("ERROR", "CRITICAL"):
            logger.error(f"AUDIT [{level}] {order_id}: {event} — {detail}")
        else:
            logger.debug(f"AUDIT [{level}] {order_id}: {event} — {detail}")
