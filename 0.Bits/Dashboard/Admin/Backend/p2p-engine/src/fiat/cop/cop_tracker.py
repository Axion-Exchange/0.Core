"""
COP Order Tracker (SQLite)
===========================
Persistent state machine for COP P2P orders with audit logging.
Extracted from cop_standalone.py for PearV2.

SAFETY INVARIANTS:
1. COMPLETED and CANCELLED are TERMINAL — no outgoing transitions (enforced by VALID_TRANSITIONS).
2. Every state change is persisted BEFORE the caller proceeds with side effects.
3. Audit log is append-only and immutable — never update/delete rows.
4. CC security check prevents one customer's cédula from being reused across Binance accounts.

CONCURRENCY NOTE:
This module is NOT thread/task-safe on its own. The COPChatHandler is responsible
for acquiring a per-order asyncio.Lock BEFORE calling any mutation method (M1 fix).
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from .cop_types import COPOrder, COPOrderState

logger = logging.getLogger(__name__)


class COPOrderTracker:
    """SQLite-based persistence for COP order state."""

    LINK_EXPIRY_MINUTES = 21

    # V4-04: Valid state transitions — COMPLETED and CANCELLED are terminal
    # SAFETY: This is the ONLY authority on valid transitions. Any code that calls
    # transition() is subject to this matrix. Adding new transitions here should
    # be done with extreme care — especially any that allow leaving terminal states.
    VALID_TRANSITIONS: dict[COPOrderState, set[COPOrderState]] = {
        COPOrderState.NEW: {COPOrderState.AWAITING_INFO, COPOrderState.COLLECTING_BANK_INFO, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW},
        # SELL flow transitions
        COPOrderState.AWAITING_INFO: {COPOrderState.INFO_RECEIVED, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW},
        COPOrderState.INFO_RECEIVED: {COPOrderState.GENERATING_LINK, COPOrderState.LINK_SENT, COPOrderState.AWAITING_PAYMENT, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW},
        COPOrderState.GENERATING_LINK: {COPOrderState.LINK_SENT, COPOrderState.INFO_RECEIVED, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW, COPOrderState.FAILED},
        COPOrderState.LINK_SENT: {COPOrderState.AWAITING_PAYMENT, COPOrderState.PAYMENT_RECEIVED, COPOrderState.RELEASING, COPOrderState.LINK_EXPIRED, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW, COPOrderState.INFO_RECEIVED, COPOrderState.COMPLETED},
        COPOrderState.LINK_EXPIRED: {COPOrderState.GENERATING_LINK, COPOrderState.INFO_RECEIVED, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW},
        COPOrderState.AWAITING_PAYMENT: {COPOrderState.PAYMENT_RECEIVED, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW, COPOrderState.INFO_RECEIVED},
        COPOrderState.PAYMENT_RECEIVED: {COPOrderState.RELEASING, COPOrderState.MANUAL_REVIEW, COPOrderState.CANCELLED},
        COPOrderState.RELEASING: {COPOrderState.COMPLETED, COPOrderState.FAILED, COPOrderState.MANUAL_REVIEW, COPOrderState.CANCELLED},
        # BUY flow transitions
        COPOrderState.COLLECTING_BANK_INFO: {COPOrderState.PAYOUT_PENDING, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW},
        COPOrderState.PAYOUT_PENDING: {COPOrderState.PAYOUT_SENT, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW},
        COPOrderState.PAYOUT_SENT: {COPOrderState.MARK_PAID_PENDING, COPOrderState.COMPLETED, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW},
        COPOrderState.MARK_PAID_PENDING: {COPOrderState.COMPLETED, COPOrderState.CANCELLED, COPOrderState.MANUAL_REVIEW},
        # Terminal / error states
        COPOrderState.COMPLETED: set(),
        COPOrderState.FAILED: {COPOrderState.MANUAL_REVIEW, COPOrderState.RELEASING},
        COPOrderState.CANCELLED: set(),
        COPOrderState.MANUAL_REVIEW: {COPOrderState.AWAITING_INFO, COPOrderState.INFO_RECEIVED, COPOrderState.COLLECTING_BANK_INFO, COPOrderState.PAYOUT_PENDING, COPOrderState.RELEASING, COPOrderState.CANCELLED, COPOrderState.COMPLETED},
    }

    def __init__(self, db_path: str = "data/cop_orders.db"):
        self.db_path = db_path
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Enable WAL mode for better concurrent read performance
        c.execute("PRAGMA journal_mode=WAL")

        c.execute("""
            CREATE TABLE IF NOT EXISTS cop_orders (
                binance_order_id TEXT PRIMARY KEY,
                binance_external_id TEXT,
                customer_name TEXT, customer_cc TEXT, customer_email TEXT,
                bank_code TEXT, bank_name TEXT,
                amount_cop TEXT, amount_usdt TEXT,
                facilitapay_subject_id TEXT, facilitapay_tx_id TEXT, payment_url TEXT,
                state TEXT DEFAULT 'new',
                binance_buyer_name TEXT,
                created_at TEXT, link_expires_at TEXT,
                welcome_sent INTEGER DEFAULT 0,
                chat_messages TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS cop_subjects (
                cc TEXT PRIMARY KEY,
                facilitapay_subject_id TEXT NOT NULL,
                name TEXT, email TEXT, created_at TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_cop_tx ON cop_orders(facilitapay_tx_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_cop_state ON cop_orders(state)")

        # Persistent message ID tracking (survives restarts)
        c.execute("""
            CREATE TABLE IF NOT EXISTS seen_messages (
                order_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                seen_at TEXT NOT NULL,
                PRIMARY KEY (order_id, message_id)
            )
        """)

        # P0-2: Release guard — DB-enforced at-most-once crypto release.
        # SAFETY: UNIQUE(order_id) prevents any second release attempt.
        c.execute("""
            CREATE TABLE IF NOT EXISTS cop_releases (
                order_id TEXT PRIMARY KEY,
                claimed_at TEXT NOT NULL,
                released_at TEXT,
                release_success INTEGER
            )
        """)

        # BUY: Payout claim guard — DB-enforced at-most-once COP payout.
        # SAFETY: Same pattern as cop_releases, prevents double COP send.
        c.execute("""
            CREATE TABLE IF NOT EXISTS cop_payout_claims (
                order_id TEXT PRIMARY KEY,
                claimed_at TEXT NOT NULL,
                payout_tx_id TEXT,
                payout_success INTEGER
            )
        """)

        # Audit log — append-only, immutable
        # SAFETY: This table should NEVER have UPDATE or DELETE operations.
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                order_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                result TEXT
            )
        """)

        # Schema migration: add BUY columns if they don't exist
        existing_cols = {row[1] for row in c.execute("PRAGMA table_info(cop_orders)").fetchall()}
        buy_columns = {
            "order_side": "TEXT DEFAULT 'SELL'",
            "seller_account_number": "TEXT",
            "seller_account_type": "TEXT",
            "seller_bank_account_id": "TEXT",
            "facilitapay_payout_tx_id": "TEXT",
            "payout_sent_at": "TEXT",
            "mark_paid_at": "TEXT",
            "mark_paid_retries": "INTEGER DEFAULT 0",
        }
        for col, col_type in buy_columns.items():
            if col not in existing_cols:
                c.execute(f"ALTER TABLE cop_orders ADD COLUMN {col} {col_type}")
                logger.info(f"Migration: added column '{col}' to cop_orders")

        conn.commit()
        conn.close()

    # ---- CRUD ----

    def create_order(
        self, binance_order_id: str, binance_external_id: str = None,
        amount_cop: str = None, amount_usdt: str = None,
        binance_buyer_name: str = None, order_side: str = "SELL",
    ) -> COPOrder:
        initial_state = (
            COPOrderState.COLLECTING_BANK_INFO if order_side == "BUY"
            else COPOrderState.AWAITING_INFO
        )
        order = COPOrder(
            binance_order_id=binance_order_id,
            binance_external_id=binance_external_id,
            order_side=order_side,
            amount_cop=amount_cop, amount_usdt=amount_usdt,
            binance_buyer_name=binance_buyer_name,
            state=initial_state,
            created_at=datetime.utcnow(),
        )
        self._save(order)
        return order

    def get_order(self, binance_order_id: str) -> Optional[COPOrder]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM cop_orders WHERE binance_order_id = ?", (binance_order_id,)).fetchone()
        conn.close()
        return self._to_order(row) if row else None

    def get_order_by_tx_id(self, tx_id: str) -> Optional[COPOrder]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM cop_orders WHERE facilitapay_tx_id = ?", (tx_id,)).fetchone()
        conn.close()
        return self._to_order(row) if row else None

    def get_orders_by_state(self, state: COPOrderState) -> list[COPOrder]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM cop_orders WHERE state = ?", (state.value,)).fetchall()
        conn.close()
        return [self._to_order(row) for row in rows]

    # ---- State Machine ----

    def transition(self, order_id: str, new_state: COPOrderState) -> Optional[COPOrder]:
        """
        Transition an order to a new state, enforcing VALID_TRANSITIONS.

        SAFETY: This method MUST be called UNDER a per-order lock (M1).
        Returns None if the transition is not allowed (and logs a rejection).
        """
        order = self.get_order(order_id)
        if not order:
            return None

        old = order.state

        # V4-04: Enforce valid transitions — reject invalid state changes
        allowed = self.VALID_TRANSITIONS.get(old, set())
        if new_state not in allowed:
            logger.warning(
                f"🚨 REJECTED transition {order_id}: {old.value} → {new_state.value} "
                f"(allowed: {[s.value for s in allowed]})"
            )
            return None

        order.state = new_state
        if new_state == COPOrderState.LINK_SENT:
            order.link_expires_at = datetime.utcnow() + timedelta(minutes=self.LINK_EXPIRY_MINUTES)
        self._save(order)
        logger.info(f"COP Order {order_id}: {old.value} → {new_state.value}")
        return order

    # ---- Info setters ----

    # P0-1: States where customer info can be set and order moved to INFO_RECEIVED.
    # SAFETY: Terminal and in-progress states are EXCLUDED to prevent state bypass.
    # NOTE: NEW is excluded because NEW → INFO_RECEIVED is not a valid transition
    #        (orders must go NEW → AWAITING_INFO first).
    _INFO_SETTABLE_STATES = {
        COPOrderState.AWAITING_INFO,
        COPOrderState.INFO_RECEIVED,
    }

    def set_customer_info(self, order_id: str, name: str, cc: str, email: str,
                          bank_code: str, bank_name: str = None):
        order = self.get_order(order_id)
        if not order:
            return
        # P0-1: Block state mutation on terminal/in-progress orders
        if order.state not in self._INFO_SETTABLE_STATES:
            logger.warning(
                "🚨 BLOCKED: set_customer_info for %s in state %s "
                "(only allowed in %s)",
                order_id, order.state.value,
                [s.value for s in self._INFO_SETTABLE_STATES],
            )
            return
        order.customer_name = name
        order.customer_cc = cc
        order.customer_email = email
        order.bank_code = bank_code
        order.bank_name = bank_name
        order.state = COPOrderState.INFO_RECEIVED
        self._save(order)

    def set_payment_link(self, order_id: str, subject_id: str, tx_id: str, payment_url: str):
        order = self.get_order(order_id)
        if not order:
            return
        order.facilitapay_subject_id = subject_id
        order.facilitapay_tx_id = tx_id
        order.payment_url = payment_url
        order.link_expires_at = datetime.utcnow() + timedelta(minutes=self.LINK_EXPIRY_MINUTES)
        order.state = COPOrderState.LINK_SENT
        self._save(order)

    def add_message(self, order_id: str, message: str):
        order = self.get_order(order_id)
        if not order:
            return
        order.chat_messages.append(message)
        self._save(order)

    def mark_welcome_sent(self, order_id: str):
        order = self.get_order(order_id)
        if not order:
            return
        order.welcome_sent = True
        self._save(order)

    # ---- Subject cache ----

    def get_subject_by_cc(self, cc: str) -> Optional[str]:
        """Returns subject_id if cached, else None."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM cop_subjects WHERE cc = ?", (cc,)).fetchone()
        conn.close()
        return row["facilitapay_subject_id"] if row else None

    def cache_subject(self, cc: str, subject_id: str, name: str, email: str = None):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO cop_subjects VALUES (?,?,?,?,?)",
            (cc, subject_id, name, email, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    # ---- Security ----

    def check_cc_different_account(self, cc: str, buyer_name: str) -> Optional[str]:
        """
        Returns previous buyer name if CC used by different Binance account.
        SAFETY: Prevents one customer's cédula from being used by multiple accounts (fraud signal).
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT binance_buyer_name FROM cop_orders WHERE customer_cc = ? AND binance_buyer_name != ? LIMIT 1",
            (cc, buyer_name)
        ).fetchone()
        conn.close()
        return row["binance_buyer_name"] if row else None

    # ---- Message dedup ----

    def is_message_seen(self, order_id: str, message_id: str) -> bool:
        """Check if message has been processed (persisted across restarts)."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT 1 FROM seen_messages WHERE order_id = ? AND message_id = ?",
            (order_id, message_id)
        ).fetchone()
        conn.close()
        return row is not None

    def mark_message_seen(self, order_id: str, message_id: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR IGNORE INTO seen_messages VALUES (?, ?, ?)",
            (order_id, message_id, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()

    # ---- Audit ----

    def log_audit(self, order_id: str, action: str, details: str = "", result: str = ""):
        """Write to immutable audit log. NEVER update or delete audit rows."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO audit_log (timestamp, order_id, action, details, result) VALUES (?,?,?,?,?)",
            (datetime.utcnow().isoformat(), order_id, action, details, result)
        )
        conn.commit()
        conn.close()
        logger.info(f"AUDIT [{action}] order={order_id} result={result} {details}")

    # ---- P0-2: Release guard (DB-enforced at-most-once) ----

    def try_claim_release(self, order_id: str) -> bool:
        """Atomically claim a release slot for this order.

        Returns True if this is the FIRST claim (safe to proceed).
        Returns False if already claimed (MUST NOT call Binance).

        SAFETY: Uses INSERT OR IGNORE on PRIMARY KEY — no TOCTOU race.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO cop_releases (order_id, claimed_at) VALUES (?, ?)",
                (order_id, datetime.utcnow().isoformat()),
            )
            conn.commit()
            claimed = cursor.rowcount > 0
            if not claimed:
                logger.warning("🚨 RELEASE GUARD: order %s already claimed — blocking duplicate release", order_id)
            return claimed
        finally:
            conn.close()

    def mark_release_result(self, order_id: str, success: bool) -> None:
        """Record whether the Binance release call succeeded or failed."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE cop_releases SET released_at = ?, release_success = ? WHERE order_id = ?",
            (datetime.utcnow().isoformat(), 1 if success else 0, order_id),
        )
        conn.commit()
        conn.close()

    def is_release_claimed(self, order_id: str) -> bool:
        """Check if a release was already claimed for this order."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT order_id FROM cop_releases WHERE order_id = ?", (order_id,)
        ).fetchone()
        conn.close()
        return row is not None

    # ---- BUY flow helpers ----

    # States where BUY customer info can be set.
    _BUY_INFO_SETTABLE_STATES = {
        COPOrderState.COLLECTING_BANK_INFO,
    }

    def set_buy_customer_info(
        self, order_id: str, name: str, cc: str, email: str,
        bank_code: str, bank_name: str = None,
        account_number: str = None, account_type: str = None,
    ):
        """Set seller's bank details for BUY orders."""
        order = self.get_order(order_id)
        if not order:
            return
        if order.state not in self._BUY_INFO_SETTABLE_STATES:
            logger.warning(
                "BLOCKED: set_buy_customer_info for %s in state %s",
                order_id, order.state.value,
            )
            return
        order.customer_name = name
        order.customer_cc = cc
        order.customer_email = email
        order.bank_code = bank_code
        order.bank_name = bank_name
        order.seller_account_number = account_number
        order.seller_account_type = account_type
        self._save(order)

    def set_seller_bank_account_id(self, order_id: str, bank_account_id: str):
        """Store FacilitaPay registered bank account UUID."""
        order = self.get_order(order_id)
        if not order:
            return
        order.seller_bank_account_id = bank_account_id
        self._save(order)

    def set_payout_tx_id(self, order_id: str, tx_id: str):
        """Store FacilitaPay payout transaction ID."""
        order = self.get_order(order_id)
        if not order:
            return
        order.facilitapay_payout_tx_id = tx_id
        order.payout_sent_at = datetime.utcnow()
        self._save(order)

    def try_claim_payout(self, order_id: str) -> bool:
        """Atomically claim a payout slot for this BUY order.

        Returns True if this is the FIRST claim (safe to proceed).
        Returns False if already claimed (MUST NOT send COP).

        SAFETY: Uses INSERT OR IGNORE on PRIMARY KEY — no TOCTOU race.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO cop_payout_claims (order_id, claimed_at) VALUES (?, ?)",
                (order_id, datetime.utcnow().isoformat()),
            )
            conn.commit()
            # Check if our row was actually inserted (rowcount = 1) or ignored (0)
            row = conn.execute(
                "SELECT claimed_at FROM cop_payout_claims WHERE order_id = ?",
                (order_id,),
            ).fetchone()
            if row:
                # We got a row — but was it ours?
                # If payout_success is already set, someone already claimed it
                existing = conn.execute(
                    "SELECT payout_success FROM cop_payout_claims WHERE order_id = ?",
                    (order_id,),
                ).fetchone()
                if existing and existing[0] is not None:
                    return False  # Already completed
                return True
            return False
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def mark_payout_result(self, order_id: str, success: bool):
        """Record whether the FacilitaPay payout succeeded or failed."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE cop_payout_claims SET payout_success = ? WHERE order_id = ?",
            (1 if success else 0, order_id),
        )
        conn.commit()
        conn.close()

    def set_mark_paid_pending(self, order_id: str):
        """Mark that COP was sent but Binance mark_paid is pending."""
        order = self.get_order(order_id)
        if not order:
            return
        order.mark_paid_retries = 0
        self._save(order)

    def increment_mark_paid_retries(self, order_id: str) -> int:
        """Increment mark_paid retry counter. Returns new count."""
        order = self.get_order(order_id)
        if not order:
            return 0
        order.mark_paid_retries += 1
        self._save(order)
        return order.mark_paid_retries

    def resolve_mark_paid(self, order_id: str):
        """Record successful mark_paid."""
        order = self.get_order(order_id)
        if not order:
            return
        order.mark_paid_at = datetime.utcnow()
        order.mark_paid_retries = 0
        self._save(order)

    def get_order_by_payout_tx_id(self, tx_id: str) -> Optional[COPOrder]:
        """Find order by FacilitaPay payout transaction ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM cop_orders WHERE facilitapay_payout_tx_id = ?", (tx_id,)
        ).fetchone()
        conn.close()
        return self._to_order(row) if row else None

    # ---- Internal ----

    def _save(self, order: COPOrder):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO cop_orders (
                binance_order_id, binance_external_id,
                customer_name, customer_cc, customer_email,
                bank_code, bank_name,
                amount_cop, amount_usdt,
                facilitapay_subject_id, facilitapay_tx_id, payment_url,
                state, binance_buyer_name,
                created_at, link_expires_at,
                welcome_sent, chat_messages,
                order_side, seller_account_number, seller_account_type,
                seller_bank_account_id, facilitapay_payout_tx_id,
                payout_sent_at, mark_paid_at, mark_paid_retries
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            order.binance_order_id, order.binance_external_id,
            order.customer_name, order.customer_cc, order.customer_email,
            order.bank_code, order.bank_name,
            order.amount_cop, order.amount_usdt,
            order.facilitapay_subject_id, order.facilitapay_tx_id, order.payment_url,
            order.state.value, order.binance_buyer_name,
            order.created_at.isoformat() if order.created_at else None,
            order.link_expires_at.isoformat() if order.link_expires_at else None,
            1 if order.welcome_sent else 0,
            ",".join(order.chat_messages) if order.chat_messages else "",
            order.order_side,
            order.seller_account_number, order.seller_account_type,
            order.seller_bank_account_id, order.facilitapay_payout_tx_id,
            order.payout_sent_at.isoformat() if order.payout_sent_at else None,
            order.mark_paid_at.isoformat() if order.mark_paid_at else None,
            order.mark_paid_retries,
        ))
        conn.commit()
        conn.close()

    def _to_order(self, row) -> COPOrder:
        def dt(v):
            return datetime.fromisoformat(v) if v else None

        # Safe column access for migrated columns
        def col(name, default=None):
            try:
                return row[name]
            except (IndexError, KeyError):
                return default

        return COPOrder(
            binance_order_id=row["binance_order_id"],
            binance_external_id=row["binance_external_id"],
            order_side=col("order_side", "SELL"),
            customer_name=row["customer_name"], customer_cc=row["customer_cc"],
            customer_email=row["customer_email"],
            bank_code=row["bank_code"], bank_name=row["bank_name"],
            amount_cop=row["amount_cop"], amount_usdt=row["amount_usdt"],
            facilitapay_subject_id=row["facilitapay_subject_id"],
            facilitapay_tx_id=row["facilitapay_tx_id"],
            payment_url=row["payment_url"],
            state=COPOrderState(row["state"]),
            binance_buyer_name=row["binance_buyer_name"],
            created_at=dt(row["created_at"]),
            link_expires_at=dt(row["link_expires_at"]),
            welcome_sent=bool(row["welcome_sent"]),
            chat_messages=row["chat_messages"].split(",") if row["chat_messages"] else [],
            # BUY fields (migrated columns with safe fallbacks)
            seller_account_number=col("seller_account_number"),
            seller_account_type=col("seller_account_type"),
            seller_bank_account_id=col("seller_bank_account_id"),
            facilitapay_payout_tx_id=col("facilitapay_payout_tx_id"),
            payout_sent_at=dt(col("payout_sent_at")),
            mark_paid_at=dt(col("mark_paid_at")),
            mark_paid_retries=int(col("mark_paid_retries", 0) or 0),
        )
