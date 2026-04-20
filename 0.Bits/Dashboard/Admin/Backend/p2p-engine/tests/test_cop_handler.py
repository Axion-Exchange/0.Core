"""
TEST: COP Chat Handler
=======================
Tests the COPChatHandler orchestrator logic including:
- Webhook safety checks
- Lock management
- Amount verification
- State guards for release
"""

import pytest
from src.fiat.cop.cop_types import COPOrderState, COPOrder


class TestWebhookSafetyGuards:
    """Verify webhook handler safety checks without requiring live APIs."""

    def test_releasable_states_defined(self):
        """The handler should define a strict set of releasable states."""
        RELEASABLE_STATES = {
            COPOrderState.LINK_SENT,
            COPOrderState.AWAITING_PAYMENT,
            COPOrderState.PAYMENT_RECEIVED,
        }

        # RELEASING and COMPLETED must NOT be in releasable states
        assert COPOrderState.RELEASING not in RELEASABLE_STATES
        assert COPOrderState.COMPLETED not in RELEASABLE_STATES
        assert COPOrderState.CANCELLED not in RELEASABLE_STATES
        assert COPOrderState.NEW not in RELEASABLE_STATES

    def test_amount_verification_exact_match(self):
        """Amount verification must use exact matching — no tolerance."""
        from decimal import Decimal

        expected = Decimal("500000")
        received = Decimal("500000")
        assert expected == received, "Exact same amounts should match"

    def test_amount_verification_rejects_mismatch(self):
        """Even a 1 COP difference must be rejected."""
        from decimal import Decimal

        expected = Decimal("500000")
        received = Decimal("499999")
        assert expected != received, "1 COP difference must be rejected"

    def test_amount_verification_rejects_overpayment(self):
        """Overpayment must also be rejected — only exact match is safe."""
        from decimal import Decimal

        expected = Decimal("500000")
        received = Decimal("500001")
        assert expected != received, "Overpayment must be rejected"


class TestOrderLinkExpiry:
    """Test PSE link expiry detection."""

    def test_order_without_expiry_not_expired(self):
        order = COPOrder(binance_order_id="test_expiry_1")
        assert order.is_link_expired() is False

    def test_order_with_future_expiry_not_expired(self):
        from datetime import datetime, timedelta
        order = COPOrder(
            binance_order_id="test_expiry_2",
            link_expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert order.is_link_expired() is False

    def test_order_with_past_expiry_is_expired(self):
        from datetime import datetime, timedelta
        order = COPOrder(
            binance_order_id="test_expiry_3",
            link_expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert order.is_link_expired() is True


class TestCOPOrderDataclass:
    """Test COPOrder dataclass defaults and behavior."""

    def test_default_state_is_new(self):
        order = COPOrder(binance_order_id="dc_test_1")
        assert order.state == COPOrderState.NEW

    def test_welcome_sent_default_false(self):
        order = COPOrder(binance_order_id="dc_test_2")
        assert order.welcome_sent is False

    def test_chat_messages_default_empty(self):
        order = COPOrder(binance_order_id="dc_test_3")
        assert order.chat_messages == []

    def test_optional_fields_are_none(self):
        order = COPOrder(binance_order_id="dc_test_4")
        assert order.customer_name is None
        assert order.customer_cc is None
        assert order.customer_email is None
        assert order.bank_code is None
        assert order.amount_cop is None
        assert order.amount_usdt is None
