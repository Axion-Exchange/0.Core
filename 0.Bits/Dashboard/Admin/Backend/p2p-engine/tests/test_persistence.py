"""
Test SQLite Persistence for StateManager.
Run: python3 test_persistence.py
"""

import os
import sys

# Clean up old test database
db_path = "data/orders_test.db"
if os.path.exists(db_path):
    os.remove(db_path)

from datetime import datetime, timedelta

# Import with test database
from src.core.persistence import OrderDatabase
from src.core.state_manager import StateManager, OrderState, ManagedOrder
from src.core.types import (
    UnifiedOrder, UnifiedPayment, ExchangeId, OrderSide, OrderStatus,
    Currency, CryptoAsset, Counterparty, BankProvider, PaymentDirection, PaymentStatus
)


def create_test_order(external_id: str = "order_12345") -> UnifiedOrder:
    """Create a test order."""
    return UnifiedOrder(
        id=f"unified_{external_id}",
        external_id=external_id,
        exchange=ExchangeId.BINANCE,
        side=OrderSide.SELL,
        status=OrderStatus.PENDING,
        crypto_asset=CryptoAsset.USDT,
        crypto_amount="100.00",
        fiat_currency=Currency.EUR,
        fiat_amount="95.00",
        price="0.95",
        counterparty=Counterparty(name="Test Buyer", real_name="Test Buyer Real"),
        payment_method="SEPA",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def create_test_payment() -> UnifiedPayment:
    """Create a test payment."""
    return UnifiedPayment(
        id="payment_12345",
        external_id="ext_payment_12345",
        provider=BankProvider.JANUAR,
        direction=PaymentDirection.INCOMING,
        status=PaymentStatus.COMPLETED,
        amount="95.00",
        currency=Currency.EUR,
        sender_name="Test Buyer Real",
        payment_method="SEPA",
        created_at=datetime.now(),
    )


def test_persistence():
    print("\n🧪 SQLite Persistence Test\n")
    print("=" * 60)
    
    # Create test database
    test_db = OrderDatabase(db_path)
    print(f"✓ Created test database: {db_path}")
    
    # Create state manager with test DB
    manager = StateManager(db=test_db)
    print("✓ Created StateManager with test database")
    
    # Step 1: Track a new order
    print("\n📋 Step 1: Track new order...")
    order = create_test_order()
    managed = manager.track_order(order)
    print(f"   Order ID: {managed.id}")
    print(f"   State: {managed.state.value}")
    
    # Verify it's in the database
    db_order = test_db.load_order(managed.id)
    assert db_order is not None, "Order not found in database!"
    print("   ✓ Order persisted to database")
    
    # Step 2: Transition state
    print("\n📋 Step 2: Transition to PAYMENT_DETECTED...")
    success = manager.transition(managed.id, OrderState.PAYMENT_DETECTED, "test transition")
    assert success, "Transition failed!"
    
    db_order = test_db.load_order(managed.id)
    assert db_order["state"] == "payment_detected", f"State not updated: {db_order['state']}"
    print("   ✓ State transition persisted")
    
    # Step 3: Check state history
    print("\n📋 Step 3: Check state history...")
    history = test_db.get_order_history(managed.id)
    assert len(history) >= 2, "History not recorded!"
    print(f"   Found {len(history)} history entries:")
    for h in history:
        print(f"   - {h['from_state']} → {h['to_state']} ({h['reason']})")
    
    # Step 4: Match a payment
    print("\n📋 Step 4: Match payment...")
    payment = create_test_payment()
    manager.match_payment(managed.id, payment)
    
    db_order = test_db.load_order(managed.id)
    assert db_order["matched_payment"] is not None, "Payment not persisted!"
    print("   ✓ Matched payment persisted")
    
    # Step 5: Test recovery (simulate restart)
    print("\n📋 Step 5: Simulate restart (reload from DB)...")
    del manager
    
    # Create new manager - should load from DB
    manager2 = StateManager(db=test_db)
    
    assert len(manager2._orders) == 1, f"Expected 1 order, got {len(manager2._orders)}"
    recovered = manager2.get_by_external("order_12345")
    assert recovered is not None, "Order not recovered!"
    assert recovered.state == OrderState.PAYMENT_DETECTED, f"Wrong state: {recovered.state}"
    assert recovered.matched_payment is not None, "Payment not recovered!"
    print(f"   ✓ Order recovered: {recovered.id}")
    print(f"   ✓ State: {recovered.state.value}")
    print(f"   ✓ Payment: {recovered.matched_payment.id}")
    
    # Step 6: Get stats
    print("\n📋 Step 6: Database stats...")
    stats = test_db.get_stats()
    print(f"   Total orders: {stats['total_orders']}")
    print(f"   By state: {stats['by_state']}")
    print(f"   By exchange: {stats['by_exchange']}")
    
    # Cleanup
    os.remove(db_path)
    print(f"\n   ✓ Cleaned up test database")
    
    print("\n" + "=" * 60)
    print("✅ All persistence tests passed!\n")


if __name__ == "__main__":
    test_persistence()
