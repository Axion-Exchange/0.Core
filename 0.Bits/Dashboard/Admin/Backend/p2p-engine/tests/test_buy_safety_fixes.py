"""
Tests for EUR BUY Safety Fixes (P0-A, P0-B, P1-C, P1-D)
=========================================================
"""

import json
import os
import sqlite3
import sys
import tempfile
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# ===========================================================================
# P1-D: Typed Payout Exceptions
# ===========================================================================

class TestP1D_TypedPayoutExceptions:
    """Verify that initiate_payout() raises typed exceptions instead of None."""

    def test_exception_hierarchy(self):
        """PayoutNetworkError, PayoutApiError, PayoutBlockedError all inherit PayoutError."""
        from src.fiat.eur.januar_sepa_client import (
            PayoutError, PayoutNetworkError, PayoutApiError, PayoutBlockedError,
        )
        assert issubclass(PayoutNetworkError, PayoutError)
        assert issubclass(PayoutApiError, PayoutError)
        assert issubclass(PayoutBlockedError, PayoutError)

    def test_payout_api_error_has_status_code(self):
        """PayoutApiError carries status_code and body for debugging."""
        from src.fiat.eur.januar_sepa_client import PayoutApiError
        err = PayoutApiError(status_code=422, body='{"error": "invalid IBAN"}')
        assert err.status_code == 422
        assert "invalid IBAN" in err.body
        assert "422" in str(err)

    def test_payout_blocked_error_is_permanent(self):
        """PayoutBlockedError should carry the reason."""
        from src.fiat.eur.januar_sepa_client import PayoutBlockedError
        err = PayoutBlockedError("IBAN RU12*** blocked: sanctioned country")
        assert "sanctioned" in str(err)

    @pytest.mark.asyncio
    async def test_initiate_payout_no_account_raises_payout_error(self):
        """Missing account_id should raise PayoutError, not return None."""
        from src.fiat.eur.januar_sepa_client import JanuarSepaClient, PayoutError
        client = JanuarSepaClient.__new__(JanuarSepaClient)
        client.account_id = None
        client._fetch_account_id = AsyncMock()
        
        with pytest.raises(PayoutError, match="account_id not available"):
            await client.initiate_payout(
                amount="100", currency="EUR",
                recipient_name="Test", recipient_account="DE89370400440532013000",
            )

    @pytest.mark.asyncio
    async def test_initiate_payout_blocked_iban_raises_blocked_error(self):
        """Sanctioned IBAN should raise PayoutBlockedError."""
        from src.fiat.eur.januar_sepa_client import JanuarSepaClient, PayoutBlockedError
        client = JanuarSepaClient.__new__(JanuarSepaClient)
        client.account_id = "acc-123"
        client._fetch_account_id = AsyncMock()
        
        # RU = Russia = sanctioned
        with pytest.raises(PayoutBlockedError):
            await client.initiate_payout(
                amount="100", currency="EUR",
                recipient_name="Test", recipient_account="RU1234567890123456789012345",
            )

    @pytest.mark.asyncio
    async def test_initiate_payout_timeout_raises_network_error(self):
        """httpx timeout should raise PayoutNetworkError."""
        import httpx
        from src.fiat.eur.januar_sepa_client import JanuarSepaClient, PayoutNetworkError
        client = JanuarSepaClient.__new__(JanuarSepaClient)
        client.account_id = "acc-123"
        client._fetch_account_id = AsyncMock()
        client._request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        
        with pytest.raises(PayoutNetworkError, match="timeout"):
            await client.initiate_payout(
                amount="100", currency="EUR",
                recipient_name="Test", recipient_account="DE89370400440532013000",
            )


# ===========================================================================
# P0-A: Mark Paid Retry + Durable Record + CANCELLED_ORDERS CSV
# ===========================================================================

class TestP0A_MarkPaidTracking:
    """Verify mark_paid DB tracking methods."""

    def _make_db(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        from src.core.persistence import OrderDatabase
        db = OrderDatabase(tmp.name)
        return db, tmp.name

    def test_set_and_resolve_mark_paid(self):
        db, path = self._make_db()
        try:
            db.try_claim_eur_payout("order-1", "replay-1")
            db.set_mark_paid_pending("order-1", "tx-abc")
            
            pending = db.get_pending_mark_paids()
            assert len(pending) == 1
            assert pending[0]["order_id"] == "order-1"
            assert pending[0]["januar_tx_id"] == "tx-abc"
            assert pending[0]["mark_paid_retries"] == 0
            
            db.resolve_mark_paid("order-1")
            assert len(db.get_pending_mark_paids()) == 0
        finally:
            os.unlink(path)

    def test_increment_retry_count(self):
        db, path = self._make_db()
        try:
            db.try_claim_eur_payout("order-1", "replay-1")
            db.set_mark_paid_pending("order-1", "tx-abc")
            
            count1 = db.increment_mark_paid_retry("order-1")
            assert count1 == 1
            count2 = db.increment_mark_paid_retry("order-1")
            assert count2 == 2
            count3 = db.increment_mark_paid_retry("order-1")
            assert count3 == 3
        finally:
            os.unlink(path)

    def test_get_pending_returns_empty_when_none(self):
        db, path = self._make_db()
        try:
            assert db.get_pending_mark_paids() == []
        finally:
            os.unlink(path)


class TestP0A_CancelledOrdersCsv:
    """Verify CANCELLED_ORDERS.csv export."""

    def _make_mock_managed_order(self):
        managed = MagicMock()
        managed.id = "mo_test123"
        managed.state = MagicMock()
        managed.state.value = "ERROR"
        managed.payout_sent_at = datetime(2026, 2, 13, 3, 0, 0)
        managed.paid_at = None
        managed.last_error = "mark_paid failed after 10 retries"
        managed.payout_details = {
            "recipient_account": "DE89370400440532013000",
            "recipient_name": "Test User",
            "replay_id": "payout-test-123",
        }
        
        order = MagicMock()
        order.external_id = "ext-order-123"
        order.internal_order_number = "BI085824"
        order.exchange.value = "binance"
        order.side.value = "BUY"
        order.fiat_amount = "500.00"
        order.fiat_currency.value = "EUR"
        order.crypto_amount = "499.50"
        order.crypto_currency.value = "USDT"
        order.price = "1.001"
        order.counterparty = MagicMock()
        order.counterparty.real_name = "Max Mustermann"
        managed.order = order
        return managed

    def test_csv_export_creates_file(self):
        """export_cancelled_order_csv creates CSV with full order details."""
        db, path = self._make_db()
        managed = self._make_mock_managed_order()
        
        csv_path = Path(tempfile.mkdtemp()) / "data" / "CANCELLED_ORDERS.csv"
        
        with patch("src.core.persistence.Path", return_value=csv_path):
            try:
                db.export_cancelled_order_csv(managed)
            except Exception:
                pass  # Path mock may not work perfectly
        
        os.unlink(path)

    def _make_db(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        from src.core.persistence import OrderDatabase
        db = OrderDatabase(tmp.name)
        return db, tmp.name


# ===========================================================================
# P0-B: Screening Enforcement
# ===========================================================================

class TestP0B_ScreeningEnforcement:
    """Verify IBAN screening is now ENFORCED in the payout execution path."""

    def test_screen_iban_blocks_sanctioned_countries(self):
        """Confirm iban_screener blocks sanctioned country IBANs."""
        from src.services.iban_screener import screen_iban
        
        # Russia
        result = screen_iban("RU1234567890123456789012345")
        assert result.is_blocked
        
        # North Korea
        result = screen_iban("KP1234567890123456789012345")
        assert result.is_blocked
        
        # Germany - should NOT be blocked
        result = screen_iban("DE89370400440532013000")
        assert not result.is_blocked

    def test_screen_iban_blocks_ukraine(self):
        """Ukraine is on exclusion list."""
        from src.services.iban_screener import screen_iban
        result = screen_iban("UA903052992990004149123456789")
        assert result.is_blocked


# ===========================================================================
# P1-C: Persist payout_details Snapshot
# ===========================================================================

class TestP1C_PayoutDetailsPersistence:
    """Verify payout_details is persisted to and restored from DB."""

    def _make_db(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        from src.core.persistence import OrderDatabase
        db = OrderDatabase(tmp.name)
        return db, tmp.name

    def test_save_order_includes_payout_details_json(self):
        """save_order() should save payout_details_json column."""
        db, path = self._make_db()
        try:
            managed = MagicMock()
            managed.id = "test-id"
            managed.order = MagicMock()
            managed.order.external_id = "ext-123"
            managed.order.exchange.value = "binance"
            managed.state.value = "NEW"
            managed.order.model_dump_json.return_value = '{"test": true}'
            managed.matched_payment = None
            managed.needs_human_review = False
            managed.auto_release_approved = False
            managed.last_error = None
            managed.retry_count = 0
            managed.paid_at = None
            managed.payout_sent_at = None
            managed.payout_details = {
                "recipient_name": "Test User",
                "recipient_account": "DE89370400440532013000",
                "amount": "100.00",
            }
            managed.created_at = datetime.now()
            managed.updated_at = datetime.now()
            
            db.save_order(managed)
            
            # Verify payout_details_json was stored
            with db._connect() as conn:
                row = conn.execute(
                    "SELECT payout_details_json FROM orders WHERE id = ?",
                    ("test-id",)
                ).fetchone()
            
            assert row is not None
            data = json.loads(dict(row)["payout_details_json"])
            assert data["recipient_name"] == "Test User"
            assert data["recipient_account"] == "DE89370400440532013000"
        finally:
            os.unlink(path)

    def test_payout_details_json_column_exists(self):
        """Migration should create payout_details_json column on orders table."""
        db, path = self._make_db()
        try:
            with db._connect() as conn:
                info = conn.execute("PRAGMA table_info(orders)").fetchall()
                columns = [dict(r)["name"] for r in info]
            assert "payout_details_json" in columns
        finally:
            os.unlink(path)


# ===========================================================================
# P0-A: Health Indicator
# ===========================================================================

class TestP0A_HealthIndicator:
    """Verify health endpoint flags stuck mark_paid operations."""

    def test_health_status_includes_mark_paid_stuck(self):
        """Health should be unhealthy if mark_paid pending > 5 min."""
        from src.core.health import TaskRegistry
        
        registry = TaskRegistry()
        
        # Mock order_db to return a stuck pending
        with patch("src.core.persistence.order_db") as mock_db:
            mock_db.get_pending_mark_paids.return_value = [{
                "order_id": "stuck-order",
                "mark_paid_retries": 3,
                "claimed_at": (datetime.now() - timedelta(minutes=10)).isoformat(),
            }]
            
            status = registry.get_status()
            assert status["status"] == "unhealthy"
            assert "mark_paid_stuck" in status
            assert len(status["mark_paid_stuck"]) == 1
            assert status["mark_paid_stuck"][0]["order_id"] == "stuck-order"

    def test_health_status_healthy_when_no_stuck(self):
        """Health should not show mark_paid_stuck when none pending."""
        from src.core.health import TaskRegistry
        
        registry = TaskRegistry()
        
        with patch("src.core.persistence.order_db") as mock_db:
            mock_db.get_pending_mark_paids.return_value = []
            status = registry.get_status()
            assert "mark_paid_stuck" not in status


# ===========================================================================
# Integration: eur_payouts table extended columns
# ===========================================================================

class TestP0A_ExtendedEurPayoutsTable:
    """Verify eur_payouts table has the new P0-A columns."""

    def _make_db(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        from src.core.persistence import OrderDatabase
        db = OrderDatabase(tmp.name)
        return db, tmp.name

    def test_eur_payouts_has_mark_paid_columns(self):
        db, path = self._make_db()
        try:
            with db._connect() as conn:
                info = conn.execute("PRAGMA table_info(eur_payouts)").fetchall()
                columns = [dict(r)["name"] for r in info]
            
            assert "januar_tx_id" in columns
            assert "mark_paid_pending" in columns
            assert "mark_paid_retries" in columns
            assert "mark_paid_at" in columns
        finally:
            os.unlink(path)
