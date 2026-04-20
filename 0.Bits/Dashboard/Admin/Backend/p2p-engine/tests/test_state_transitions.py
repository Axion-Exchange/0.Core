"""
TEST: State Transition Exhaustive Tests
========================================
Verifies the state machine enforces all VALID_TRANSITIONS constraints.

Tests:
1. Every valid transition is accepted.
2. Every invalid transition is rejected.
3. Terminal states (COMPLETED, CANCELLED) block ALL transitions out.
4. Force=True cannot bypass terminal states (S1 fix).
"""

import pytest
from src.fiat.cop.cop_types import COPOrderState
from src.fiat.cop.cop_tracker import COPOrderTracker


# ---------------------------------------------------------------------------
# COP State Machine Tests
# ---------------------------------------------------------------------------

class TestCOPValidTransitions:
    """Test every arrow in the COP state machine."""

    VALID_TRANSITIONS = COPOrderTracker.VALID_TRANSITIONS

    def test_all_states_are_represented(self):
        """Every COPOrderState must have a key in VALID_TRANSITIONS."""
        for state in COPOrderState:
            assert state in self.VALID_TRANSITIONS, (
                f"State {state.value} is missing from VALID_TRANSITIONS"
            )

    def test_valid_transitions_accepted(self):
        """Every documented valid transition should succeed."""
        tracker = COPOrderTracker(db_path=":memory:")

        for from_state, to_states in self.VALID_TRANSITIONS.items():
            for to_state in to_states:
                # Create a fresh order in from_state
                order_id = f"test_{from_state.value}_to_{to_state.value}"
                tracker._save_order_with_state(order_id, from_state)

                # Transition should succeed
                result = tracker.transition(order_id, to_state)
                assert result is True, (
                    f"Valid transition {from_state.value} → {to_state.value} was rejected"
                )

    def test_invalid_transitions_rejected(self):
        """Transitions NOT in VALID_TRANSITIONS should be rejected."""
        tracker = COPOrderTracker(db_path=":memory:")

        all_states = set(COPOrderState)

        for from_state, valid_to_states in self.VALID_TRANSITIONS.items():
            invalid_to_states = all_states - valid_to_states - {from_state}
            for to_state in invalid_to_states:
                order_id = f"test_invalid_{from_state.value}_to_{to_state.value}"
                tracker._save_order_with_state(order_id, from_state)

                result = tracker.transition(order_id, to_state)
                assert result is False, (
                    f"Invalid transition {from_state.value} → {to_state.value} was accepted"
                )

    def test_terminal_states_block_all_transitions(self):
        """COMPLETED and CANCELLED must have ZERO valid outgoing transitions."""
        terminal_states = {COPOrderState.COMPLETED, COPOrderState.CANCELLED}
        for state in terminal_states:
            assert self.VALID_TRANSITIONS[state] == set(), (
                f"Terminal state {state.value} has outgoing transitions: {self.VALID_TRANSITIONS[state]}"
            )


# ---------------------------------------------------------------------------
# EUR State Machine Tests (StateManager)
# ---------------------------------------------------------------------------

class TestEURTerminalStates:
    """Test S1: force=True cannot bypass terminal states in EUR path."""

    def test_force_blocked_on_terminal_states(self):
        """force=True should NOT allow transitions out of COMPLETED, CANCELLED, EXPIRED, REFUNDED."""
        from src.core.state_manager import StateManager, ManagedOrder
        from src.core.types import OrderState, UnifiedOrder, OrderSide, OrderStatus, ExchangeId, Currency

        sm = StateManager(db=None)

        # Create a dummy order
        order = UnifiedOrder(
            external_id="test_terminal_123",
            exchange=ExchangeId.BINANCE,
            side=OrderSide.SELL,
            status=OrderStatus.COMPLETED,
            fiat_amount="100.00",
            fiat_currency=Currency.EUR,
            crypto_amount="50.0",
            crypto_asset="USDT",
        )
        managed = sm.track_order(order)
        order_id = managed.id

        # Force to COMPLETED
        sm.transition(order_id, OrderState.COMPLETED, "test_setup", force=True)

        # Now try to force out of COMPLETED — should fail (S1)
        result = sm.transition(order_id, OrderState.NEW, "exploit_attempt", force=True)
        assert result is False, "S1 VIOLATED: force=True escaped COMPLETED state"

    def test_force_allowed_on_non_terminal(self):
        """force=True should work for non-terminal states."""
        from src.core.state_manager import StateManager
        from src.core.types import OrderState, UnifiedOrder, OrderSide, OrderStatus, ExchangeId, Currency

        sm = StateManager(db=None)

        order = UnifiedOrder(
            external_id="test_force_ok_123",
            exchange=ExchangeId.BINANCE,
            side=OrderSide.SELL,
            status=OrderStatus.NEW,
            fiat_amount="100.00",
            fiat_currency=Currency.EUR,
            crypto_amount="50.0",
            crypto_asset="USDT",
        )
        managed = sm.track_order(order)
        order_id = managed.id

        # Force transition from NEW to some non-standard target — should succeed
        result = sm.transition(order_id, OrderState.AGENT_REQUIRED, "test_force", force=True)
        assert result is True, "force=True should work on non-terminal states"
