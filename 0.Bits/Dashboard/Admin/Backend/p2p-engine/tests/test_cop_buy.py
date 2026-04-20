"""
COP BUY Flow Tests
==================
Unit tests for the COP BUY payout automation:
- State machine transitions
- Info extraction (account_number, account_type)
- Payout claim (at-most-once guard)
- mark_paid retry logic
"""

import os
import sys
import tempfile
import sqlite3
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fiat.cop.cop_types import COPOrder, COPOrderState
from src.fiat.cop.cop_tracker import COPOrderTracker
from src.fiat.cop.info_extractor import CustomerInfo, COPInfoExtractor


# ============================================================================
# State Machine Tests
# ============================================================================

class TestBuyStateTransitions:
    """Verify BUY state machine transitions are enforced correctly."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_cop.db")
        self.tracker = COPOrderTracker(db_path=self.db_path)

    def test_buy_order_creates_with_collecting_state(self):
        """BUY orders start in COLLECTING_BANK_INFO."""
        order = self.tracker.create_order(
            binance_order_id="BUY001",
            amount_cop="1000000",
            amount_usdt="250",
            order_side="BUY",
        )
        assert order.state == COPOrderState.COLLECTING_BANK_INFO
        assert order.order_side == "BUY"
        assert order.is_buy is True

    def test_sell_order_creates_with_awaiting_info_state(self):
        """SELL orders still start in AWAITING_INFO (backward compat)."""
        order = self.tracker.create_order(
            binance_order_id="SELL001",
            amount_cop="1000000",
            amount_usdt="250",
        )
        assert order.state == COPOrderState.AWAITING_INFO
        assert order.order_side == "SELL"
        assert order.is_buy is False

    def test_buy_happy_path_transitions(self):
        """Complete BUY flow: COLLECTING_BANK_INFO → ... → COMPLETED."""
        order = self.tracker.create_order(
            binance_order_id="BUY002", amount_cop="1000000", order_side="BUY",
        )
        # COLLECTING_BANK_INFO → PAYOUT_PENDING
        result = self.tracker.transition("BUY002", COPOrderState.PAYOUT_PENDING)
        assert result is not None
        assert result.state == COPOrderState.PAYOUT_PENDING

        # PAYOUT_PENDING → PAYOUT_SENT
        result = self.tracker.transition("BUY002", COPOrderState.PAYOUT_SENT)
        assert result is not None
        assert result.state == COPOrderState.PAYOUT_SENT

        # PAYOUT_SENT → MARK_PAID_PENDING
        result = self.tracker.transition("BUY002", COPOrderState.MARK_PAID_PENDING)
        assert result is not None
        assert result.state == COPOrderState.MARK_PAID_PENDING

        # MARK_PAID_PENDING → COMPLETED
        result = self.tracker.transition("BUY002", COPOrderState.COMPLETED)
        assert result is not None
        assert result.state == COPOrderState.COMPLETED

    def test_buy_direct_payout_sent_to_completed(self):
        """PAYOUT_SENT can go directly to COMPLETED (skipping MARK_PAID_PENDING)."""
        self.tracker.create_order(
            binance_order_id="BUY003", amount_cop="500000", order_side="BUY",
        )
        self.tracker.transition("BUY003", COPOrderState.PAYOUT_PENDING)
        self.tracker.transition("BUY003", COPOrderState.PAYOUT_SENT)
        result = self.tracker.transition("BUY003", COPOrderState.COMPLETED)
        assert result is not None
        assert result.state == COPOrderState.COMPLETED

    def test_buy_invalid_transition_rejected(self):
        """Invalid transitions are rejected."""
        self.tracker.create_order(
            binance_order_id="BUY004", amount_cop="500000", order_side="BUY",
        )
        # Can't go from COLLECTING_BANK_INFO → COMPLETED directly
        result = self.tracker.transition("BUY004", COPOrderState.COMPLETED)
        assert result is None

    def test_buy_terminal_state_cannot_leave(self):
        """COMPLETED is terminal — no outgoing transitions."""
        self.tracker.create_order(
            binance_order_id="BUY005", amount_cop="500000", order_side="BUY",
        )
        self.tracker.transition("BUY005", COPOrderState.PAYOUT_PENDING)
        self.tracker.transition("BUY005", COPOrderState.PAYOUT_SENT)
        self.tracker.transition("BUY005", COPOrderState.COMPLETED)
        # Try to leave COMPLETED
        result = self.tracker.transition("BUY005", COPOrderState.PAYOUT_PENDING)
        assert result is None

    def test_buy_order_can_go_to_manual_review(self):
        """BUY orders can be escalated to MANUAL_REVIEW from any active state."""
        self.tracker.create_order(
            binance_order_id="BUY006", amount_cop="500000", order_side="BUY",
        )
        result = self.tracker.transition("BUY006", COPOrderState.MANUAL_REVIEW)
        assert result is not None
        assert result.state == COPOrderState.MANUAL_REVIEW


# ============================================================================
# Payout Claim (At-Most-Once) Tests
# ============================================================================

class TestPayoutClaim:
    """Verify at-most-once payout guard via cop_payout_claims table."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_cop.db")
        self.tracker = COPOrderTracker(db_path=self.db_path)

    def test_first_claim_succeeds(self):
        """First payout claim should succeed."""
        assert self.tracker.try_claim_payout("BUY001") is True

    def test_second_claim_after_success_fails(self):
        """After marking payout as successful, claim should fail."""
        self.tracker.try_claim_payout("BUY002")
        self.tracker.mark_payout_result("BUY002", True)
        assert self.tracker.try_claim_payout("BUY002") is False

    def test_mark_payout_result(self):
        """mark_payout_result records outcome."""
        self.tracker.try_claim_payout("BUY003")
        self.tracker.mark_payout_result("BUY003", False)
        # After failure, a new claim should not be possible (row exists)
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT payout_success FROM cop_payout_claims WHERE order_id = ?",
            ("BUY003",),
        ).fetchone()
        conn.close()
        assert row[0] == 0  # failure recorded


# ============================================================================
# BUY Info Extraction Tests
# ============================================================================

class TestBuyInfoExtraction:
    """Test CustomerInfo BUY-specific fields and regex extraction."""

    def test_is_complete_for_buy_all_fields(self):
        info = CustomerInfo(
            name="Juan Perez", cc="1090421192",
            bank_code="1007", account_number="12345678901",
            account_type="savings",
        )
        assert info.is_complete_for_buy() is True

    def test_is_complete_for_buy_missing_account(self):
        info = CustomerInfo(
            name="Juan Perez", cc="1090421192",
            bank_code="1007",
        )
        assert info.is_complete_for_buy() is False

    def test_missing_buy_fields(self):
        info = CustomerInfo(name="Juan Perez", cc="1090421192")
        missing = info.missing_buy_fields()
        assert "banco" in missing
        assert "número de cuenta" in missing
        assert "tipo de cuenta (ahorros/corriente)" in missing
        assert "nombre completo" not in missing  # present
        assert "cédula" not in missing  # present

    def test_sell_is_complete_unchanged(self):
        """SELL flow is_complete still works (backward compat)."""
        info = CustomerInfo(
            name="Maria", cc="45678901", email="m@x.com", bank_code="1007",
        )
        assert info.is_complete() is True

    def test_regex_extract_account_type_ahorros(self):
        extractor = COPInfoExtractor()
        info = extractor._regex_extract("Cuenta de ahorros Bancolombia")
        assert info.account_type == "savings"

    def test_regex_extract_account_type_corriente(self):
        extractor = COPInfoExtractor()
        info = extractor._regex_extract("Cuenta corriente BBVA")
        assert info.account_type == "checking"

    def test_regex_extract_account_number_labeled(self):
        extractor = COPInfoExtractor()
        info = extractor._regex_extract(
            "Juan Perez CC 1090421192 cuenta: 123456789012 ahorros Bancolombia"
        )
        assert info.account_number == "123456789012"

    def test_regex_extract_account_number_unlabeled(self):
        extractor = COPInfoExtractor()
        info = extractor._regex_extract(
            "1090421192\n4567890123456\nahorros bancolombia"
        )
        # CC is 1090421192, account should be 4567890123456
        assert info.account_number == "4567890123456"

    def test_buy_info_merge_with_previous(self):
        """Merging preserves BUY fields from previous extraction."""
        import asyncio
        extractor = COPInfoExtractor()
        previous = CustomerInfo(
            name="Juan Perez", cc="1090421192",
            bank_code="1007", bank_name="Bancolombia",
        )
        new_msgs = ["987654321012 ahorros"]
        result = asyncio.get_event_loop().run_until_complete(
            extractor.extract(new_msgs, previous=previous)
        )
        assert result.name == "Juan Perez"
        assert result.bank_code == "1007"
        assert result.account_number == "987654321012"
        assert result.account_type == "savings"


# ============================================================================
# Buy Customer Info Tracker Tests
# ============================================================================

class TestBuyCustomerInfo:
    """Test tracker's set_buy_customer_info method."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_cop.db")
        self.tracker = COPOrderTracker(db_path=self.db_path)

    def test_set_buy_info_saves_all_fields(self):
        self.tracker.create_order(
            binance_order_id="BUY010", amount_cop="1000000", order_side="BUY",
        )
        self.tracker.set_buy_customer_info(
            "BUY010", name="Juan Perez", cc="1090421192",
            email="juan@x.com", bank_code="1007", bank_name="Bancolombia",
            account_number="12345678901", account_type="savings",
        )
        order = self.tracker.get_order("BUY010")
        assert order.customer_name == "Juan Perez"
        assert order.customer_cc == "1090421192"
        assert order.seller_account_number == "12345678901"
        assert order.seller_account_type == "savings"

    def test_set_buy_info_blocked_in_wrong_state(self):
        self.tracker.create_order(
            binance_order_id="BUY011", amount_cop="1000000", order_side="BUY",
        )
        self.tracker.transition("BUY011", COPOrderState.PAYOUT_PENDING)
        # Should be blocked in PAYOUT_PENDING
        self.tracker.set_buy_customer_info(
            "BUY011", name="Juan", cc="12345678",
            email="j@x.com", bank_code="1007",
            account_number="999", account_type="savings",
        )
        order = self.tracker.get_order("BUY011")
        assert order.customer_name is None  # Not saved


# ============================================================================
# Mark Paid Retry Tests
# ============================================================================

class TestMarkPaidRetries:
    """Test mark_paid retry counter and resolution."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_cop.db")
        self.tracker = COPOrderTracker(db_path=self.db_path)

    def test_increment_retries(self):
        self.tracker.create_order(
            binance_order_id="BUY020", amount_cop="1000000", order_side="BUY",
        )
        count = self.tracker.increment_mark_paid_retries("BUY020")
        assert count == 1
        count = self.tracker.increment_mark_paid_retries("BUY020")
        assert count == 2

    def test_resolve_mark_paid(self):
        self.tracker.create_order(
            binance_order_id="BUY021", amount_cop="1000000", order_side="BUY",
        )
        self.tracker.increment_mark_paid_retries("BUY021")
        self.tracker.increment_mark_paid_retries("BUY021")
        self.tracker.resolve_mark_paid("BUY021")
        order = self.tracker.get_order("BUY021")
        assert order.mark_paid_retries == 0
        assert order.mark_paid_at is not None

    def test_payout_tx_id_saved(self):
        self.tracker.create_order(
            binance_order_id="BUY022", amount_cop="1000000", order_side="BUY",
        )
        self.tracker.set_payout_tx_id("BUY022", "fp-tx-12345")
        order = self.tracker.get_order("BUY022")
        assert order.facilitapay_payout_tx_id == "fp-tx-12345"
        assert order.payout_sent_at is not None


# ============================================================================
# Schema Migration Tests
# ============================================================================

class TestSchemaMigration:
    """Test that DB migration adds new columns without breaking existing data."""

    def test_migration_adds_buy_columns(self):
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test_migration.db")

        # Create a "v1" database without BUY columns
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cop_orders (
                binance_order_id TEXT PRIMARY KEY,
                binance_external_id TEXT,
                customer_name TEXT, customer_cc TEXT, customer_email TEXT,
                bank_code TEXT, bank_name TEXT,
                amount_cop TEXT, amount_usdt TEXT,
                facilitapay_subject_id TEXT, facilitapay_tx_id TEXT, payment_url TEXT,
                state TEXT, binance_buyer_name TEXT,
                created_at TEXT, link_expires_at TEXT,
                welcome_sent INTEGER, chat_messages TEXT
            )
        """)
        conn.execute("""
            INSERT INTO cop_orders VALUES (
                'OLD001', NULL,
                'Old User', '12345678', 'old@x.com',
                '1007', 'Bancolombia',
                '1000000', '250',
                NULL, NULL, NULL,
                'awaiting_info', 'OldBuyer',
                '2024-01-01T00:00:00', NULL,
                0, ''
            )
        """)
        conn.commit()
        conn.close()

        # Now init tracker — this should migrate
        tracker = COPOrderTracker(db_path=db_path)

        # Old order should still be readable
        order = tracker.get_order("OLD001")
        assert order is not None
        assert order.customer_name == "Old User"
        assert order.order_side == "SELL"  # default
        assert order.seller_account_number is None  # new column, NULL

        # New BUY order should work
        buy_order = tracker.create_order(
            binance_order_id="NEW001", amount_cop="500000", order_side="BUY",
        )
        assert buy_order.state == COPOrderState.COLLECTING_BANK_INFO


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
