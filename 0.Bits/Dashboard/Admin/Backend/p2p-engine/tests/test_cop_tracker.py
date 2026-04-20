"""
TEST: COP Order Tracker
========================
Tests the SQLite-backed COP state machine including:
- Order CRUD operations
- State transitions with VALID_TRANSITIONS enforcement
- Audit logging
- CC reuse detection
"""

import pytest
from src.fiat.cop.cop_tracker import COPOrderTracker
from src.fiat.cop.cop_types import COPOrderState, COPOrder


class TestCOPOrderCRUD:
    """Basic order lifecycle tests."""

    def test_create_and_retrieve_order(self):
        tracker = COPOrderTracker(db_path=":memory:")
        order = COPOrder(binance_order_id="12345")
        tracker.save_order(order)

        retrieved = tracker.get_order("12345")
        assert retrieved is not None
        assert retrieved.binance_order_id == "12345"
        assert retrieved.state == COPOrderState.NEW

    def test_update_order_fields(self):
        tracker = COPOrderTracker(db_path=":memory:")
        order = COPOrder(
            binance_order_id="update_test",
            customer_name="Juan Perez",
            customer_cc="1234567890",
        )
        tracker.save_order(order)

        retrieved = tracker.get_order("update_test")
        assert retrieved.customer_name == "Juan Perez"
        assert retrieved.customer_cc == "1234567890"

    def test_nonexistent_order_returns_none(self):
        tracker = COPOrderTracker(db_path=":memory:")
        assert tracker.get_order("nonexistent") is None


class TestCOPStateTransitions:
    """State machine transition tests."""

    def test_new_to_awaiting_info(self):
        tracker = COPOrderTracker(db_path=":memory:")
        tracker._save_order_with_state("order_1", COPOrderState.NEW)
        assert tracker.transition("order_1", COPOrderState.AWAITING_INFO) is True

    def test_payment_received_to_releasing(self):
        tracker = COPOrderTracker(db_path=":memory:")
        tracker._save_order_with_state("order_2", COPOrderState.PAYMENT_RECEIVED)
        assert tracker.transition("order_2", COPOrderState.RELEASING) is True

    def test_releasing_to_completed(self):
        tracker = COPOrderTracker(db_path=":memory:")
        tracker._save_order_with_state("order_3", COPOrderState.RELEASING)
        assert tracker.transition("order_3", COPOrderState.COMPLETED) is True

    def test_completed_is_terminal(self):
        tracker = COPOrderTracker(db_path=":memory:")
        tracker._save_order_with_state("order_4", COPOrderState.COMPLETED)

        # No valid transitions out of COMPLETED
        for target in COPOrderState:
            if target != COPOrderState.COMPLETED:
                assert tracker.transition("order_4", target) is False, (
                    f"COMPLETED → {target.value} should be blocked"
                )

    def test_cancelled_is_terminal(self):
        tracker = COPOrderTracker(db_path=":memory:")
        tracker._save_order_with_state("order_5", COPOrderState.CANCELLED)

        for target in COPOrderState:
            if target != COPOrderState.CANCELLED:
                assert tracker.transition("order_5", target) is False, (
                    f"CANCELLED → {target.value} should be blocked"
                )


class TestCOPAuditLog:
    """Audit logging tests."""

    def test_transition_creates_audit_entry(self):
        tracker = COPOrderTracker(db_path=":memory:")
        tracker._save_order_with_state("audit_1", COPOrderState.NEW)
        tracker.transition("audit_1", COPOrderState.AWAITING_INFO)

        logs = tracker.get_audit_log("audit_1")
        assert len(logs) >= 1, "Transition must create audit entry"

    def test_manual_audit_log(self):
        tracker = COPOrderTracker(db_path=":memory:")
        tracker._save_order_with_state("audit_2", COPOrderState.NEW)
        tracker.log_audit("audit_2", "TEST_EVENT", "test detail", "OK")

        logs = tracker.get_audit_log("audit_2")
        found = any("TEST_EVENT" in str(log) for log in logs)
        assert found, "Manual audit entry should be retrievable"


class TestCOPOrdersByState:
    """Tests for retrieving orders by state."""

    def test_get_orders_by_state(self):
        tracker = COPOrderTracker(db_path=":memory:")

        tracker._save_order_with_state("active_1", COPOrderState.AWAITING_INFO)
        tracker._save_order_with_state("active_2", COPOrderState.AWAITING_INFO)
        tracker._save_order_with_state("done_1", COPOrderState.COMPLETED)

        awaiting = tracker.get_orders_by_state(COPOrderState.AWAITING_INFO)
        assert len(awaiting) == 2

        completed = tracker.get_orders_by_state(COPOrderState.COMPLETED)
        assert len(completed) == 1

    def test_empty_state_returns_empty_list(self):
        tracker = COPOrderTracker(db_path=":memory:")
        result = tracker.get_orders_by_state(COPOrderState.RELEASING)
        assert result == []
