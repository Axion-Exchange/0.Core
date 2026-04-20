
import os
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app
from src.core.types import KycSession, KycStatus, ExchangeId

@pytest.fixture
def client():
    return TestClient(app)

# Helper for async mocks
async def make_coro(value):
    return value

@pytest.fixture
def mock_didit():
    # Patch the singleton accessor implementation directly
    with patch("src.kyc.didit_client.didit_client") as mock_accessor:
        mock_instance = MagicMock()
        mock_accessor.return_value = mock_instance
        yield mock_instance

def test_create_kyc_session(client, mock_didit):
    """Test POST /api/kyc/session"""
    print("\nTesting Create KYC Session...")
    
    mock_session = KycSession(
        id="kyc_test_123",
        external_id="didit_sess_123",
        status=KycStatus.PENDING,
        link="https://verify.didit.me/test",
        order_id="BIN-TEST",
        exchange=ExchangeId.BINANCE,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24),
        raw={}
    )
    # Manual coroutine replacement
    mock_didit.create_kyc_session.side_effect = lambda *args, **kwargs: make_coro(mock_session)
    
    payload = {
        "exchange": "binance",
        "order_id": "12345678"
    }
    response = client.post("/api/kyc/session", params=payload)
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["session_id"] == "didit_sess_123"
    assert data["link"] == "https://verify.didit.me/test"
    assert data["status"] == "pending"

def test_get_kyc_session_status_approved(client, mock_didit):
    """Test GET /api/kyc/session/{id} - APPROVED"""
    print("\nTesting Get Session Status (APPROVED)...")
    
    mock_session = KycSession(
        id="kyc_test_123",
        external_id="didit_sess_123",
        status=KycStatus.APPROVED,
        link="https://verify.didit.me/test",
        order_id="BIN-TEST",
        exchange=ExchangeId.BINANCE,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24),
        raw={}
    )
    mock_didit.get_session_status.side_effect = lambda *args, **kwargs: make_coro(mock_session)
    
    response = client.get("/api/kyc/session/didit_sess_123")
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "approved"

def test_get_kyc_session_status_rejected(client, mock_didit):
    """Test GET /api/kyc/session/{id} - REJECTED"""
    print("\nTesting Get Session Status (REJECTED)...")
    
    mock_session = KycSession(
        id="kyc_test_123",
        external_id="didit_sess_123",
        status=KycStatus.REJECTED,
        link="https://verify.didit.me/test",
        order_id="BIN-TEST",
        exchange=ExchangeId.BINANCE,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24),
        raw={}
    )
    mock_didit.get_session_status.side_effect = lambda *args, **kwargs: make_coro(mock_session)
    
    response = client.get("/api/kyc/session/didit_sess_123")
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "rejected"

def test_get_session_by_order(client, mock_didit):
    """Test GET /api/kyc/session/by-order/{internal}"""
    print("\nTesting Get Session By Order...")
    
    # Create a STALE session for cache
    stale_session = KycSession(
        id="kyc_test_456",
        external_id="didit_sess_456",
        status=KycStatus.PENDING,
        link="https://verify.didit.me/test2",
        order_id="BIN-ORDER-1",
        exchange=ExchangeId.BINANCE,
        created_at=datetime.now() - timedelta(days=1), # Old
        expires_at=datetime.now(),
        raw={}
    )

    mock_session = KycSession(
        id="kyc_test_456",
        external_id="didit_sess_456",
        status=KycStatus.APPROVED, # Updated status
        link="https://verify.didit.me/test2",
        order_id="BIN-ORDER-1",
        exchange=ExchangeId.BINANCE,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24),
        raw={}
    )
    
    # Return stale session from cache to pass the first check
    mock_didit.get_cached_session.return_value = stale_session
    # Return updated session from refresh
    mock_didit.refresh_session.side_effect = lambda *args, **kwargs: make_coro(mock_session)
    
    response = client.get("/api/kyc/session/by-order/BIN-ORDER-1")
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["internal_order_number"] == "BIN-ORDER-1"
    assert data["session_id"] == "didit_sess_456"
    assert data["status"] == "approved"
