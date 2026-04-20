"""
TEST: P0 Emergency Fixes
==========================
Tests verifying the 4 P0 fixes for production readiness.

P0-1: set_customer_info cannot bypass state machine (terminal states stay terminal)
P0-2: DB release guard prevents double-release (try_claim_release is at-most-once)
P0-3: FACILITAPAY_WEBHOOK_SECRET required when ENABLE_COP=true (startup validation)
P0-4: /version endpoint returns git SHA
"""

import os
import sys
import threading
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fiat.cop.cop_types import COPOrderState
from src.fiat.cop.cop_tracker import COPOrderTracker


# ─── Fixture ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tracker(tmp_path):
    """Create a fresh in-memory COPOrderTracker for each test."""
    db_path = str(tmp_path / "test_cop.db")
    return COPOrderTracker(db_path=db_path)


def _walk_to_state(tracker, order_id, target_state):
    """Walk an order through valid transitions to reach a target state."""
    # create_order starts at AWAITING_INFO
    paths = {
        COPOrderState.INFO_RECEIVED: [COPOrderState.INFO_RECEIVED],
        COPOrderState.GENERATING_LINK: [COPOrderState.INFO_RECEIVED, COPOrderState.GENERATING_LINK],
        COPOrderState.LINK_SENT: [COPOrderState.INFO_RECEIVED, COPOrderState.GENERATING_LINK, COPOrderState.LINK_SENT],
        COPOrderState.PAYMENT_RECEIVED: [
            COPOrderState.INFO_RECEIVED, COPOrderState.GENERATING_LINK,
            COPOrderState.LINK_SENT, COPOrderState.AWAITING_PAYMENT,
            COPOrderState.PAYMENT_RECEIVED,
        ],
        COPOrderState.RELEASING: [
            COPOrderState.INFO_RECEIVED, COPOrderState.GENERATING_LINK,
            COPOrderState.LINK_SENT, COPOrderState.AWAITING_PAYMENT,
            COPOrderState.PAYMENT_RECEIVED, COPOrderState.RELEASING,
        ],
        COPOrderState.COMPLETED: [
            COPOrderState.INFO_RECEIVED, COPOrderState.GENERATING_LINK,
            COPOrderState.LINK_SENT, COPOrderState.AWAITING_PAYMENT,
            COPOrderState.PAYMENT_RECEIVED, COPOrderState.RELEASING,
            COPOrderState.COMPLETED,
        ],
        COPOrderState.CANCELLED: [COPOrderState.CANCELLED],
    }
    if target_state == COPOrderState.AWAITING_INFO:
        return  # Already there after create_order
    for step in paths[target_state]:
        result = tracker.transition(order_id, step)
        assert result is not None, f"Failed to transition to {step.value}"


# =============================================================================
# P0-1: set_customer_info CANNOT bypass VALID_TRANSITIONS
# =============================================================================

class TestP0_1_SetCustomerInfoStateGuard:
    """P0-1: set_customer_info must NOT re-open terminal or in-progress states."""

    def test_blocked_on_completed(self, tracker):
        """COMPLETED order must stay COMPLETED after set_customer_info."""
        tracker.create_order("TERM-001", amount_cop="100000", amount_usdt="50")
        _walk_to_state(tracker, "TERM-001", COPOrderState.COMPLETED)

        # Attempt to set info on completed order
        tracker.set_customer_info("TERM-001", "Attacker", "12345", "x@evil.com", "1007")

        order = tracker.get_order("TERM-001")
        assert order.state == COPOrderState.COMPLETED, \
            "CRITICAL: set_customer_info re-opened COMPLETED order!"

    def test_blocked_on_cancelled(self, tracker):
        """CANCELLED order must stay CANCELLED after set_customer_info."""
        tracker.create_order("TERM-002", amount_cop="100000", amount_usdt="50")
        tracker.transition("TERM-002", COPOrderState.CANCELLED)

        tracker.set_customer_info("TERM-002", "Attacker", "12345", "x@evil.com", "1007")

        order = tracker.get_order("TERM-002")
        assert order.state == COPOrderState.CANCELLED, \
            "CRITICAL: set_customer_info re-opened CANCELLED order!"

    def test_blocked_on_releasing(self, tracker):
        """RELEASING order must stay RELEASING after set_customer_info."""
        tracker.create_order("TERM-003", amount_cop="100000", amount_usdt="50")
        _walk_to_state(tracker, "TERM-003", COPOrderState.RELEASING)

        tracker.set_customer_info("TERM-003", "Attacker", "12345", "x@evil.com", "1007")

        order = tracker.get_order("TERM-003")
        assert order.state == COPOrderState.RELEASING, \
            "CRITICAL: set_customer_info changed state of RELEASING order!"

    def test_blocked_on_payment_received(self, tracker):
        """PAYMENT_RECEIVED order must stay PAYMENT_RECEIVED."""
        tracker.create_order("TERM-004", amount_cop="100000", amount_usdt="50")
        _walk_to_state(tracker, "TERM-004", COPOrderState.PAYMENT_RECEIVED)

        tracker.set_customer_info("TERM-004", "Attacker", "12345", "x@evil.com", "1007")

        order = tracker.get_order("TERM-004")
        assert order.state == COPOrderState.PAYMENT_RECEIVED

    def test_blocked_on_link_sent(self, tracker):
        """LINK_SENT order must stay LINK_SENT."""
        tracker.create_order("TERM-005", amount_cop="100000", amount_usdt="50")
        _walk_to_state(tracker, "TERM-005", COPOrderState.LINK_SENT)

        tracker.set_customer_info("TERM-005", "Attacker", "12345", "x@evil.com", "1007")

        order = tracker.get_order("TERM-005")
        assert order.state == COPOrderState.LINK_SENT

    def test_allowed_on_awaiting_info(self, tracker):
        """AWAITING_INFO → INFO_RECEIVED is the normal happy path."""
        tracker.create_order("TERM-006", amount_cop="100000", amount_usdt="50")

        tracker.set_customer_info("TERM-006", "Juan", "12345", "juan@email.com", "1007")

        order = tracker.get_order("TERM-006")
        assert order.state == COPOrderState.INFO_RECEIVED
        assert order.customer_name == "Juan"
        assert order.customer_cc == "12345"

    def test_allowed_on_info_received(self, tracker):
        """INFO_RECEIVED → INFO_RECEIVED (update info) is allowed."""
        tracker.create_order("TERM-007", amount_cop="100000", amount_usdt="50")
        tracker.transition("TERM-007", COPOrderState.INFO_RECEIVED)

        tracker.set_customer_info("TERM-007", "Juan Updated", "99999", "new@email.com", "1051")

        order = tracker.get_order("TERM-007")
        assert order.state == COPOrderState.INFO_RECEIVED
        assert order.customer_name == "Juan Updated"

    def test_info_settable_states_are_subset_of_transitions(self, tracker):
        """All _INFO_SETTABLE_STATES (except INFO_RECEIVED itself) must have
        INFO_RECEIVED as a valid target in VALID_TRANSITIONS.
        INFO_RECEIVED → INFO_RECEIVED is an idempotent re-set, not a transition."""
        for state in COPOrderTracker._INFO_SETTABLE_STATES:
            if state == COPOrderState.INFO_RECEIVED:
                continue  # Re-set is handled directly, not via transition()
            allowed = COPOrderTracker.VALID_TRANSITIONS.get(state, set())
            assert COPOrderState.INFO_RECEIVED in allowed, \
                f"State {state.value} is in _INFO_SETTABLE_STATES but cannot transition to INFO_RECEIVED"


# =============================================================================
# P0-2: DB Release Guard (at-most-once release)
# =============================================================================

class TestP0_2_DBReleaseGuard:
    """P0-2: try_claim_release must enforce at-most-once semantics via DB."""

    def test_first_claim_succeeds(self, tracker):
        """First call to try_claim_release must return True."""
        assert tracker.try_claim_release("REL-001") is True

    def test_second_claim_fails(self, tracker):
        """Second call to try_claim_release for same order must return False."""
        tracker.try_claim_release("REL-002")
        assert tracker.try_claim_release("REL-002") is False

    def test_third_claim_fails(self, tracker):
        """Third (and any subsequent) call must also return False."""
        tracker.try_claim_release("REL-003")
        tracker.try_claim_release("REL-003")
        assert tracker.try_claim_release("REL-003") is False

    def test_different_orders_independent(self, tracker):
        """Claims for different orders are independent."""
        assert tracker.try_claim_release("REL-A") is True
        assert tracker.try_claim_release("REL-B") is True
        assert tracker.try_claim_release("REL-A") is False
        assert tracker.try_claim_release("REL-B") is False

    def test_mark_release_result_success(self, tracker):
        """After claiming, can record success."""
        tracker.try_claim_release("REL-004")
        tracker.mark_release_result("REL-004", success=True)
        assert tracker.is_release_claimed("REL-004") is True

    def test_mark_release_result_failure(self, tracker):
        """After claiming, can record failure."""
        tracker.try_claim_release("REL-005")
        tracker.mark_release_result("REL-005", success=False)
        assert tracker.is_release_claimed("REL-005") is True

    def test_is_release_claimed_false_for_unclaimed(self, tracker):
        """is_release_claimed returns False for orders never claimed."""
        assert tracker.is_release_claimed("REL-NONEXISTENT") is False

    def test_concurrent_claims_only_one_wins(self, tracker):
        """Simulate concurrent claims — exactly one must succeed."""
        results = []

        def claim():
            results.append(tracker.try_claim_release("RACE-001"))

        threads = [threading.Thread(target=claim) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 1 claim must succeed, rest must fail
        assert results.count(True) == 1, \
            f"Expected exactly 1 successful claim, got {results.count(True)}"
        assert results.count(False) == 9


# =============================================================================
# P0-3: Webhook Secret Required at Startup
# =============================================================================

class TestP0_3_WebhookSecretRequired:
    """P0-3: FACILITAPAY_WEBHOOK_SECRET must be in COP_REQUIRED."""

    def test_webhook_secret_in_cop_required(self):
        """FACILITAPAY_WEBHOOK_SECRET must be a required COP variable."""
        from src.core.env_validator import COP_REQUIRED
        assert "FACILITAPAY_WEBHOOK_SECRET" in COP_REQUIRED, \
            "FACILITAPAY_WEBHOOK_SECRET must be required for COP operations"

    def test_webhook_secret_not_optional(self):
        """FACILITAPAY_WEBHOOK_SECRET must NOT be in optional vars."""
        from src.core.env_validator import OPTIONAL_VARS
        assert "FACILITAPAY_WEBHOOK_SECRET" not in OPTIONAL_VARS, \
            "FACILITAPAY_WEBHOOK_SECRET must not be optional — it's required for COP"

    def test_validate_env_exits_without_webhook_secret(self, monkeypatch):
        """Startup must fail if ENABLE_COP=true but webhook secret is missing."""
        from src.core.env_validator import validate_env, COP_REQUIRED, CORE_REQUIRED

        # Set all required vars EXCEPT webhook secret
        for var in CORE_REQUIRED:
            monkeypatch.setenv(var, "test-value")
        for var in COP_REQUIRED:
            if var != "FACILITAPAY_WEBHOOK_SECRET":
                monkeypatch.setenv(var, "test-value")
        monkeypatch.delenv("FACILITAPAY_WEBHOOK_SECRET", raising=False)

        with pytest.raises(SystemExit):
            validate_env(enable_cop=True)

    def test_validate_env_passes_with_webhook_secret(self, monkeypatch):
        """Startup must succeed if all COP vars including webhook secret are set."""
        from src.core.env_validator import validate_env, COP_REQUIRED, CORE_REQUIRED

        for var in CORE_REQUIRED:
            monkeypatch.setenv(var, "test-value")
        for var in COP_REQUIRED:
            monkeypatch.setenv(var, "test-value")

        result = validate_env(enable_cop=True)
        assert result["cop"] is True


# =============================================================================
# P0-4: /version Endpoint
# =============================================================================

class TestP0_4_VersionEndpoint:
    """P0-4: /version endpoint must exist and return git SHA."""

    def test_get_git_sha_returns_string(self):
        """get_git_sha must return a non-empty string."""
        from src.api.routes import get_git_sha
        sha = get_git_sha()
        assert isinstance(sha, str)
        assert len(sha) > 0

    def test_git_sha_cached(self):
        """_GIT_SHA should be cached at import time."""
        from src.api.routes import _GIT_SHA
        assert isinstance(_GIT_SHA, str)
        assert len(_GIT_SHA) > 0

    def test_version_endpoint_exists(self):
        """The /version route must be registered on the router."""
        from src.api.routes import router

        # Router has prefix /api, so route path is /version within the router
        version_routes = [
            r for r in router.routes
            if hasattr(r, "path") and "/version" in r.path
        ]
        assert len(version_routes) == 1, "/version endpoint must exist"

    def test_version_endpoint_is_get(self):
        """The /version route must be a GET endpoint."""
        from src.api.routes import router

        for route in router.routes:
            if hasattr(route, "path") and "/version" in route.path:
                assert "GET" in route.methods, "/version must be a GET endpoint"
                break


# =============================================================================
# Property-Based: Terminal State Invariant
# =============================================================================

class TestTerminalStateInvariant:
    """No sequence of operations can escape a terminal state."""

    def test_all_operations_blocked_on_completed(self, tracker):
        """Every state transition must be rejected for COMPLETED orders."""
        tracker.create_order("PROP-001", amount_cop="100000", amount_usdt="50")
        _walk_to_state(tracker, "PROP-001", COPOrderState.COMPLETED)

        for target in COPOrderState:
            result = tracker.transition("PROP-001", target)
            assert result is None, \
                f"COMPLETED order transitioned to {target.value}!"

    def test_all_operations_blocked_on_cancelled(self, tracker):
        """Every state transition must be rejected for CANCELLED orders."""
        tracker.create_order("PROP-002", amount_cop="100000", amount_usdt="50")
        tracker.transition("PROP-002", COPOrderState.CANCELLED)

        for target in COPOrderState:
            result = tracker.transition("PROP-002", target)
            assert result is None, \
                f"CANCELLED order transitioned to {target.value}!"
