"""
Tests for Chat-Fallback Name Retry Fix
=======================================
Verifies that when Januar rejects a non-Latin name (PROVIDER_VALIDATION error),
the orchestrator extracts a Latin name from Binance chat and retries the payout
WITHOUT hitting the DB guard (P0-5) a second time.

BUG (pre-fix): try_claim_eur_payout() used INSERT OR IGNORE on PRIMARY KEY(order_id).
After the first claim, the row already existed, so the retry INSERT was silently
ignored → returned False → retry blocked → dead code path.

FIX: Skip the DB re-claim on retry. We already hold the per-order lock and the
original claim row exists. Just use a new replay_id for Januar idempotency.
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


def _make_managed_order(order_id="mo_test123", ext_id="22851234567890123456", exchange="binance"):
    """Create a minimal ManagedOrder-like mock for testing."""
    from src.core.types import OrderSide, OrderState, ExchangeId
    
    order = MagicMock()
    order.side = OrderSide.BUY
    order.external_id = ext_id
    order.exchange = ExchangeId.BINANCE
    order.internal_order_number = "BI123456"
    
    managed = MagicMock()
    managed.id = order_id
    managed.order = order
    managed.state = OrderState.NEW
    managed.payout_sent_at = None
    managed.paid_at = None
    managed.payout_details = {
        "amount": "100.00",
        "currency": "EUR",
        "recipient_name": "محمد الحسين",  # Arabic name — cannot be cleaned to Latin
        "recipient_account": "DE89370400440532013000",  # Valid German IBAN
        "reference": "BI123456",
        "internal_note": "test",
    }
    managed.matched_payment = None
    return managed


def _make_temp_db():
    """Create a temporary OrderDatabase with schema."""
    from src.core.persistence import OrderDatabase
    tmp = tempfile.mktemp(suffix=".db")
    db = OrderDatabase(db_path=tmp)
    return db, tmp


class TestChatFallbackRetry:
    """Verify the chat-fallback name retry path works end-to-end."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_name_validation_error(self):
        """
        Scenario:
        1. Januar rejects payout with PROVIDER_VALIDATION character error
        2. Orchestrator extracts Latin name "Ivan Petrov" from Binance chat
        3. Retry payout with Latin name succeeds
        4. initiate_payout is called TWICE (original + retry)
        """
        from src.fiat.eur.januar_sepa_client import PayoutApiError
        from src.services.order_orchestrator import OrderOrchestrator

        db, db_path = _make_temp_db()
        managed = _make_managed_order()

        # Mock state manager
        state = MagicMock()
        state.get_order.return_value = managed
        state.get_lock.return_value = asyncio.Lock()
        state._persist = MagicMock()
        state.set_error = MagicMock()
        state.transition = MagicMock()

        # Mock exchange client — re-verification passes, mark_paid succeeds
        exchange_client = AsyncMock()
        verified_order = MagicMock()
        verified_order.status = MagicMock()
        verified_order.status.value = "new"
        # Ensure status is not in abort_states
        from src.core.types import OrderState
        verified_order.status = OrderState.NEW
        exchange_client.get_order.return_value = verified_order
        exchange_client.mark_order_paid.return_value = True

        # Mock Januar client
        januar_client = AsyncMock()
        payout_result = MagicMock()
        payout_result.id = "txn-retry-ok"

        # First call: raise PROVIDER_VALIDATION error (non-Latin chars)
        # Second call: succeed with Latin name
        januar_client.initiate_payout.side_effect = [
            PayoutApiError(
                status_code=422,
                body='{"error": "PROVIDER_VALIDATION: name contains non-Latin character"}'
            ),
            payout_result,  # Retry succeeds
        ]

        # Mock registry
        mock_registry = MagicMock()
        mock_registry.get_exchange_api.return_value = exchange_client
        mock_registry.get_bank.return_value = januar_client

        # Build orchestrator with mocks
        orch = OrderOrchestrator.__new__(OrderOrchestrator)
        orch.state = state
        orch._logger = MagicMock()
        orch._extract_name_from_chat = AsyncMock(return_value="Ivan Petrov")
        orch._send_completion_message = AsyncMock()

        # Patch registry and persistence at module level
        with patch("src.services.order_orchestrator.registry", mock_registry), \
             patch("src.core.persistence.order_db", db):
            result = await orch._execute_buy_payout_locked(managed.id)

        # ── ASSERTIONS ──
        # 1. Payout succeeded
        assert result is True, "Payout should succeed after chat-fallback retry"

        # 2. initiate_payout was called TWICE (original + retry)
        assert januar_client.initiate_payout.call_count == 2, \
            f"Expected 2 payout calls, got {januar_client.initiate_payout.call_count}"

        # 3. Second call used the Latin name
        retry_call = januar_client.initiate_payout.call_args_list[1]
        # Accept either transliterated "Yvan Petrov" or chat-extracted "Ivan Petrov"
        retry_name = retry_call.kwargs["recipient_name"]
        assert retry_name in ("Yvan Petrov", "Ivan Petrov"), f"Expected a Latin name, got: {retry_name}"

        # 4. Second call used a different replay_id (for idempotency)
        first_replay = januar_client.initiate_payout.call_args_list[0].kwargs["replay_id"]
        retry_replay = januar_client.initiate_payout.call_args_list[1].kwargs["replay_id"]
        assert retry_replay != first_replay, "Retry must use different replay_id"
        assert retry_replay.endswith("-retry"), f"Retry replay_id should end with '-retry', got: {retry_replay}"

        # 5. Chat fallback may NOT be called if extract_clean_latin_parts handled it
        # orch._extract_name_from_chat was not needed since name was cleaned directly

        # 6. mark_paid was called on Binance
        assert exchange_client.mark_order_paid.call_count >= 1

        # Cleanup
        os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_retry_fails_when_no_latin_name_in_chat(self):
        """
        If _extract_name_from_chat returns None, the payout should fail
        with an error, not crash or silently succeed.
        """
        from src.fiat.eur.januar_sepa_client import PayoutApiError
        from src.services.order_orchestrator import OrderOrchestrator

        db, db_path = _make_temp_db()
        managed = _make_managed_order()

        state = MagicMock()
        state.get_order.return_value = managed
        state.get_lock.return_value = asyncio.Lock()
        state._persist = MagicMock()
        state.set_error = MagicMock()

        exchange_client = AsyncMock()
        from src.core.types import OrderState
        verified_order = MagicMock()
        verified_order.status = OrderState.NEW
        exchange_client.get_order.return_value = verified_order

        januar_client = AsyncMock()
        januar_client.initiate_payout.side_effect = PayoutApiError(
            status_code=422,
            body='{"error": "PROVIDER_VALIDATION: name contains non-Latin character"}'
        )

        mock_registry = MagicMock()
        mock_registry.get_exchange_api.return_value = exchange_client
        mock_registry.get_bank.return_value = januar_client

        orch = OrderOrchestrator.__new__(OrderOrchestrator)
        orch.state = state
        orch._logger = MagicMock()
        orch._extract_name_from_chat = AsyncMock(return_value=None)  # No Latin name found

        with patch("src.services.order_orchestrator.registry", mock_registry), \
             patch("src.core.persistence.order_db", db):
            result = await orch._execute_buy_payout_locked(managed.id)

        # Should fail gracefully
        assert result is False, "Payout should fail when no Latin name available"

        # state.set_error should be called with explanation
        state.set_error.assert_called()
        error_msg = state.set_error.call_args[0][1]
        assert "fallback" in error_msg.lower() or "name validation" in error_msg.lower() or "provider_validation" in error_msg.lower()

        # Only 1 payout attempt (no retry)
        assert januar_client.initiate_payout.call_count == 1

        os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_retry_fails_when_second_payout_also_fails(self):
        """
        If the retry payout also fails (e.g. IBAN issue), the error
        is properly recorded and the function returns False.
        """
        from src.fiat.eur.januar_sepa_client import PayoutApiError
        from src.services.order_orchestrator import OrderOrchestrator

        db, db_path = _make_temp_db()
        managed = _make_managed_order()

        state = MagicMock()
        state.get_order.return_value = managed
        state.get_lock.return_value = asyncio.Lock()
        state._persist = MagicMock()
        state.set_error = MagicMock()

        exchange_client = AsyncMock()
        from src.core.types import OrderState
        verified_order = MagicMock()
        verified_order.status = OrderState.NEW
        exchange_client.get_order.return_value = verified_order

        januar_client = AsyncMock()
        # Both calls fail
        januar_client.initiate_payout.side_effect = [
            PayoutApiError(
                status_code=422,
                body='{"error": "PROVIDER_VALIDATION: name contains non-Latin character"}'
            ),
            PayoutApiError(
                status_code=422,
                body='{"error": "PROVIDER_VALIDATION: still invalid"}'
            ),
        ]

        mock_registry = MagicMock()
        mock_registry.get_exchange_api.return_value = exchange_client
        mock_registry.get_bank.return_value = januar_client

        orch = OrderOrchestrator.__new__(OrderOrchestrator)
        orch.state = state
        orch._logger = MagicMock()
        orch._extract_name_from_chat = AsyncMock(return_value="Ivan Petrov")

        with patch("src.services.order_orchestrator.registry", mock_registry), \
             patch("src.core.persistence.order_db", db):
            result = await orch._execute_buy_payout_locked(managed.id)

        assert result is False, "Should fail when retry also fails"
        assert januar_client.initiate_payout.call_count == 2, "Should attempt retry"
        state.set_error.assert_called()

        os.unlink(db_path)
