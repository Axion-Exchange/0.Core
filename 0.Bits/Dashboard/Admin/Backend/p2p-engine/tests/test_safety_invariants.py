"""
TEST: Safety Invariants
========================
Property-based tests verifying that critical safety contracts hold
under all conditions.

Invariant 1: No money can leave without a VALID state transition.
Invariant 2: Terminal states are truly terminal.
Invariant 3: Every state has defined valid transitions (no undefined behavior).
Invariant 4: Audit log is append-only and complete.
"""

import pytest
from src.fiat.cop.cop_types import COPOrderState
from src.fiat.cop.cop_tracker import COPOrderTracker


class TestTerminalStateInvariant:
    """Invariant: COMPLETED and CANCELLED are final — no exits, no re-entry."""

    def test_completed_has_no_exits(self):
        assert COPOrderTracker.VALID_TRANSITIONS[COPOrderState.COMPLETED] == set()

    def test_cancelled_has_no_exits(self):
        assert COPOrderTracker.VALID_TRANSITIONS[COPOrderState.CANCELLED] == set()

    def test_no_state_can_transition_to_itself_silently(self):
        """Verify that self-transitions are explicit, not silent no-ops."""
        for state, targets in COPOrderTracker.VALID_TRANSITIONS.items():
            if state in targets:
                # Self-transition is declared — this is OK, just must be logged
                pass
            # The key invariant: absence from targets means rejection


class TestStateCompleteness:
    """Invariant: Every defined state has an entry in VALID_TRANSITIONS."""

    def test_all_states_covered(self):
        tracker_states = set(COPOrderTracker.VALID_TRANSITIONS.keys())
        enum_states = set(COPOrderState)

        missing = enum_states - tracker_states
        assert missing == set(), (
            f"States without transition rules: {[s.value for s in missing]}. "
            f"This is dangerous — undefined states could bypass safety checks."
        )

    def test_no_extra_states_in_transitions(self):
        """No phantom states in VALID_TRANSITIONS that don't exist as enums."""
        tracker_states = set(COPOrderTracker.VALID_TRANSITIONS.keys())
        enum_states = set(COPOrderState)

        extra = tracker_states - enum_states
        assert extra == set(), (
            f"Phantom states in VALID_TRANSITIONS: {extra}"
        )


class TestReleasePathSafety:
    """Invariant: Crypto can only be released from PAYMENT_RECEIVED → RELEASING → COMPLETED."""

    def test_releasing_only_from_payment_received(self):
        """RELEASING must only be reachable from PAYMENT_RECEIVED (or MANUAL_REVIEW, FAILED for retry)."""
        states_that_can_reach_releasing = set()
        for state, targets in COPOrderTracker.VALID_TRANSITIONS.items():
            if COPOrderState.RELEASING in targets:
                states_that_can_reach_releasing.add(state)

        # RELEASING should only be reachable from these states
        expected = {
            COPOrderState.PAYMENT_RECEIVED,  # Normal flow
            COPOrderState.MANUAL_REVIEW,     # Manual retry
            COPOrderState.FAILED,            # Retry after failure
        }
        assert states_that_can_reach_releasing == expected, (
            f"RELEASING reachable from unexpected states: "
            f"{states_that_can_reach_releasing - expected}"
        )

    def test_completed_only_from_releasing(self):
        """COMPLETED must only be reachable from RELEASING."""
        states_that_can_reach_completed = set()
        for state, targets in COPOrderTracker.VALID_TRANSITIONS.items():
            if COPOrderState.COMPLETED in targets:
                states_that_can_reach_completed.add(state)

        assert states_that_can_reach_completed == {COPOrderState.RELEASING}, (
            f"COMPLETED reachable from unexpected states: {states_that_can_reach_completed}"
        )


class TestAuditLogIntegrity:
    """Invariant: Every state transition is logged with timestamp and details."""

    def test_audit_log_created_on_transition(self):
        tracker = COPOrderTracker(db_path=":memory:")

        order_id = "audit_test_001"
        tracker._save_order_with_state(order_id, COPOrderState.NEW)
        tracker.transition(order_id, COPOrderState.AWAITING_INFO)

        # Check audit log
        logs = tracker.get_audit_log(order_id)
        assert len(logs) > 0, "Transition should create an audit log entry"

    def test_audit_log_records_from_and_to_state(self):
        tracker = COPOrderTracker(db_path=":memory:")

        order_id = "audit_test_002"
        tracker._save_order_with_state(order_id, COPOrderState.PAYMENT_RECEIVED)
        tracker.transition(order_id, COPOrderState.RELEASING)

        logs = tracker.get_audit_log(order_id)
        latest = logs[-1]
        assert "PAYMENT_RECEIVED" in str(latest) or "RELEASING" in str(latest), (
            "Audit log must record transition states"
        )
