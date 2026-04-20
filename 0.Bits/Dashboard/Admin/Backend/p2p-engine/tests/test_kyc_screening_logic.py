import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from src.services.kyc_screener import KycScreener, KycScreeningResult
from src.core.types import UnifiedOrder, OrderSide, OrderStatus, ExchangeId, Counterparty, Currency

@pytest.fixture
def mock_orders_db():
    with patch("sqlite3.connect") as mock_connect:
        yield mock_connect

@pytest.fixture
def mock_kyc_cache():
    with patch("src.services.kyc_screener.KycStatusCache") as mock_cache_cls:
        mock_cache = MagicMock()
        mock_cache_cls.return_value = mock_cache
        yield mock_cache

@pytest.fixture
def screener(mock_orders_db, mock_kyc_cache):
    return KycScreener()

# Helper to create dummy orders
def create_order(amount: float, name: str = "Test User") -> UnifiedOrder:
    return UnifiedOrder(
        id="internal_id_123", # Required
        external_id="12345",
        exchange=ExchangeId.BINANCE,
        side=OrderSide.SELL,
        status=OrderStatus.AWAITING_PAYMENT,
        created_at=datetime.now(),
        updated_at=datetime.now(), # Required
        crypto_amount="100.0", # String
        crypto_asset="USDT",
        fiat_amount=str(amount), # String
        fiat_currency=Currency.EUR,
        price="1.0", # String
        counterparty=Counterparty(
            name=name,
            real_name=None,
            verification_status="unverified"
        ),
        payment_method="SEPA",
        raw={} # Valid dict
    )

@pytest.mark.asyncio
async def test_screen_order_cached_user(screener, mock_kyc_cache):
    """Test that cached KYC user is skipped."""
    mock_kyc_cache.has_kyc.return_value = True
    
    order = create_order(1000.0, "Verified User")
    result = await screener.screen_new_order(order)
    
    assert result.kyc_required is False
    assert "in cache" in result.reason
    assert result.has_kyc_cache is True

@pytest.mark.asyncio
async def test_screen_order_small_amount(screener, mock_kyc_cache):
    """Test that small order (<500) is skipped for new user."""
    mock_kyc_cache.has_kyc.return_value = False
    # Mock no previous orders
    screener._find_previous_orders = MagicMock(return_value=[])
    
    order = create_order(400.0, "New User")
    result = await screener.screen_new_order(order)
    
    assert result.kyc_required is False
    assert "small amount" in result.reason

@pytest.mark.asyncio
async def test_screen_order_large_amount_new_user(screener, mock_kyc_cache):
    """Test that large order (>500) requires KYC for new user."""
    mock_kyc_cache.has_kyc.return_value = False
    screener._find_previous_orders = MagicMock(return_value=[])
    
    order = create_order(600.0, "New User")
    result = await screener.screen_new_order(order)
    
    assert result.kyc_required is True
    assert "New customer" in result.reason

@pytest.mark.asyncio
async def test_screen_order_repeat_customer(screener, mock_kyc_cache):
    """Test that repeat customer (previous orders) is skipped."""
    mock_kyc_cache.has_kyc.return_value = False
    # Mock previous orders exist
    screener._find_previous_orders = MagicMock(return_value=["ORDER-1", "ORDER-2"])
    
    # Even large amount should skip if repeat
    order = create_order(1000.0, "Repeat User")
    result = await screener.screen_new_order(order)
    
    assert result.kyc_required is False
    assert "Repeat customer" in result.reason
    assert result.previous_orders_count == 2
