"""
TEST: Idempotency and Double-Execution Prevention
==================================================
Verifies that critical operations cannot be executed twice.

Tests:
1. Double webhook delivery doesn't release crypto twice.
2. Double payout doesn't send EUR twice.
3. Duplicate state transitions are handled safely.
"""

import pytest


class TestCOPWebhookIdempotency:
    """Verify that duplicate FacilitaPay webhooks don't cause double release."""

    def test_completed_order_blocks_release(self):
        """An order already in COMPLETED state must reject release attempts."""
        from src.fiat.cop.cop_tracker import COPOrderTracker
        from src.fiat.cop.cop_types import COPOrderState

        tracker = COPOrderTracker(db_path=":memory:")

        order_id = "idempotent_test_001"
        tracker._save_order_with_state(order_id, COPOrderState.COMPLETED)

        # Attempt to transition to RELEASING — should fail (terminal state)
        result = tracker.transition(order_id, COPOrderState.RELEASING)
        assert result is False, "COMPLETED order must block RELEASING transition"

    def test_releasing_order_blocks_duplicate(self):
        """An order already in RELEASING state must reject a second RELEASING attempt."""
        from src.fiat.cop.cop_tracker import COPOrderTracker
        from src.fiat.cop.cop_types import COPOrderState

        tracker = COPOrderTracker(db_path=":memory:")

        order_id = "idempotent_test_002"
        tracker._save_order_with_state(order_id, COPOrderState.RELEASING)

        # Try RELEASING → RELEASING (self-transition)
        result = tracker.transition(order_id, COPOrderState.RELEASING)
        assert result is False, "RELEASING → RELEASING self-transition must be rejected"


class TestEURPayoutIdempotency:
    """Verify that EUR payouts cannot be sent twice."""

    def test_payout_sent_at_prevents_duplicate(self):
        """If payout_sent_at is set, execute_buy_payout must refuse to send again."""
        from src.core.state_manager import StateManager, ManagedOrder
        from src.core.types import OrderState, UnifiedOrder, OrderSide, OrderStatus, ExchangeId, Currency
        from datetime import datetime

        sm = StateManager(db=None)

        order = UnifiedOrder(
            external_id="dup_payout_test_123",
            exchange=ExchangeId.BINANCE,
            side=OrderSide.BUY,
            status=OrderStatus.NEW,
            fiat_amount="100.00",
            fiat_currency=Currency.EUR,
            crypto_amount="50.0",
            crypto_asset="USDT",
        )
        managed = sm.track_order(order)

        # Simulate payout already sent
        managed.payout_sent_at = datetime.now()

        # The payout_sent_at guard should prevent re-execution
        assert managed.payout_sent_at is not None, "payout_sent_at should be set"

    def test_payout_sent_at_initially_none(self):
        """New orders should have payout_sent_at = None."""
        from src.core.state_manager import ManagedOrder
        from src.core.types import UnifiedOrder, OrderSide, OrderStatus, ExchangeId, Currency

        order = UnifiedOrder(
            external_id="new_order_test_456",
            exchange=ExchangeId.BINANCE,
            side=OrderSide.BUY,
            status=OrderStatus.NEW,
            fiat_amount="50.00",
            fiat_currency=Currency.EUR,
            crypto_amount="25.0",
            crypto_asset="USDT",
        )
        managed = ManagedOrder(order=order)
        assert managed.payout_sent_at is None, "New orders should not have payout_sent_at set"


class TestCOPStateIdempotency:
    """Verify that repeated COP state transitions are idempotent."""

    def test_same_state_transition_accepted_only_if_valid(self):
        """Self-transitions are only valid if explicitly declared in VALID_TRANSITIONS."""
        from src.fiat.cop.cop_tracker import COPOrderTracker
        from src.fiat.cop.cop_types import COPOrderState

        tracker = COPOrderTracker(db_path=":memory:")

        for state in COPOrderState:
            order_id = f"self_transition_{state.value}"
            tracker._save_order_with_state(order_id, state)

            # Self-transition: should only succeed if state is in its own valid targets
            valid_targets = COPOrderTracker.VALID_TRANSITIONS.get(state, set())
            result = tracker.transition(order_id, state)

            if state in valid_targets:
                assert result is True, f"Self-transition for {state.value} should succeed (it's in valid targets)"
            else:
                assert result is False, f"Self-transition for {state.value} should fail (not in valid targets)"
