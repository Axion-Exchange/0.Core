#!/usr/bin/env python3
"""
DASHBOARD SIMULATOR
==================
Simulates dashboard actions for KYC decisions.

This script allows manual approve/reject actions until the real dashboard is built.

Usage:
    python -m src.kyc.dashboard_simulator approve BIN-12345678
    python -m src.kyc.dashboard_simulator reject BIN-12345678
    python -m src.kyc.dashboard_simulator list   # List orders pending review
"""

import sys
import asyncio
from datetime import datetime


def get_state_manager():
    """Get state manager singleton."""
    from src.core.state_manager import state_manager
    return state_manager


def list_pending_review():
    """List all orders flagged for human review."""
    sm = get_state_manager()
    
    pending = [o for o in sm._orders.values() if o.needs_human_review]
    
    if not pending:
        print("\n📋 No orders pending review\n")
        return
    
    print(f"\n📋 Orders Pending Review ({len(pending)}):")
    print("-" * 60)
    
    for order in pending:
        print(f"""
  📦 {order.order.internal_order_number}
     External ID: {order.order.external_id}
     Customer: {order.order.counterparty.name if order.order.counterparty else 'Unknown'}
     Amount: {order.order.fiat_amount} {order.order.fiat_currency.value} → {order.order.crypto_amount} {order.order.crypto_asset.value}
     State: {order.state.value}
     KYC Status: {order.kyc_status or 'None'}
     Updated: {order.updated_at.strftime('%Y-%m-%d %H:%M')}
""")
    print("-" * 60)


def approve_order(internal_order_number: str):
    """Approve KYC for an order (dashboard approval)."""
    sm = get_state_manager()
    
    managed = sm.get_by_internal(internal_order_number)
    if not managed:
        print(f"❌ Order not found: {internal_order_number}")
        return False
    
    # Clear review flag and approve KYC
    managed.needs_human_review = False
    sm.complete_kyc(managed.id)  # Sets kyc_status = "passed"
    
    print(f"✅ Approved KYC for {internal_order_number}")
    print(f"   kyc_status is now: {managed.kyc_status}")
    print(f"   Chatter will notify customer on next poll")
    return True


def reject_order(internal_order_number: str):
    """Reject KYC for an order (dashboard rejection)."""
    sm = get_state_manager()
    
    managed = sm.get_by_internal(internal_order_number)
    if not managed:
        print(f"❌ Order not found: {internal_order_number}")
        return False
    
    # Clear review flag and reject KYC
    managed.needs_human_review = False
    sm.reject_kyc(managed.id)  # Sets kyc_status = "rejected"
    
    print(f"❌ Rejected KYC for {internal_order_number}")
    print(f"   kyc_status is now: {managed.kyc_status}")
    print(f"   Chatter will notify customer on next poll")
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    action = sys.argv[1].lower()
    
    if action == "list":
        list_pending_review()
    
    elif action == "approve":
        if len(sys.argv) < 3:
            print("Usage: dashboard_simulator approve <internal_order_number>")
            print("Example: dashboard_simulator approve BIN-12345678")
            return
        approve_order(sys.argv[2])
    
    elif action == "reject":
        if len(sys.argv) < 3:
            print("Usage: dashboard_simulator reject <internal_order_number>")
            print("Example: dashboard_simulator reject BIN-12345678")
            return
        reject_order(sys.argv[2])
    
    else:
        print(f"Unknown action: {action}")
        print("Valid actions: list, approve, reject")


if __name__ == "__main__":
    main()
