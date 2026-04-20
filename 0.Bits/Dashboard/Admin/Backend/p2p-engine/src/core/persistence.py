"""
ORDER PERSISTENCE - SQLite Storage
===================================
Persists order state to SQLite database for crash recovery.
All order changes are saved automatically.

Database: data/orders.db
Tables:
  - orders: Core order data
  - order_history: State change audit log
  - eur_payouts: DB-level at-most-once guard for EUR buy payouts (P0-5)
  - eur_releases: DB-level at-most-once guard for EUR sell releases (P0-6)
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("persistence")


class OrderDatabase:
    """
    SQLite persistence for P2P orders.
    
    Saves order state on every mutation.
    Loads all orders on startup for crash recovery.
    """
    
    def __init__(self, db_path: str = "data/orders.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _connect(self):
        """Thread-safe connection context with WAL mode."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # FIX C3: WAL mode for concurrent safety
        conn.execute("PRAGMA busy_timeout=30000")  # 30s busy wait
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    external_id TEXT UNIQUE NOT NULL,
                    exchange TEXT NOT NULL,
                    state TEXT NOT NULL,
                    order_data TEXT NOT NULL,
                    matched_payment TEXT,
                    kyc_session_id TEXT,
                    needs_kyc INTEGER DEFAULT 0,
                    kyc_evaluated INTEGER DEFAULT 0,
                    needs_human_review INTEGER DEFAULT 0,
                    auto_release_approved INTEGER DEFAULT 0,
                    last_error TEXT,
                    retry_count INTEGER DEFAULT 0,
                    paid_at TEXT,
                    payout_sent_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Migration: Add paid_at column if missing
            try:
                conn.execute("ALTER TABLE orders ADD COLUMN paid_at TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # S2: Migration — Add payout_sent_at column if missing
            # SAFETY: Tracks when a payout was actually sent. Used for idempotency checks
            # to prevent double payouts. If payout_sent_at is set, the order has already
            # been paid out and MUST NOT be paid again.
            try:
                conn.execute("ALTER TABLE orders ADD COLUMN payout_sent_at TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # P1-C: Migration — Add payout_details_json column
            # Persists the payout target snapshot (IBAN, name, amount) to survive restarts
            try:
                conn.execute("ALTER TABLE orders ADD COLUMN payout_details_json TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("ALTER TABLE orders ADD COLUMN trustpilot_sent_at TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS order_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    reason TEXT,
                    data TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            """)

            # P0-5: EUR payout guard — at-most-once payout per order
            # P0-A: Extended with mark_paid tracking columns
            conn.execute("""
                CREATE TABLE IF NOT EXISTS eur_payouts (
                    order_id TEXT PRIMARY KEY,
                    replay_id TEXT NOT NULL,
                    claimed_at TEXT NOT NULL,
                    completed_at TEXT,
                    payout_success INTEGER,
                    januar_tx_id TEXT,
                    mark_paid_pending INTEGER DEFAULT 0,
                    mark_paid_retries INTEGER DEFAULT 0,
                    mark_paid_at TEXT
                )
            """)
            
            # P0-A: Migration — add mark_paid columns to existing eur_payouts
            for col, defn in [("januar_tx_id", "TEXT"), ("mark_paid_pending", "INTEGER DEFAULT 0"),
                              ("mark_paid_retries", "INTEGER DEFAULT 0"), ("mark_paid_at", "TEXT")]:
                try:
                    conn.execute(f"ALTER TABLE eur_payouts ADD COLUMN {col} {defn}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

            # P0-6: EUR release guard — at-most-once release per order
            conn.execute("""
                CREATE TABLE IF NOT EXISTS eur_releases (
                    order_id TEXT PRIMARY KEY,
                    claimed_at TEXT NOT NULL,
                    completed_at TEXT,
                    release_success INTEGER
                )
            """)

            # SELL AD TOPUP guard — at-most-once topup per BUY order + audit trail
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sell_ad_topups (
                    order_id        TEXT PRIMARY KEY,
                    ad_id           TEXT NOT NULL DEFAULT '',
                    usdt_added      REAL NOT NULL DEFAULT 0,
                    old_qty         REAL NOT NULL DEFAULT 0,
                    new_qty         REAL NOT NULL DEFAULT 0,
                    funding_balance REAL NOT NULL DEFAULT 0,
                    success         INTEGER NOT NULL DEFAULT 0,
                    error           TEXT,
                    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # Indexes for fast lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_external_id ON orders (external_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_state ON orders (state)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_exchange ON orders (exchange)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_order_id ON order_history (order_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON order_history (timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_to_state ON order_history (to_state)")

            # CRITICAL FIX: Consumed payments registry — prevents same payment reuse
            # Added after forensic audit revealed single payments being matched to 20+ orders
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consumed_payments (
                    payment_id TEXT PRIMARY KEY,
                    order_external_id TEXT NOT NULL,
                    consumed_at TEXT NOT NULL
                )
            """)
    
    # =========================================================================
    # SAVE / UPDATE
    # =========================================================================
    
    def save_order(self, managed_order: Any) -> None:
        """
        Upsert a ManagedOrder to the database.
        Called on every state change.
        """
        with self._connect() as conn:
            order = managed_order.order
            
            conn.execute("""
                INSERT INTO orders (
                    id, external_id, exchange, state, order_data,
                    matched_payment,
                    needs_human_review, auto_release_approved,
                    last_error, retry_count, paid_at, payout_sent_at,
                    payout_details_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    state = excluded.state,
                    order_data = excluded.order_data,
                    matched_payment = excluded.matched_payment,
                    needs_human_review = excluded.needs_human_review,
                    auto_release_approved = excluded.auto_release_approved,
                    last_error = excluded.last_error,
                    retry_count = excluded.retry_count,
                    paid_at = excluded.paid_at,
                    payout_sent_at = excluded.payout_sent_at,
                    payout_details_json = excluded.payout_details_json,
                    updated_at = excluded.updated_at
            """, (
                managed_order.id,
                order.external_id,
                order.exchange.value,
                managed_order.state.value,
                order.model_dump_json(),
                managed_order.matched_payment.model_dump_json() if managed_order.matched_payment else None,
                int(managed_order.needs_human_review),
                int(managed_order.auto_release_approved),
                managed_order.last_error,
                managed_order.retry_count,
                managed_order.paid_at.isoformat() if managed_order.paid_at else None,
                managed_order.payout_sent_at.isoformat() if managed_order.payout_sent_at else None,
                json.dumps(managed_order.payout_details) if managed_order.payout_details else None,
                managed_order.created_at.isoformat(),
                managed_order.updated_at.isoformat(),
            ))
    
    def save_state_change(
        self,
        order_id: str,
        from_state: str | None,
        to_state: str,
        reason: str = "",
        data: dict | None = None
    ) -> None:
        """Record a state transition in the audit log."""
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO order_history (order_id, from_state, to_state, reason, data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                from_state,
                to_state,
                reason,
                json.dumps(data) if data else None,
                datetime.now().isoformat()
            ))
    
    # =========================================================================
    # LOAD / QUERY
    # =========================================================================
    
    def load_all_orders(self) -> list[dict]:
        """Load all orders from database (for startup recovery)."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]
    
    def load_active_orders(self) -> list[dict]:
        """Load only non-terminal orders."""
        terminal_states = ('completed', 'cancelled', 'expired')
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM orders WHERE state NOT IN (?, ?, ?) ORDER BY created_at DESC",
                terminal_states
            ).fetchall()
            return [dict(row) for row in rows]
    
    def load_order(self, order_id: str) -> dict | None:
        """Load a single order by internal ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            return dict(row) if row else None
    
    def load_by_external_id(self, external_id: str) -> dict | None:
        """Load a single order by exchange order ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM orders WHERE external_id = ?", (external_id,)).fetchone()
            return dict(row) if row else None
    
    def get_order_history(self, order_id: str) -> list[dict]:
        """Get full state change history for an order."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM order_history WHERE order_id = ? ORDER BY timestamp ASC",
                (order_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    # =========================================================================
    # STATS
    # =========================================================================
    
    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            by_state = conn.execute(
                "SELECT state, COUNT(*) as count FROM orders GROUP BY state"
            ).fetchall()
            by_exchange = conn.execute(
                "SELECT exchange, COUNT(*) as count FROM orders GROUP BY exchange"
            ).fetchall()
            
            return {
                "total_orders": total,
                "by_state": {row["state"]: row["count"] for row in by_state},
                "by_exchange": {row["exchange"]: row["count"] for row in by_exchange}
            }
    
    def delete_order(self, order_id: str) -> bool:
        """Delete an order (use with caution)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM order_history WHERE order_id = ?", (order_id,))
            result = conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            return result.rowcount > 0

    # =========================================================================
    # P0-5: EUR PAYOUT GUARD (at-most-once)
    # =========================================================================

    def try_claim_eur_payout(self, order_id: str, replay_id: str) -> bool:
        """
        Atomically claim the right to execute a payout for an EUR order.
        Returns True only on the FIRST call per order_id.
        Uses INSERT OR IGNORE on PRIMARY KEY(order_id) for atomic dedup.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO eur_payouts (order_id, replay_id, claimed_at) VALUES (?, ?, ?)",
                (order_id, replay_id, datetime.now().isoformat()),
            )
            claimed = cursor.rowcount > 0
            if not claimed:
                logger.warning(
                    "🚨 EUR PAYOUT GUARD: order %s already claimed — blocking duplicate payout",
                    order_id,
                )
            return claimed

    def mark_eur_payout_result(self, order_id: str, success: bool) -> None:
        """Record payout outcome in the guard table."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE eur_payouts SET completed_at = ?, payout_success = ? WHERE order_id = ?",
                (datetime.now().isoformat(), 1 if success else 0, order_id),
            )

    # =========================================================================
    # P0-A: MARK PAID RETRY TRACKING
    # =========================================================================

    def set_mark_paid_pending(self, order_id: str, januar_tx_id: str) -> None:
        """Flag an order as needing mark_paid retry (EUR sent, Binance mark_paid failed)."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE eur_payouts SET mark_paid_pending = 1, januar_tx_id = ? WHERE order_id = ?",
                (januar_tx_id, order_id),
            )
            logger.warning("P0-A: mark_paid_pending=1 for order %s (januar_tx=%s)", order_id, januar_tx_id)

    def resolve_mark_paid(self, order_id: str) -> None:
        """Clear mark_paid_pending after successful mark_paid on Binance."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE eur_payouts SET mark_paid_pending = 0, mark_paid_at = ? WHERE order_id = ?",
                (datetime.now().isoformat(), order_id),
            )
            logger.info("P0-A: mark_paid resolved for order %s", order_id)

    def increment_mark_paid_retry(self, order_id: str) -> int:
        """Increment retry count. Returns new count."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE eur_payouts SET mark_paid_retries = mark_paid_retries + 1 WHERE order_id = ?",
                (order_id,),
            )
            row = conn.execute(
                "SELECT mark_paid_retries FROM eur_payouts WHERE order_id = ?",
                (order_id,),
            ).fetchone()
            return dict(row)["mark_paid_retries"] if row else 0

    # =========================================================================
    # SELL AD TOPUP GUARD (at-most-once per BUY order)
    # =========================================================================

    def try_claim_sell_topup(self, order_id: str) -> bool:
        """
        Atomically claim the right to top up a SELL ad for a completed BUY order.
        Returns True only on the FIRST call per order_id.
        Uses INSERT OR IGNORE on PRIMARY KEY(order_id) for atomic dedup.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO sell_ad_topups (order_id, created_at) VALUES (?, ?)",
                (order_id, datetime.now().isoformat()),
            )
            claimed = cursor.rowcount > 0
            if not claimed:
                logger.warning(
                    "SELL TOPUP GUARD: order %s already claimed — blocking duplicate topup",
                    order_id,
                )
            return claimed

    def record_sell_topup(
        self,
        order_id: str,
        ad_id: str,
        usdt_added: float,
        old_qty: float,
        new_qty: float,
        funding_balance: float,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """Record SELL ad topup outcome for audit."""
        with self._connect() as conn:
            conn.execute(
                """UPDATE sell_ad_topups
                   SET ad_id = ?, usdt_added = ?, old_qty = ?, new_qty = ?,
                       funding_balance = ?, success = ?, error = ?
                   WHERE order_id = ?""",
                (ad_id, usdt_added, old_qty, new_qty,
                 funding_balance, 1 if success else 0, error, order_id),
            )

    def get_pending_mark_paids(self) -> list[dict]:
        """Get all orders with mark_paid_pending=1 for reconciliation."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT order_id, replay_id, januar_tx_id, mark_paid_retries, claimed_at "
                "FROM eur_payouts WHERE mark_paid_pending = 1"
            ).fetchall()
            return [dict(row) for row in rows]

    def export_cancelled_order_csv(self, managed_order: "Any") -> None:
        """
        Append a permanently-failed order to data/CANCELLED_ORDERS.csv.
        Contains ALL order details for forensic review.
        """
        import csv
        csv_path = Path("data/CANCELLED_ORDERS.csv")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = csv_path.exists()

        order = managed_order.order
        row = {
            "timestamp": datetime.now().isoformat(),
            "managed_id": managed_order.id,
            "external_id": order.external_id,
            "internal_order_number": order.internal_order_number,
            "exchange": order.exchange.value,
            "side": order.side.value if hasattr(order, "side") else "",
            "fiat_amount": order.fiat_amount,
            "fiat_currency": order.fiat_currency.value,
            "crypto_amount": order.crypto_amount,
            "crypto_currency": order.crypto_currency.value if hasattr(order, "crypto_currency") else "",
            "price": order.price,
            "counterparty_name": order.counterparty.real_name if order.counterparty else "",
            "state": managed_order.state.value,
            "payout_sent_at": managed_order.payout_sent_at.isoformat() if managed_order.payout_sent_at else "",
            "paid_at": managed_order.paid_at.isoformat() if managed_order.paid_at else "",
            "payout_recipient_iban": (managed_order.payout_details or {}).get("recipient_account", ""),
            "payout_recipient_name": (managed_order.payout_details or {}).get("recipient_name", ""),
            "payout_replay_id": (managed_order.payout_details or {}).get("replay_id", ""),
            "last_error": managed_order.last_error or "",
            "reason": "mark_paid_failed_exhausted",
        }

        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        logger.critical(
            "CANCELLED ORDER exported to CSV: %s (%s %s EUR to %s)",
            order.external_id, order.fiat_amount, order.fiat_currency.value,
            (managed_order.payout_details or {}).get("recipient_name", "UNKNOWN"),
        )

    # =========================================================================
    # P0-6: EUR RELEASE GUARD (at-most-once)
    # =========================================================================

    def try_claim_eur_release(self, order_id: str) -> bool:
        """
        Atomically claim the right to release crypto for an EUR order.
        Returns True only on the FIRST call per order_id.
        Uses INSERT OR IGNORE on PRIMARY KEY(order_id) for atomic dedup.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO eur_releases (order_id, claimed_at) VALUES (?, ?)",
                (order_id, datetime.now().isoformat()),
            )
            claimed = cursor.rowcount > 0
            if not claimed:
                logger.warning(
                    "🚨 EUR RELEASE GUARD: order %s already claimed — blocking duplicate release",
                    order_id,
                )
            return claimed

    def mark_eur_release_result(self, order_id: str, success: bool) -> None:
        """Record release outcome in the guard table."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE eur_releases SET completed_at = ?, release_success = ? WHERE order_id = ?",
                (datetime.now().isoformat(), 1 if success else 0, order_id),
            )

    # =========================================================================
    # PAYMENT CONSUMPTION REGISTRY (prevents same payment reuse)
    # =========================================================================

    def is_payment_consumed(self, payment_id: str) -> bool:
        """Check if a Januar payment has already been used to release an order."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM consumed_payments WHERE payment_id = ?",
                (payment_id,),
            ).fetchone()
            return row is not None

    def mark_payment_consumed(self, payment_id: str, order_external_id: str) -> None:
        """Mark a Januar payment as consumed — it can NEVER be reused."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO consumed_payments (payment_id, order_external_id, consumed_at) VALUES (?, ?, ?)",
                (payment_id, order_external_id, datetime.now().isoformat()),
            )
            logger.warning(
                "🛡️ PAYMENT CONSUMED: %s -> order %s",
                payment_id[:12], order_external_id[-8:],
            )

    # =========================================================================
    # DATABASE RESET & ARCHIVE
    # =========================================================================
    
    def mark_trustpilot_sent(self, order_id: str) -> None:
        """Mark that a Trustpilot thank-you was sent for this order."""
        from datetime import datetime, timezone
        with self._connect() as conn:
            conn.execute(
                "UPDATE orders SET trustpilot_sent_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), order_id),
            )

    def is_trustpilot_sent(self, order_id: str) -> bool:
        """Check if Trustpilot message was already sent for this order."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT trustpilot_sent_at FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            return bool(row and row[0])

    def is_trustpilot_sent_by_ext_id(self, ext_id: str) -> bool:
        """Check if Trustpilot message was already sent, by external_id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT trustpilot_sent_at FROM orders WHERE external_id = ?",
                (ext_id,),
            ).fetchone()
            return bool(row and row[0])

    def mark_trustpilot_sent_by_ext_id(self, ext_id: str) -> None:
        """Mark Trustpilot sent, by external_id."""
        from datetime import datetime, timezone
        with self._connect() as conn:
            conn.execute(
                "UPDATE orders SET trustpilot_sent_at = ? WHERE external_id = ?",
                (datetime.now(timezone.utc).isoformat(), ext_id),
            )

    def archive_and_reset(self) -> str | None:
        """
        Archive the current database and create a fresh one.
        
        Renames the current orders.db to orders_backup_{timestamp}.db.
        Returns the path to the backup file, or None if no DB existed.
        """
        if not self.db_path.exists():
            logger.info("No existing database to archive.")
            self._init_db()
            return None
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_path.parent / f"orders_backup_{timestamp}.db"
        
        # Rename the old DB
        import shutil
        shutil.move(str(self.db_path), str(backup_path))
        logger.info("Archived old database to: %s", backup_path)
        
        # Create fresh DB
        self._init_db()
        logger.info("Created fresh database.")
        
        return str(backup_path)
    
    def clear_all(self) -> int:
        """
        Delete all orders and history from the database (without archiving).
        Returns the number of orders deleted.
        """
        with self._connect() as conn:
            conn.execute("DELETE FROM order_history")
            result = conn.execute("DELETE FROM orders")
            count = result.rowcount
            logger.info("Cleared %d orders from database.", count)
            return count



# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

order_db = OrderDatabase()
