"""
FACILITAPAY PERSISTENCE
========================
SQLite tables for FacilitaPay COP data — subjects, bank accounts,
transactions, and webhook deduplication.

Uses the same pattern as the existing PearV1 OrderDatabase (WAL mode,
busy timeout, fail-fast semantics).
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class FacilitaPayDatabase:
    """SQLite persistence for FacilitaPay COP data."""

    def __init__(self, db_path: str = "facilitapay.db"):
        self.db_path = Path(db_path)
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        conn = self._connect()
        try:
            conn.executescript("""
                -- FacilitaPay subjects (persons + companies)
                CREATE TABLE IF NOT EXISTS fp_subjects (
                    id TEXT PRIMARY KEY,
                    document_number TEXT UNIQUE NOT NULL,
                    document_type TEXT NOT NULL,
                    social_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    email TEXT,
                    phone TEXT,
                    fiscal_country TEXT DEFAULT 'Colombia',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    raw_json TEXT
                );

                -- FacilitaPay customer bank accounts (for payouts)
                CREATE TABLE IF NOT EXISTS fp_bank_accounts (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL REFERENCES fp_subjects(id),
                    account_number TEXT NOT NULL,
                    branch_number TEXT,
                    bank_code TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    owner_name TEXT,
                    owner_document_number TEXT,
                    currency TEXT DEFAULT 'COP',
                    created_at TEXT DEFAULT (datetime('now')),
                    raw_json TEXT,
                    UNIQUE(subject_id, account_number, bank_code)
                );

                -- FacilitaPay transactions (both pay-in and payout)
                CREATE TABLE IF NOT EXISTS fp_transactions (
                    id TEXT PRIMARY KEY,
                    pear_order_id TEXT,
                    direction TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    amount TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    exchange_currency TEXT,
                    subject_id TEXT NOT NULL,
                    payment_url TEXT,
                    payment_url_created_at TEXT,
                    pse_ticket_id INTEGER,
                    pse_trazability_code TEXT,
                    pse_bank_code TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    raw_json TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_fp_tx_pear_order
                    ON fp_transactions(pear_order_id);
                CREATE INDEX IF NOT EXISTS idx_fp_tx_status
                    ON fp_transactions(status);

                -- Prevent duplicate active transactions per order+direction (C-04 fix)
                CREATE UNIQUE INDEX IF NOT EXISTS idx_fp_tx_order_direction_active
                    ON fp_transactions(pear_order_id, direction)
                    WHERE status != 'canceled';

                -- Webhook notification deduplication log
                -- handler_status: 'received' = persisted but not yet processed
                --                 'processed' = handler executed successfully
                --                 Used by reconciliation to retry failed handlers
                CREATE TABLE IF NOT EXISTS fp_webhook_log (
                    notification_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    transaction_id TEXT,
                    transaction_ids TEXT,
                    handler_status TEXT NOT NULL DEFAULT 'received',
                    processed_at TEXT DEFAULT (datetime('now')),
                    raw_json TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_fp_webhook_tx
                    ON fp_webhook_log(transaction_id);
                CREATE INDEX IF NOT EXISTS idx_fp_webhook_status
                    ON fp_webhook_log(handler_status);

                -- Webhook failure tracking for retry safety valve (H-04 fix)
                CREATE TABLE IF NOT EXISTS fp_webhook_failures (
                    dedup_key TEXT PRIMARY KEY,
                    fail_count INTEGER NOT NULL DEFAULT 0,
                    last_failed_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
        finally:
            conn.close()

    # ─── Subjects ──────────────────────────────────────────

    def save_subject(self, subject_id: str, document_number: str,
                     document_type: str, social_name: str, status: str,
                     email: str | None = None, phone: str | None = None,
                     raw_json: str | None = None) -> None:
        """Insert or update a FacilitaPay subject."""
        conn = self._connect()
        try:
            conn.execute("""
                INSERT INTO fp_subjects (id, document_number, document_type,
                    social_name, status, email, phone, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    social_name = excluded.social_name,
                    email = excluded.email,
                    phone = excluded.phone,
                    updated_at = datetime('now'),
                    raw_json = excluded.raw_json
            """, (subject_id, document_number, document_type,
                  social_name, status, email, phone, raw_json))
            conn.commit()
        finally:
            conn.close()

    def get_subject_by_document(self, document_number: str) -> dict | None:
        """Lookup subject by document number (for dedup)."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM fp_subjects WHERE document_number = ?",
                (document_number,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_subject(self, subject_id: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM fp_subjects WHERE id = ?",
                (subject_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ─── Bank Accounts ─────────────────────────────────────

    def save_bank_account(self, bank_account_id: str, subject_id: str,
                          account_number: str, bank_code: str, bank_name: str,
                          account_type: str, branch_number: str | None = None,
                          owner_name: str | None = None,
                          owner_document_number: str | None = None,
                          raw_json: str | None = None) -> None:
        """Insert or update a customer bank account."""
        conn = self._connect()
        try:
            conn.execute("""
                INSERT INTO fp_bank_accounts (id, subject_id, account_number,
                    branch_number, bank_code, bank_name, account_type,
                    owner_name, owner_document_number, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    account_number = excluded.account_number,
                    bank_code = excluded.bank_code,
                    bank_name = excluded.bank_name,
                    raw_json = excluded.raw_json
            """, (bank_account_id, subject_id, account_number, branch_number,
                  bank_code, bank_name, account_type, owner_name,
                  owner_document_number, raw_json))
            conn.commit()
        finally:
            conn.close()

    def get_bank_account(self, subject_id: str, account_number: str,
                         bank_code: str) -> dict | None:
        """Lookup bank account by subject + account + bank (for dedup)."""
        conn = self._connect()
        try:
            row = conn.execute(
                """SELECT * FROM fp_bank_accounts
                   WHERE subject_id = ? AND account_number = ? AND bank_code = ?""",
                (subject_id, account_number, bank_code)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ─── Transactions ──────────────────────────────────────

    def save_transaction(self, tx_id: str, pear_order_id: str | None,
                         direction: str, status: str, amount: str,
                         currency: str, subject_id: str,
                         exchange_currency: str | None = None,
                         payment_url: str | None = None,
                         pse_ticket_id: int | None = None,
                         pse_trazability_code: str | None = None,
                         pse_bank_code: str | None = None,
                         raw_json: str | None = None) -> None:
        """
        Insert or update a FacilitaPay transaction.
        
        Raises sqlite3.IntegrityError if a non-canceled transaction already
        exists for the same (pear_order_id, direction) combination.
        """
        payment_url_ts = datetime.utcnow().isoformat() if payment_url else None
        conn = self._connect()
        try:
            conn.execute("""
                INSERT INTO fp_transactions (id, pear_order_id, direction, status,
                    amount, currency, exchange_currency, subject_id, payment_url,
                    payment_url_created_at, pse_ticket_id, pse_trazability_code,
                    pse_bank_code, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    updated_at = datetime('now'),
                    raw_json = excluded.raw_json
            """, (tx_id, pear_order_id, direction, status, amount, currency,
                  exchange_currency, subject_id, payment_url, payment_url_ts,
                  pse_ticket_id, pse_trazability_code, pse_bank_code, raw_json))
            conn.commit()
        finally:
            conn.close()

    def get_expired_pse_links(self, minutes: int = 21) -> list[dict]:
        """Get pending PSE transactions with expired payment URLs."""
        conn = self._connect()
        try:
            rows = conn.execute("""
                SELECT * FROM fp_transactions
                WHERE direction = 'payin'
                AND status = 'pending'
                AND payment_url IS NOT NULL
                AND payment_url_created_at IS NOT NULL
                AND payment_url_created_at < datetime('now', ? || ' minutes')
            """, (f"-{minutes}",)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_transaction_status(self, tx_id: str, new_status: str) -> None:
        """Update transaction status (from webhook or poll)."""
        conn = self._connect()
        try:
            conn.execute(
                """UPDATE fp_transactions
                   SET status = ?, updated_at = datetime('now')
                   WHERE id = ?""",
                (new_status, tx_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_transaction(self, tx_id: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM fp_transactions WHERE id = ?", (tx_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_transaction_by_order(self, pear_order_id: str,
                                  direction: str) -> dict | None:
        """Find existing transaction for a PearV1 order (for dedup)."""
        conn = self._connect()
        try:
            row = conn.execute(
                """SELECT * FROM fp_transactions
                   WHERE pear_order_id = ? AND direction = ?
                   AND status != 'canceled'
                   ORDER BY created_at DESC LIMIT 1""",
                (pear_order_id, direction)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_pending_transactions(self, direction: str | None = None,
                                  older_than_minutes: int = 5) -> list[dict]:
        """Get pending transactions for status polling."""
        conn = self._connect()
        try:
            query = """
                SELECT * FROM fp_transactions
                WHERE status = 'pending'
                AND created_at < datetime('now', ? || ' minutes')
            """
            params: list[Any] = [f"-{older_than_minutes}"]
            if direction:
                query += " AND direction = ?"
                params.append(direction)
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def log_webhook_atomic(self, notification_id: str, event_type: str,
                           transaction_id: str | None = None,
                           transaction_ids: str | None = None,
                           raw_json: str | None = None) -> bool:
        """
        Atomically persist a webhook event. Returns True if this is a NEW event,
        False if it was already persisted (dedup).
        
        Uses INSERT OR IGNORE on the UNIQUE(notification_id) PK constraint.
        No read-then-write race — the INSERT is the dedup check.
        
        New events are persisted with handler_status='received'.
        Callers must call mark_webhook_processed() after successful handling.
        """
        conn = self._connect()
        try:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO fp_webhook_log
                    (notification_id, event_type, transaction_id,
                     transaction_ids, handler_status, raw_json)
                VALUES (?, ?, ?, ?, 'received', ?)
            """, (notification_id, event_type, transaction_id,
                  transaction_ids, raw_json))
            conn.commit()
            return cursor.rowcount > 0  # True = new event, False = duplicate
        finally:
            conn.close()

    def mark_webhook_processed(self, notification_id: str) -> None:
        """Mark a persisted webhook as successfully processed."""
        conn = self._connect()
        try:
            conn.execute("""
                UPDATE fp_webhook_log
                SET handler_status = 'processed',
                    processed_at = datetime('now')
                WHERE notification_id = ?
            """, (notification_id,))
            conn.commit()
        finally:
            conn.close()

    def get_unprocessed_webhooks(self, older_than_minutes: int = 5) -> list[dict]:
        """
        Get webhooks that were persisted but whose handlers failed.
        These need to be retried by the reconciliation sweep.
        
        Only returns events older than `older_than_minutes` to avoid
        racing with in-flight handler execution.
        """
        conn = self._connect()
        try:
            rows = conn.execute("""
                SELECT * FROM fp_webhook_log
                WHERE handler_status = 'received'
                AND processed_at < datetime('now', ? || ' minutes')
                ORDER BY processed_at ASC
            """, (f"-{older_than_minutes}",)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def is_webhook_processed(self, notification_id: str) -> bool:
        """Check if a webhook notification was already processed."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM fp_webhook_log WHERE notification_id = ?",
                (notification_id,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def is_event_processed(self, transaction_id: str, event_type: str) -> bool:
        """Check if a specific event was already handled for a transaction."""
        conn = self._connect()
        try:
            row = conn.execute(
                """SELECT 1 FROM fp_webhook_log
                   WHERE transaction_id = ? AND event_type = ?
                   AND handler_status = 'processed'""",
                (transaction_id, event_type)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def log_webhook(self, notification_id: str, event_type: str,
                    transaction_id: str | None = None,
                    transaction_ids: str | None = None,
                    raw_json: str | None = None) -> None:
        """Record a processed webhook for deduplication. LEGACY — use log_webhook_atomic."""
        conn = self._connect()
        try:
            conn.execute("""
                INSERT OR IGNORE INTO fp_webhook_log
                    (notification_id, event_type, transaction_id,
                     transaction_ids, handler_status, raw_json)
                VALUES (?, ?, ?, ?, 'processed', ?)
            """, (notification_id, event_type, transaction_id,
                  transaction_ids, raw_json))
            conn.commit()
        finally:
            conn.close()

    def get_webhook_fail_count(self, dedup_key: str) -> int:
        """Get the number of times a webhook has failed processing."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT fail_count FROM fp_webhook_failures WHERE dedup_key = ?",
                (dedup_key,)
            ).fetchone()
            return row["fail_count"] if row else 0
        finally:
            conn.close()

    def increment_webhook_fail_count(self, dedup_key: str) -> None:
        """Increment the failure counter for a webhook dedup key."""
        conn = self._connect()
        try:
            conn.execute("""
                INSERT INTO fp_webhook_failures (dedup_key, fail_count, last_failed_at)
                VALUES (?, 1, datetime('now'))
                ON CONFLICT(dedup_key) DO UPDATE SET
                    fail_count = fail_count + 1,
                    last_failed_at = datetime('now')
            """, (dedup_key,))
            conn.commit()
        finally:
            conn.close()
