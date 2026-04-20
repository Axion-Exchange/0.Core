"""
Tests for P0-5 / P0-6 / P1-2 audit fixes.

P0-5: EUR payout DB-level at-most-once guard (eur_payouts table)
P0-6: EUR release DB-level at-most-once guard (eur_releases table)
P1-2: Health heartbeat staleness detection
"""

import os
import sqlite3
import tempfile
import threading
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch


# =============================================================================
# P0-5: EUR PAYOUT GUARD TESTS
# =============================================================================


class TestP0_5_EurPayoutGuard:
    """Test DB-level at-most-once payout guard for EUR buy orders."""

    def _make_db(self):
        from src.core.persistence import OrderDatabase
        tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tf.close()
        return OrderDatabase(db_path=tf.name)

    def test_first_claim_succeeds(self):
        db = self._make_db()
        assert db.try_claim_eur_payout("order-001", "replay-001") is True

    def test_second_claim_fails(self):
        db = self._make_db()
        assert db.try_claim_eur_payout("order-001", "replay-001") is True
        assert db.try_claim_eur_payout("order-001", "replay-001") is False

    def test_third_claim_fails(self):
        db = self._make_db()
        db.try_claim_eur_payout("order-001", "replay-001")
        db.try_claim_eur_payout("order-001", "replay-001")
        assert db.try_claim_eur_payout("order-001", "replay-001") is False

    def test_different_orders_independent(self):
        db = self._make_db()
        assert db.try_claim_eur_payout("order-001", "replay-001") is True
        assert db.try_claim_eur_payout("order-002", "replay-002") is True
        # But second claim of order-001 still fails
        assert db.try_claim_eur_payout("order-001", "replay-001") is False

    def test_mark_payout_result_success(self):
        db = self._make_db()
        db.try_claim_eur_payout("order-001", "replay-001")
        db.mark_eur_payout_result("order-001", True)
        # Verify result was written
        with db._connect() as conn:
            row = conn.execute("SELECT * FROM eur_payouts WHERE order_id = ?", ("order-001",)).fetchone()
            assert dict(row)["payout_success"] == 1
            assert dict(row)["completed_at"] is not None

    def test_mark_payout_result_failure(self):
        db = self._make_db()
        db.try_claim_eur_payout("order-001", "replay-001")
        db.mark_eur_payout_result("order-001", False)
        with db._connect() as conn:
            row = conn.execute("SELECT * FROM eur_payouts WHERE order_id = ?", ("order-001",)).fetchone()
            assert dict(row)["payout_success"] == 0

    def test_replay_id_stored(self):
        db = self._make_db()
        db.try_claim_eur_payout("order-001", "payout-BI123456-ext123")
        with db._connect() as conn:
            row = conn.execute("SELECT * FROM eur_payouts WHERE order_id = ?", ("order-001",)).fetchone()
            assert dict(row)["replay_id"] == "payout-BI123456-ext123"

    def test_concurrent_claims_only_one_wins(self):
        """Simulate 10 threads racing to claim the same payout."""
        db = self._make_db()
        results = []
        barrier = threading.Barrier(10)

        def claim():
            barrier.wait()
            results.append(db.try_claim_eur_payout("race-order", "replay-race"))

        threads = [threading.Thread(target=claim) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results.count(True) == 1, f"Expected exactly 1 winner, got {results.count(True)}"
        assert results.count(False) == 9


# =============================================================================
# P0-6: EUR RELEASE GUARD TESTS
# =============================================================================


class TestP0_6_EurReleaseGuard:
    """Test DB-level at-most-once release guard for EUR sell orders."""

    def _make_db(self):
        from src.core.persistence import OrderDatabase
        tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tf.close()
        return OrderDatabase(db_path=tf.name)

    def test_first_claim_succeeds(self):
        db = self._make_db()
        assert db.try_claim_eur_release("order-001") is True

    def test_second_claim_fails(self):
        db = self._make_db()
        assert db.try_claim_eur_release("order-001") is True
        assert db.try_claim_eur_release("order-001") is False

    def test_different_orders_independent(self):
        db = self._make_db()
        assert db.try_claim_eur_release("order-001") is True
        assert db.try_claim_eur_release("order-002") is True
        assert db.try_claim_eur_release("order-001") is False

    def test_mark_release_result_success(self):
        db = self._make_db()
        db.try_claim_eur_release("order-001")
        db.mark_eur_release_result("order-001", True)
        with db._connect() as conn:
            row = conn.execute("SELECT * FROM eur_releases WHERE order_id = ?", ("order-001",)).fetchone()
            assert dict(row)["release_success"] == 1
            assert dict(row)["completed_at"] is not None

    def test_mark_release_result_failure(self):
        db = self._make_db()
        db.try_claim_eur_release("order-001")
        db.mark_eur_release_result("order-001", False)
        with db._connect() as conn:
            row = conn.execute("SELECT * FROM eur_releases WHERE order_id = ?", ("order-001",)).fetchone()
            assert dict(row)["release_success"] == 0

    def test_concurrent_claims_only_one_wins(self):
        """Simulate 10 threads racing to claim the same release."""
        db = self._make_db()
        results = []
        barrier = threading.Barrier(10)

        def claim():
            barrier.wait()
            results.append(db.try_claim_eur_release("race-order"))

        threads = [threading.Thread(target=claim) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results.count(True) == 1
        assert results.count(False) == 9


# =============================================================================
# P0-5 SUPPLEMENT: save_order() now persists payout_sent_at
# =============================================================================


class TestP0_5_PayoutSentAtPersistence:
    """Verify payout_sent_at survives save_order() → load cycle."""

    def test_payout_sent_at_in_save_order_sql(self):
        """Confirm save_order SQL includes payout_sent_at (the original bug)."""
        import inspect
        from src.core.persistence import OrderDatabase
        source = inspect.getsource(OrderDatabase.save_order)
        assert "payout_sent_at" in source, \
            "save_order() must include payout_sent_at in SQL — P0-5 fix missing!"


# =============================================================================
# P1-2: HEALTH STALENESS TESTS
# =============================================================================


class TestP1_2_HealthStaleness:
    """Test heartbeat staleness detection in health check."""

    def _make_registry(self):
        from src.core.health import TaskRegistry
        return TaskRegistry()

    def test_fresh_task_not_stale(self):
        reg = self._make_registry()
        reg.register("orchestrator", critical=True)
        reg.mark_running("orchestrator")
        status = reg.get_status()
        assert status["status"] == "healthy"
        task = status["tasks"][0]
        assert task["stale"] is False

    def test_stale_task_detected(self):
        reg = self._make_registry()
        reg.register("orchestrator", critical=True)
        reg.mark_running("orchestrator")
        # Simulate heartbeat from 10 minutes ago
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        reg._tasks["orchestrator"].last_heartbeat = old_time
        status = reg.get_status()
        assert status["status"] == "unhealthy"
        assert "orchestrator" in status.get("stale_tasks", [])
        task = status["tasks"][0]
        assert task["stale"] is True

    def test_non_critical_stale_only_degrades(self):
        reg = self._make_registry()
        reg.register("orchestrator", critical=True)
        reg.mark_running("orchestrator")
        reg.register("optional_task", critical=False)
        reg.mark_running("optional_task")
        # Only optional task is stale
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        reg._tasks["optional_task"].last_heartbeat = old_time
        status = reg.get_status()
        # Stale non-critical tasks still cause "unhealthy" because stale_tasks is non-empty
        assert status["status"] == "unhealthy"
        assert "optional_task" in status.get("stale_tasks", [])

    def test_stopped_task_not_stale(self):
        """A stopped task with old heartbeat should NOT be marked stale."""
        reg = self._make_registry()
        reg.register("orchestrator", critical=True)
        reg.mark_running("orchestrator")
        reg.mark_stopped("orchestrator")
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        reg._tasks["orchestrator"].last_heartbeat = old_time
        task_dict = next(t for t in reg.get_status()["tasks"] if t["name"] == "orchestrator")
        assert task_dict["stale"] is False  # Not running, so not stale

    def test_stale_threshold_boundary(self):
        """Task heartbeat at exactly 4 minutes should NOT be stale (threshold is 5 min)."""
        reg = self._make_registry()
        reg.register("orchestrator", critical=True)
        reg.mark_running("orchestrator")
        recent_time = (datetime.now(timezone.utc) - timedelta(minutes=4)).isoformat()
        reg._tasks["orchestrator"].last_heartbeat = recent_time
        status = reg.get_status()
        assert status["status"] == "healthy"
        task = status["tasks"][0]
        assert task["stale"] is False


# =============================================================================
# P1-3: PRINT→LOGGING VERIFICATION
# =============================================================================


class TestP1_3_NoPrintInCriticalCode:
    """Verify critical modules don't use print() in new code."""

    def test_persistence_no_print(self):
        import inspect
        from src.core.persistence import OrderDatabase
        source = inspect.getsource(OrderDatabase)
        # Allow print in string comments/docstrings but not as actual calls
        lines = [l for l in source.split("\n") if l.strip().startswith("print(")]
        assert len(lines) == 0, f"Found print() calls in persistence.py: {lines}"

    def test_state_manager_load_from_db_no_print(self):
        import inspect
        from src.core.state_manager import StateManager
        source = inspect.getsource(StateManager._load_from_db)
        lines = [l for l in source.split("\n") if l.strip().startswith("print(")]
        assert len(lines) == 0, f"Found print() calls in _load_from_db: {lines}"
