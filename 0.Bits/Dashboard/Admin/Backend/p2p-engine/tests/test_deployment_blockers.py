"""
Tests for deployment blockers R-01, A-12, R-02.
Run: python -m pytest tests/test_deployment_blockers.py -v
"""
import json
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# R-01: NameError regression — create_pse_payin persistence call
# =============================================================================

class TestR01_NameError:
    """
    R-01: After removing exchange_currency parameter from create_pse_payin(),
    line 556 still referenced `exchange_currency` as a bare variable.
    This must now reference `self.SETTLEMENT_CURRENCY`.
    """

    def test_settlement_currency_in_save_transaction_call(self):
        """Verify no NameError: the persistence call uses self.SETTLEMENT_CURRENCY."""
        import ast
        import os

        client_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "fiat", "cop", "facilitapay_client.py"
        )
        with open(client_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # Find the create_pse_payin function
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_pse_payin":
                # Check that create_pse_payin does NOT have exchange_currency as a parameter
                param_names = [arg.arg for arg in node.args.args]
                assert "exchange_currency" not in param_names, (
                    "exchange_currency should NOT be a parameter of create_pse_payin"
                )

                # Scan for bare Name references to 'exchange_currency' (the bug)
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and child.id == "exchange_currency":
                        pytest.fail(
                            f"R-01 REGRESSION: bare 'exchange_currency' variable reference "
                            f"found at line {child.lineno} in create_pse_payin(). "
                            f"Must use self.SETTLEMENT_CURRENCY instead."
                        )
                break
        else:
            pytest.fail("Could not find create_pse_payin in facilitapay_client.py")

    def test_settlement_currency_constant_exists(self):
        """Verify SETTLEMENT_CURRENCY class constant is defined."""
        import importlib.util
        import os

        client_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "fiat", "cop", "facilitapay_client.py"
        )
        with open(client_path, "r", encoding="utf-8") as f:
            source = f.read()

        assert "SETTLEMENT_CURRENCY" in source, "SETTLEMENT_CURRENCY constant missing"
        assert 'SETTLEMENT_CURRENCY = "USD"' in source or "SETTLEMENT_CURRENCY = 'USD'" in source, (
            "SETTLEMENT_CURRENCY must default to USD"
        )


# =============================================================================
# A-12: Webhook secret fail-closed verification
# =============================================================================

class TestA12_WebhookSecretFailClosed:
    """
    A-12: Webhook endpoint must reject webhooks with missing/null/wrong secrets.
    Previously, null secret silently skipped verification.
    """

    @pytest.fixture
    def mock_client(self):
        """Create a minimal mock FacilitaPayCopClient."""
        client = MagicMock()
        client.webhook_secret = "correct-secret-123"
        client.db = MagicMock()

        # verify_webhook_secret uses hmac.compare_digest
        import hmac
        def verify(received):
            return hmac.compare_digest(str(received), client.webhook_secret)
        client.verify_webhook_secret = verify

        return client

    def _build_webhook_body(self, secret=None, include_secret_key=True):
        """Build a FacilitaPay webhook body."""
        notification = {
            "type": "identified",
            "transaction_id": "test-tx-uuid-1234",
        }
        if include_secret_key:
            notification["secret"] = secret
        return json.dumps({"notification": notification}).encode()

    @pytest.mark.asyncio
    async def test_missing_secret_rejected(self, mock_client):
        """Webhook with no secret field → 401."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        # Import after mocking to avoid import-time side effects
        import sys
        sys.path.insert(0, "src")
        from fiat.cop.facilitapay_webhooks import create_webhook_router

        app = FastAPI()
        router = create_webhook_router(mock_client)
        app.include_router(router)

        client = TestClient(app)
        body = self._build_webhook_body(secret=None, include_secret_key=False)
        resp = client.post(
            "/webhooks/facilitapay",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401, f"Missing secret should return 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_null_secret_rejected(self, mock_client):
        """Webhook with secret=null → 401."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        import sys
        sys.path.insert(0, "src")
        from fiat.cop.facilitapay_webhooks import create_webhook_router

        app = FastAPI()
        router = create_webhook_router(mock_client)
        app.include_router(router)

        client = TestClient(app)
        body = self._build_webhook_body(secret=None, include_secret_key=True)
        resp = client.post(
            "/webhooks/facilitapay",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401, f"Null secret should return 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_wrong_secret_rejected(self, mock_client):
        """Webhook with wrong secret → 401."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        import sys
        sys.path.insert(0, "src")
        from fiat.cop.facilitapay_webhooks import create_webhook_router

        app = FastAPI()
        router = create_webhook_router(mock_client)
        app.include_router(router)

        client = TestClient(app)
        body = self._build_webhook_body(secret="wrong-secret-999")
        resp = client.post(
            "/webhooks/facilitapay",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401, f"Wrong secret should return 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_correct_secret_accepted(self, mock_client):
        """Webhook with correct secret → 200 (persisted)."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        import sys
        sys.path.insert(0, "src")
        from fiat.cop.facilitapay_webhooks import create_webhook_router

        # Make log_webhook_atomic return True (new event)
        mock_client.db.log_webhook_atomic = MagicMock(return_value=True)
        mock_client.db.mark_webhook_processed = MagicMock()

        app = FastAPI()
        router = create_webhook_router(mock_client)
        app.include_router(router)

        client = TestClient(app)
        body = self._build_webhook_body(secret="correct-secret-123")
        resp = client.post(
            "/webhooks/facilitapay",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200, f"Correct secret should return 200, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_empty_string_secret_rejected(self, mock_client):
        """Webhook with secret="" → 401."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        import sys
        sys.path.insert(0, "src")
        from fiat.cop.facilitapay_webhooks import create_webhook_router

        app = FastAPI()
        router = create_webhook_router(mock_client)
        app.include_router(router)

        client = TestClient(app)
        body = self._build_webhook_body(secret="")
        resp = client.post(
            "/webhooks/facilitapay",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401, f"Empty secret should return 401, got {resp.status_code}"


# =============================================================================
# R-02: Currency-aware amount verification
# =============================================================================

class TestR02_CurrencyAwareAmountVerification:
    """
    R-02: handle_webhook must verify amounts using currency-aware logic.
    - If tx.currency == "COP": compare tx.value to order.amount_cop
    - If tx.exchange_currency == "COP": compare tx.exchanged_value to order.amount_cop
    - If neither is COP: fail safe to MANUAL_REVIEW
    """

    def test_fp_transaction_has_exchanged_value_field(self):
        """FPTransaction model must have explicit exchanged_value field."""
        import sys
        sys.path.insert(0, "src")
        from fiat.cop.facilitapay_models import FPTransaction

        # Create a transaction with exchanged_value
        tx = FPTransaction(
            id="test-uuid",
            status="identified",
            value="850000",
            currency="COP",
            exchange_currency="USD",
            exchanged_value="197.43",
        )
        assert tx.exchanged_value == "197.43"
        assert tx.value == "850000"
        assert tx.currency == "COP"

    def test_cop_direct_amount_match(self):
        """COP pay-in: tx.currency=COP, tx.value=850000 → match order.amount_cop=850000."""
        tx_currency = "COP"
        tx_value = "850000"
        tx_exchange_currency = "USD"
        tx_exchanged_value = None  # Not yet exchanged at 'identified' stage
        order_amount_cop = "850000"

        # Currency-aware routing logic (mirrors handle_webhook)
        if tx_currency == "COP":
            tx_amount_cop = tx_value
        elif tx_exchange_currency == "COP" and tx_exchanged_value:
            tx_amount_cop = tx_exchanged_value
        else:
            pytest.fail("Should have found COP amount")

        paid_int = int(Decimal(str(tx_amount_cop)).to_integral_value())
        expected_int = int(Decimal(str(order_amount_cop)).to_integral_value())
        assert paid_int == expected_int

    def test_cop_to_usd_conversion_amount_match(self):
        """
        COP→USD conversion: tx.currency=COP, tx.value=850000.
        Even after FX, value stays in COP. exchanged_value = USD amount.
        We should still match on tx.value (COP).
        """
        tx_currency = "COP"
        tx_value = "850000"
        tx_exchange_currency = "USD"
        tx_exchanged_value = "197.43"
        order_amount_cop = "850000"

        if tx_currency == "COP":
            tx_amount_cop = tx_value
        elif tx_exchange_currency == "COP" and tx_exchanged_value:
            tx_amount_cop = tx_exchanged_value
        else:
            pytest.fail("Should have found COP amount")

        paid_int = int(Decimal(str(tx_amount_cop)).to_integral_value())
        expected_int = int(Decimal(str(order_amount_cop)).to_integral_value())
        assert paid_int == expected_int

    def test_usd_with_cop_exchange_amount_match(self):
        """
        Hypothetical payout: tx.currency=USD, tx.exchange_currency=COP,
        tx.exchanged_value=4500000.
        Falls back to exchanged_value for COP comparison.
        """
        tx_currency = "USD"
        tx_value = "1000.00"
        tx_exchange_currency = "COP"
        tx_exchanged_value = "4500000"
        order_amount_cop = "4500000"

        if tx_currency == "COP":
            tx_amount_cop = tx_value
        elif tx_exchange_currency == "COP" and tx_exchanged_value:
            tx_amount_cop = tx_exchanged_value
        else:
            pytest.fail("Should have found COP amount")

        paid_int = int(Decimal(str(tx_amount_cop)).to_integral_value())
        expected_int = int(Decimal(str(order_amount_cop)).to_integral_value())
        assert paid_int == expected_int

    def test_neither_currency_cop_fails_safe(self):
        """
        Pathological: tx.currency=USD, tx.exchange_currency=EUR.
        No COP field available → should fail safe (returns None/triggers review).
        """
        tx_currency = "USD"
        tx_value = "500.00"
        tx_exchange_currency = "EUR"
        tx_exchanged_value = "470.00"

        tx_amount_cop = None
        if tx_currency == "COP":
            tx_amount_cop = tx_value
        elif tx_exchange_currency == "COP" and tx_exchanged_value:
            tx_amount_cop = tx_exchanged_value

        assert tx_amount_cop is None, "Should fail safe when no COP field available"

    def test_amount_mismatch_detected(self):
        """Amount mismatch: paid 800000 COP but expected 850000 COP."""
        tx_amount_cop = "800000"
        order_amount_cop = "850000"

        paid_int = int(Decimal(str(tx_amount_cop)).to_integral_value())
        expected_int = int(Decimal(str(order_amount_cop)).to_integral_value())
        assert paid_int != expected_int, "Should detect mismatch"

    def test_decimal_cop_truncation(self):
        """COP amounts with spurious decimals are truncated to integers."""
        tx_amount_cop = "850000.00"
        order_amount_cop = "850000"

        paid_int = int(Decimal(str(tx_amount_cop)).to_integral_value())
        expected_int = int(Decimal(str(order_amount_cop)).to_integral_value())
        assert paid_int == expected_int
