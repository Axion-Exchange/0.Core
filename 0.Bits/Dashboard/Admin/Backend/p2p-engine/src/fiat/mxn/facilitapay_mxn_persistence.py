"""
FacilitaPay MXN Persistence Layer
==================================
SQLite-backed persistence for MXN FacilitaPay transactions.
Separate DB file from COP to avoid collisions.
Mirrors facilitapay_persistence.py schema.
"""

import json
import sqlite3
import logging
from typing import Any

logger = logging.getLogger("fp_mxn_db")


class FacilitaPayMXNDatabase:
    """SQLite database for MXN FacilitaPay transactions."""

    def __init__(self, db_path: str = "data/facilitapay_mxn.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS fp_mxn_subjects (
                    id TEXT PRIMARY KEY,
                    document_number TEXT UNIQUE NOT NULL,
                    document_type TEXT DEFAULT 'curp',
                    social_name TEXT,
                    email TEXT,
                    rfc TEXT,
                    status TEXT DEFAULT 'pending',
                    raw_json TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS fp_mxn_bank_accounts (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    clabe TEXT NOT NULL,
                    bank_code TEXT,
                    bank_name TEXT,
                    owner_name TEXT,
                    owner_document_number TEXT,
                    raw_json TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS fp_mxn_transactions (
                    id TEXT PRIMARY KEY,
                    pear_order_id TEXT,
                    direction TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    amount TEXT,
                    currency TEXT DEFAULT 'MXN',
                    subject_id TEXT,
                    dynamic_clabe TEXT,
                    exchange_currency TEXT DEFAULT 'MXN',
                    raw_json TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_mxn_tx_order
                    ON fp_mxn_transactions(pear_order_id, direction);
                CREATE INDEX IF NOT EXISTS idx_mxn_tx_status
                    ON fp_mxn_transactions(status);

                CREATE TABLE IF NOT EXISTS fp_mxn_webhook_log (
                    notification_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    transaction_id TEXT,
                    transaction_ids TEXT,
                    handler_status TEXT DEFAULT 'received',
                    raw_json TEXT,
                    received_at TEXT DEFAULT (datetime('now')),
                    processed_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS fp_mxn_webhook_failures (
                    dedup_key TEXT PRIMARY KEY,
                    fail_count INTEGER DEFAULT 0,
                    last_failed_at TEXT
                );
            """)
            conn.commit()
            logger.info("MXN FacilitaPay database initialized: %s", self.db_path)
        finally:
            conn.close()

    # ─── SUBJECTS ─────────────────────────────────────────────

    def get_subject_by_document(self, document_number: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM fp_mxn_subjects WHERE document_number = ?",
                (document_number,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def save_subject(self, subject_id: str, document_number: str,
                     social_name: str, email: str | None = None,
                     rfc: str | None = None, status: str = "approved",
                     raw_json: str | None = None) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO fp_mxn_subjects
                    (id, document_number, social_name, email, rfc, status, raw_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (subject_id, document_number, social_name, email, rfc, status, raw_json))
            conn.commit()
        finally:
            conn.close()

    # ─── BANK ACCOUNTS ────────────────────────────────────────

    def get_bank_account_by_clabe(self, clabe: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM fp_mxn_bank_accounts WHERE clabe = ?",
                (clabe,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def save_bank_account(self, bank_account_id: str, subject_id: str,
                          clabe: str, bank_code: str | None = None,
                          bank_name: str | None = None,
                          owner_name: str | None = None,
                          owner_document_number: str | None = None,
                          raw_json: str | None = None) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO fp_mxn_bank_accounts
                    (id, subject_id, clabe, bank_code, bank_name,
                     owner_name, owner_document_number, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (bank_account_id, subject_id, clabe, bank_code, bank_name,
                  owner_name, owner_document_number, raw_json))
            conn.commit()
        finally:
            conn.close()

    # ─── TRANSACTIONS ─────────────────────────────────────────

    def save_transaction(self, tx_id: str, pear_order_id: str,
                         direction: str, status: str, amount: str,
                         currency: str = "MXN", subject_id: str | None = None,
                         dynamic_clabe: str | None = None,
                         exchange_currency: str = "MXN",
                         raw_json: str | None = None) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO fp_mxn_transactions
                    (id, pear_order_id, direction, status, amount, currency,
                     subject_id, dynamic_clabe, exchange_currency, raw_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (tx_id, pear_order_id, direction, status, amount, currency,
                  subject_id, dynamic_clabe, exchange_currency, raw_json))
            conn.commit()
        finally:
            conn.close()

    def get_transaction_by_order(self, pear_order_id: str,
                                  direction: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                """SELECT * FROM fp_mxn_transactions
                   WHERE pear_order_id = ? AND direction = ?
                   AND status != 'canceled'
                   ORDER BY created_at DESC LIMIT 1""",
                (pear_order_id, direction)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_transaction(self, tx_id: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM fp_mxn_transactions WHERE id = ?", (tx_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_transaction_status(self, tx_id: str, new_status: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """UPDATE fp_mxn_transactions
                   SET status = ?, updated_at = datetime('now')
                   WHERE id = ?""",
                (new_status, tx_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_pending_transactions(self, direction: str | None = None,
                                  older_than_minutes: int = 5) -> list[dict]:
        conn = self._connect()
        try:
            query = """
                SELECT * FROM fp_mxn_transactions
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

    # ─── WEBHOOKS ─────────────────────────────────────────────

    def log_webhook_atomic(self, notification_id: str, event_type: str,
                           transaction_id: str | None = None,
                           transaction_ids: str | None = None,
                           raw_json: str | None = None) -> bool:
        """Atomically persist webhook. Returns True if NEW, False if dup."""
        conn = self._connect()
        try:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO fp_mxn_webhook_log
                    (notification_id, event_type, transaction_id,
                     transaction_ids, handler_status, raw_json)
                VALUES (?, ?, ?, ?, 'received', ?)
            """, (notification_id, event_type, transaction_id,
                  transaction_ids, raw_json))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def mark_webhook_processed(self, notification_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                UPDATE fp_mxn_webhook_log
                SET handler_status = 'processed',
                    processed_at = datetime('now')
                WHERE notification_id = ?
            """, (notification_id,))
            conn.commit()
        finally:
            conn.close()

    def is_webhook_processed(self, notification_id: str) -> bool:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM fp_mxn_webhook_log WHERE notification_id = ?",
                (notification_id,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()
