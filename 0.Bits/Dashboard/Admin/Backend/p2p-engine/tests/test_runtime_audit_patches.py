"""
Runtime Integration Audit — Patch Verification Tests
=====================================================
Tests for P0-1 (webhook mount), P0-2 (COP listOrders POST),
P1-1 (heartbeats), P1-2 (COP exception escalation),
P1-4 (env vars), P1-5 (API auth fail-closed).

Run: python -m pytest tests/test_runtime_audit_patches.py -v
"""

import asyncio
import os
import sys
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════════════════════
# P0-2: COP listOrders uses POST, not GET
# ═══════════════════════════════════════════════════════════════════════════════

class TestP0_2_CopListOrdersPost:
    """Verify BinanceChatClient.get_active_orders() uses POST (not GET)."""

    @pytest.mark.asyncio
    async def test_get_active_orders_uses_post(self):
        """P0-2: listOrders endpoint requires POST. GET returns 404."""
        from src.fiat.cop.binance_chat import BinanceChatClient

        client = BinanceChatClient(api_key="test", api_secret="test")

        # Mock _signed_post to return a valid response
        mock_response = {"code": "000000", "data": [{"orderNumber": "123", "fiat": "COP"}]}
        client._signed_post = AsyncMock(return_value=mock_response)
        client._signed_get = AsyncMock(side_effect=Exception("GET should not be called"))

        orders = await client.get_active_orders()

        # Must use POST, not GET
        client._signed_post.assert_called_once()
        client._signed_get.assert_not_called()
        assert len(orders) == 1
        assert orders[0]["orderNumber"] == "123"

    @pytest.mark.asyncio
    async def test_correct_endpoint_path(self):
        """Verify the endpoint matches the canonical BinanceApiClient path."""
        from src.fiat.cop.binance_chat import BinanceChatClient

        client = BinanceChatClient(api_key="test", api_secret="test")
        mock_response = {"code": "000000", "data": []}
        client._signed_post = AsyncMock(return_value=mock_response)

        await client.get_active_orders()

        call_args = client._signed_post.call_args
        assert call_args[0][0] == "/sapi/v1/c2c/orderMatch/listOrders"

    @pytest.mark.asyncio
    async def test_does_not_call_invalid_endpoint(self):
        """Ensure no call to non-existent endpoints like listUserOrderHistory."""
        from src.fiat.cop.binance_chat import BinanceChatClient

        client = BinanceChatClient(api_key="test", api_secret="test")
        mock_response = {"code": "000000", "data": []}
        client._signed_post = AsyncMock(return_value=mock_response)

        await client.get_active_orders()

        # Verify the only POST call is to listOrders
        call_path = client._signed_post.call_args[0][0]
        assert "listUserOrderHistory" not in call_path


# ═══════════════════════════════════════════════════════════════════════════════
# P0-1: Webhook router mounted
# ═══════════════════════════════════════════════════════════════════════════════

class TestP0_1_WebhookRouterMounted:
    """Verify create_webhook_router creates a valid router with correct path."""

    def test_webhook_router_has_correct_path(self):
        """Webhook router must register POST /webhooks/facilitapay."""
        from src.fiat.cop.facilitapay_webhooks import create_webhook_router

        mock_client = MagicMock()
        mock_client.verify_webhook_secret = MagicMock(return_value=True)
        router = create_webhook_router(mock_client)

        # Check that the router has routes
        assert len(router.routes) > 0

        # Find the webhook route
        webhook_paths = [r.path for r in router.routes if hasattr(r, 'path')]
        assert "/webhooks/facilitapay" in webhook_paths

    def test_webhook_router_rejects_missing_secret(self):
        """Webhook with missing/empty secret must be rejected (fail-closed)."""
        from src.fiat.cop.facilitapay_webhooks import create_webhook_router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        mock_client = MagicMock()
        mock_client.verify_webhook_secret = MagicMock(return_value=False)

        app = FastAPI()
        router = create_webhook_router(mock_client)
        app.include_router(router)

        test_client = TestClient(app)
        response = test_client.post(
            "/webhooks/facilitapay",
            json={
                "notification": {
                    "type": "payment.identified",
                    "secret": "",
                    "transaction_id": "tx_123",
                }
            },
        )
        # Must reject — fail-closed on missing secret
        assert response.status_code == 401

    def test_webhook_route_not_404(self):
        """The webhook route must be reachable (not 404)."""
        from src.fiat.cop.facilitapay_webhooks import create_webhook_router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        mock_client = MagicMock()
        mock_client.verify_webhook_secret = MagicMock(return_value=True)
        mock_client.db = MagicMock()
        mock_client.db.log_webhook_atomic = MagicMock(return_value=True)
        mock_client.db.mark_webhook_processed = MagicMock()
        mock_client.get_transaction = AsyncMock(return_value=None)

        app = FastAPI()
        router = create_webhook_router(mock_client)
        app.include_router(router)

        test_client = TestClient(app)
        response = test_client.post(
            "/webhooks/facilitapay",
            json={
                "notification": {
                    "type": "payment.identified",
                    "secret": "valid_secret",
                    "transaction_id": "tx_123",
                }
            },
        )
        assert response.status_code != 404


# ═══════════════════════════════════════════════════════════════════════════════
# P1-1: Heartbeat updates within window
# ═══════════════════════════════════════════════════════════════════════════════

class TestP1_1_Heartbeats:
    """Verify heartbeat mechanism works correctly."""

    def test_heartbeat_updates_timestamp(self):
        """Heartbeat must update the last_heartbeat timestamp."""
        from src.core.health import TaskRegistry

        registry = TaskRegistry()
        registry.register("test_task", critical=True)
        registry.mark_running("test_task")

        # Get initial state — tasks is a list of dicts
        status = registry.get_status()
        task_entry = [t for t in status["tasks"] if t.get("name") == "test_task"]
        assert len(task_entry) == 1
        initial_heartbeat = task_entry[0]["last_heartbeat"]

        # Wait a tiny bit then heartbeat
        import time
        time.sleep(0.01)
        registry.heartbeat("test_task")

        status = registry.get_status()
        task_entry = [t for t in status["tasks"] if t.get("name") == "test_task"]
        updated_heartbeat = task_entry[0]["last_heartbeat"]

        assert updated_heartbeat is not None
        if initial_heartbeat is not None:
            assert updated_heartbeat >= initial_heartbeat

    def test_heartbeat_on_unregistered_task(self):
        """Heartbeat on unregistered task should not crash."""
        from src.core.health import TaskRegistry

        registry = TaskRegistry()
        # Should not raise — silently ignore
        registry.heartbeat("nonexistent_task")


# ═══════════════════════════════════════════════════════════════════════════════
# P1-2: COP exception handling with failure escalation
# ═══════════════════════════════════════════════════════════════════════════════

class TestP1_2_CopExceptionHandling:
    """Verify COP handler escalates after consecutive failures."""

    @pytest.mark.asyncio
    async def test_consecutive_failures_increments(self):
        """COP handler must track consecutive failures."""
        from src.fiat.cop.cop_handler import COPChatHandler

        handler = COPChatHandler.__new__(COPChatHandler)
        handler._running = True
        handler._sweep_counter = 0
        handler._consecutive_failures = 0
        handler.poll_interval = 0.01
        handler._order_locks = {}

        call_count = 0

        async def failing_poll():
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                handler._running = False
            raise ValueError("test error")

        handler._poll_cycle = failing_poll

        with patch("src.core.health.task_registry") as mock_registry:
            mock_registry.heartbeat = MagicMock()
            mock_registry.mark_error = MagicMock()

            await handler.start()

            # Should have incremented failure counter
            assert handler._consecutive_failures >= 2
            # mark_error should have been called
            mock_registry.mark_error.assert_called()

    @pytest.mark.asyncio
    async def test_escalates_after_threshold(self):
        """COP handler must re-raise after MAX consecutive failures."""
        from src.fiat.cop.cop_handler import COPChatHandler

        handler = COPChatHandler.__new__(COPChatHandler)
        handler._running = True
        handler._sweep_counter = 0
        handler._consecutive_failures = 0
        handler.poll_interval = 0.001

        async def always_fails():
            raise ValueError("persistent error")

        handler._poll_cycle = always_fails

        with patch("src.core.health.task_registry") as mock_registry:
            mock_registry.heartbeat = MagicMock()
            mock_registry.mark_error = MagicMock()

            with pytest.raises(ValueError, match="persistent error"):
                await handler.start()

            # Should have hit the threshold (10)
            assert handler._consecutive_failures >= 10


# ═══════════════════════════════════════════════════════════════════════════════
# P1-4/P1-5: Env var validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestP1_4_5_EnvValidation:
    """Verify env_validator catches missing critical vars."""

    def test_api_secret_key_required(self):
        """Startup must fail if API_SECRET_KEY is not set."""
        from src.core.env_validator import CORE_REQUIRED
        assert "API_SECRET_KEY" in CORE_REQUIRED

    def test_facilitapay_cashout_required_for_cop(self):
        """FACILITAPAY_CASHOUT_ACCOUNT_ID must be in COP_REQUIRED."""
        from src.core.env_validator import COP_REQUIRED
        assert "FACILITAPAY_CASHOUT_ACCOUNT_ID" in COP_REQUIRED

    def test_validate_env_exits_on_missing_core(self):
        """validate_env must exit if core vars are missing."""
        from src.core.env_validator import validate_env

        # Clear all required vars
        env = {k: "" for k in [
            "BINANCE_API_KEY", "BINANCE_API_SECRET",
            "JANUAR_API_KEY", "JANUAR_API_SECRET",
            "API_SECRET_KEY",
        ]}

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(SystemExit):
                validate_env(enable_cop=False)

    def test_validate_env_exits_on_missing_cop_vars(self):
        """validate_env must exit if COP vars missing when ENABLE_COP=true."""
        from src.core.env_validator import validate_env

        # Set core vars but NOT cop vars
        env = {
            "BINANCE_API_KEY": "test",
            "BINANCE_API_SECRET": "test",
            "JANUAR_API_KEY": "test",
            "JANUAR_API_SECRET": "test",
            "API_SECRET_KEY": "test",
            "FACILITAPAY_USERNAME": "",
            "FACILITAPAY_PASSWORD": "",
            "FACILITAPAY_CASH_IN_ACCOUNT_ID": "",
            "FACILITAPAY_CASHOUT_ACCOUNT_ID": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(SystemExit):
                validate_env(enable_cop=True)
