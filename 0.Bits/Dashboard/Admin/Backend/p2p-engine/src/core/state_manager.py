"""
STATE MANAGER
=============
Central order state machine shared by ALL exchanges and banks.
Handles state transitions, event emission, and persistence.

SAFETY INVARIANTS:
1. Terminal states (COMPLETED, CANCELLED, EXPIRED, REFUNDED) are final — no transitions out, even with force=True (S1).
2. Every state change is persisted BEFORE the method returns — on failure, in-memory state is rolled back.
3. Per-order asyncio.Lock prevents concurrent transitions.

Order State Flow:
    NEW → PENDING → PAID → RELEASING → COMPLETED
                  ↘ CANCELLED
                  ↘ APPEALED → RESOLVED
                  ↘ EXPIRED
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import uuid4
import asyncio
import json

from pydantic import BaseModel, Field

from .types import (
    ExchangeId,
    OrderSide,
    OrderState,  # Now imported from types.py (unified enum)
    UnifiedOrder,
    UnifiedPayment,
    Currency,
    CryptoAsset,
)
from .persistence import OrderDatabase, order_db

# Re-export OrderState for backwards compatibility
__all__ = ["OrderState", "ManagedOrder", "OrderEvent", "StateManager", "state_manager"]


class ManagedOrder(BaseModel):
    """
    An order being tracked by the state manager.
    Wraps UnifiedOrder with internal state and metadata.
    """
    id: str = Field(default_factory=lambda: f"mo_{uuid4().hex[:12]}")
    
    # Core order data (from exchange)
    order: UnifiedOrder
    
    # Internal state
    state: OrderState = OrderState.NEW
    state_history: list[dict[str, Any]] = Field(default_factory=list)
    
    # Linked data
    matched_payment: UnifiedPayment | None = None
    chat_last_read: datetime | None = None
    payout_details: dict[str, Any] | None = None  # Buy orders: prepared payout payload
    
    needs_human_review: bool = False
    auto_release_approved: bool = False
    is_third_party: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    paid_at: datetime | None = None  # When buyer marked order as paid
    payout_sent_at: datetime | None = None  # Buy orders: when EUR was sent via Januar
    
    # Error tracking
    last_error: str | None = None
    retry_count: int = 0


# =============================================================================
# EVENT TYPES
# =============================================================================

class OrderEvent(str, Enum):
    """Events emitted by state manager."""
    ORDER_NEW = "order.new"
    ORDER_STATE_CHANGED = "order.state_changed"
    ORDER_MARKED_AS_PAID = "order.marked_as_paid"
    ORDER_PAYMENT_VERIFIED = "order.payment_verified"
    ORDER_RELEASED = "order.released"
    ORDER_COMPLETED = "order.completed"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_APPEALED = "order.appealed"
    ORDER_ERROR = "order.error"
    ORDER_NEEDS_ATTENTION = "order.needs_attention"
    THIRD_PARTY_DETECTED = "order.third_party"
    CHAT_NEW_MESSAGE = "chat.new_message"


EventHandler = Callable[[OrderEvent, ManagedOrder, dict[str, Any]], None]


# =============================================================================
# STATE MANAGER
# =============================================================================

class StateManager:
    """
    Central state machine for all P2P orders.
    
    Used by all exchanges and banks - provides:
    - Order tracking by internal ID and external ID
    - State transitions with validation
    - Event emission for observers
    - Payment matching
    """
    
    def __init__(self, db: OrderDatabase | None = None):
        self._orders: dict[str, ManagedOrder] = {}  # id -> ManagedOrder
        self._by_external: dict[str, str] = {}  # external_id -> id
        self._handlers: dict[OrderEvent, list[EventHandler]] = {}
        self._db = db or order_db  # SQLite persistence
        self._order_locks: dict[str, asyncio.Lock] = {}  # Per-order locking for concurrent safety
        
        # Load existing orders from database
        self._load_from_db()
    
    def get_lock(self, order_id: str) -> asyncio.Lock:
        """Get or create an asyncio.Lock for a specific order. Prevents concurrent operations."""
        if order_id not in self._order_locks:
            self._order_locks[order_id] = asyncio.Lock()
        return self._order_locks[order_id]

    def _schedule_lock_cleanup(self, order_id: str) -> None:
        """
        Schedule removal of the per-order lock after a brief delay.

        AUDIT FIX: _order_locks grew unboundedly — locks for completed/cancelled
        orders were never cleaned up. This schedules cleanup 5s after terminal
        state entry, giving in-flight operations time to release the lock.
        """
        async def _delayed_cleanup():
            await asyncio.sleep(5)
            self._order_locks.pop(order_id, None)

        try:
            asyncio.create_task(_delayed_cleanup())
        except RuntimeError:
            # No running event loop (e.g. during tests) — skip cleanup
            pass
    
    def reset_in_memory(self) -> None:
        """
        Clear in-memory state. Call after archiving/resetting the database
        so the orchestrator can rebuild state from the exchange.
        """
        self._orders.clear()
        self._by_external.clear()
        import logging
        logging.getLogger(__name__).info("Cleared in-memory order state.")

    
    def _load_from_db(self) -> None:
        """Restore orders from database on startup."""
        _logger = __import__("logging").getLogger(__name__)
        try:
            rows = self._db.load_active_orders()
            _logger.info("Loading %d active orders from database...", len(rows))
            
            for row in rows:
                order_data = json.loads(row["order_data"])
                order = UnifiedOrder.model_validate(order_data)
                
                # Parse paid_at if present
                paid_at = None
                if row.get("paid_at"):
                    paid_at = datetime.fromisoformat(row["paid_at"])
                
                # P0-5: Parse payout_sent_at if present (critical for restart safety)
                payout_sent_at = None
                if row.get("payout_sent_at"):
                    payout_sent_at = datetime.fromisoformat(row["payout_sent_at"])
                
                managed = ManagedOrder(
                    id=row["id"],
                    order=order,
                    state=OrderState(row["state"]),
                    needs_human_review=bool(row["needs_human_review"]),
                    auto_release_approved=bool(row["auto_release_approved"]),
                    last_error=row["last_error"],
                    retry_count=row["retry_count"],
                    paid_at=paid_at,
                    payout_sent_at=payout_sent_at,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                
                # Restore matched payment
                if row["matched_payment"]:
                    payment_data = json.loads(row["matched_payment"])
                    managed.matched_payment = UnifiedPayment.model_validate(payment_data)
                
                # P1-C: Restore payout_details from DB snapshot
                if row.get("payout_details_json"):
                    managed.payout_details = json.loads(row["payout_details_json"])
                
                self._orders[managed.id] = managed
                self._by_external[order.external_id] = managed.id
            
            _logger.info("Restored %d orders", len(self._orders))
        except Exception as e:
            _logger.error("Error loading orders from DB: %s", e)
    
    def _persist(self, order: ManagedOrder) -> None:
        """Save order to database. Raises on failure to prevent desync."""
        try:
            self._db.save_order(order)
        except Exception as e:
            print(f"❌ CRITICAL: Failed to persist order {order.id}: {e}")
            raise  # Re-raise — caller must handle rollback
    
    # -------------------------------------------------------------------------
    # EVENT SYSTEM
    # -------------------------------------------------------------------------
    
    def on(self, event: OrderEvent, handler: EventHandler) -> None:
        """Register an event handler."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
    
    def off(self, event: OrderEvent, handler: EventHandler) -> None:
        """Unregister an event handler."""
        if event in self._handlers:
            self._handlers[event].remove(handler)
    
    def _emit(self, event: OrderEvent, order: ManagedOrder, data: dict[str, Any] | None = None) -> None:
        """Emit an event to all registered handlers."""
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    handler(event, order, data or {})
                except Exception as e:
                    print(f"Event handler error: {e}")
    
    # -------------------------------------------------------------------------
    # ORDER MANAGEMENT
    # -------------------------------------------------------------------------
    
    def track_order(
        self, 
        order: UnifiedOrder,
    ) -> ManagedOrder:
        """
        Start tracking a new order.
        If already tracked, returns existing managed order.
        """
        # Check if already tracked
        existing_id = self._by_external.get(order.external_id)
        if existing_id and existing_id in self._orders:
            return self._orders[existing_id]
        
        # Create new managed order
        managed = ManagedOrder(
            order=order,
        )
        
        # Determine initial state based on order status
        managed.state = self._status_to_state(order.status, order.side)
        managed.state_history.append({
            "from": None,
            "to": managed.state.value,
            "at": datetime.now().isoformat(),
            "reason": "initial"
        })
        
        # Store
        self._orders[managed.id] = managed
        self._by_external[order.external_id] = managed.id
        
        # Persist to database
        self._persist(managed)
        self._db.save_state_change(managed.id, None, managed.state.value, "initial")
        
        # Emit event
        self._emit(OrderEvent.ORDER_NEW, managed)
        
        return managed
    
    def get_order(self, id: str) -> ManagedOrder | None:
        """Get order by internal ID."""
        return self._orders.get(id)
    
    def get_by_external(self, external_id: str) -> ManagedOrder | None:
        """Get order by exchange order ID."""
        internal_id = self._by_external.get(external_id)
        if internal_id:
            return self._orders.get(internal_id)
        return None
    
    def get_by_internal(self, internal_order_number: str) -> ManagedOrder | None:
        """Get order by internal order number (e.g., BIN-12345678)."""
        for managed in self._orders.values():
            if managed.order.internal_order_number == internal_order_number:
                return managed
        return None
    
    def get_orders_by_state(self, state: OrderState) -> list[ManagedOrder]:
        """Get all orders in a specific state."""
        return [o for o in self._orders.values() if o.state == state]
    
    def get_active_orders(self) -> list[ManagedOrder]:
        """Get all non-terminal orders."""
        terminal = {OrderState.COMPLETED, OrderState.CANCELLED, OrderState.EXPIRED}
        return [o for o in self._orders.values() if o.state not in terminal]
    
    # -------------------------------------------------------------------------
    # STATE TRANSITIONS
    # -------------------------------------------------------------------------
    
    # S1: Terminal states that MUST NOT be transitioned out of, even with force=True.
    # SAFETY: These represent irreversible real-world actions (money moved, crypto released).
    TERMINAL_STATES = {OrderState.COMPLETED, OrderState.CANCELLED, OrderState.EXPIRED, OrderState.REFUNDED}

    def transition(
        self,
        order_id: str,
        to_state: OrderState,
        reason: str = "",
        data: dict[str, Any] | None = None,
        force: bool = False,
    ) -> bool:
        """
        Transition an order to a new state.
        Returns True if transition was valid and applied.
        
        Args:
            force: If True, bypass state validation (used for sync cleanup).
                   S1: Even with force=True, terminal states (COMPLETED, CANCELLED,
                   EXPIRED, REFUNDED) cannot be transitioned out of.
        """
        order = self._orders.get(order_id)
        if not order:
            return False
        
        # S1: TERMINAL STATE GUARD — no transitions out of terminal states, ever.
        # SAFETY: This prevents accidentally re-processing completed/cancelled orders,
        # which could lead to double payouts or double releases.
        if order.state in self.TERMINAL_STATES:
            import logging
            logging.getLogger(__name__).warning(
                f"🚨 BLOCKED: Cannot transition {order_id} out of terminal state "
                f"{order.state.value} (requested: {to_state.value}, force={force})"
            )
            return False
        
        # Validate transition (unless forced)
        if not force and not self._is_valid_transition(order.state, to_state):
            import logging
            logging.getLogger(__name__).warning(f"Invalid transition: {order.state} → {to_state}")
            return False
        
        # Enforce reason for AGENT_REQUIRED (Safety Fallback)
        if to_state == OrderState.AGENT_REQUIRED and not reason:
            import logging
            logging.getLogger(__name__).warning(f"⚠️ Entering AGENT_REQUIRED without reason for {order_id}. Injecting default.")
            reason = "CRITICAL_MISSING_REASON"
        
        # Apply transition
        old_state = order.state
        order.state = to_state
        order.updated_at = datetime.now()
        order.state_history.append({
            "from": old_state.value,
            "to": to_state.value,
            "at": order.updated_at.isoformat(),
            "reason": reason,
            "data": data
        })
        
        # Emit event
        self._emit(OrderEvent.ORDER_STATE_CHANGED, order, {
            "from": old_state.value,
            "to": to_state.value,
            "reason": reason
        })
        
        # Emit specific events for certain transitions
        if to_state == OrderState.COMPLETED:
            self._emit(OrderEvent.ORDER_COMPLETED, order)
        elif to_state == OrderState.CANCELLED:
            self._emit(OrderEvent.ORDER_CANCELLED, order)
        elif to_state == OrderState.APPEALED:
            self._emit(OrderEvent.ORDER_APPEALED, order)
        
        # Persist to database — rollback on failure
        try:
            self._persist(order)
            self._db.save_state_change(order_id, old_state.value, to_state.value, reason, data)
        except Exception as e:
            # Rollback in-memory state to prevent desync
            import logging
            logging.getLogger(__name__).error(
                f"🔄 Rolling back {order_id}: {to_state.value} → {old_state.value} (persist failed: {e})"
            )
            order.state = old_state
            order.state_history.pop()  # Remove the failed transition from history
            return False

        # AUDIT FIX: Clean up per-order lock when entering terminal state
        # Prevents unbounded memory growth from completed/cancelled orders
        if to_state in self.TERMINAL_STATES:
            self._schedule_lock_cleanup(order_id)

        return True
    
    def _is_valid_transition(self, from_state: OrderState, to_state: OrderState) -> bool:
        """Check if a state transition is valid. Delegates to OrderState.can_transition_to()."""
        return from_state.can_transition_to(to_state)
    
    def _status_to_state(self, status: OrderState, side: OrderSide) -> OrderState:
        """
        Map exchange order status to internal state.
        
        Since status is now OrderState, this mostly passes through.
        MARKED_AS_PAID orders stay as MARKED_AS_PAID until payment is
        verified and release_crypto() is called directly.
        """
        # Just pass through the Binance status - state machine handles transitions
        # MARKED_AS_PAID stays as MARKED_AS_PAID until payment is verified
        return status
    
    # -------------------------------------------------------------------------
    # PAYMENT MATCHING
    # -------------------------------------------------------------------------
    
    def match_payment(self, order_id: str, payment: UnifiedPayment) -> bool:
        """
        Match a payment to an order.
        This is called when we detect incoming fiat that matches an order.
        """
        order = self._orders.get(order_id)
        if not order:
            return False
        
        order.matched_payment = payment
        order.updated_at = datetime.now()
        
        self._emit(OrderEvent.ORDER_MARKED_AS_PAID, order, {
            "payment_id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency.value
        })
        
        # Persist to database
        self._persist(order)
        
        return True
    

    
    def update_counterparty_real_name(self, order_id: str, real_name: str) -> None:
        """Update counterparty real name from chat or other sources."""
        order = self._orders.get(order_id)
        if order and order.order.counterparty:
            old_name = order.order.counterparty.real_name
            if old_name != real_name:
                order.order.counterparty.real_name = real_name
                order.updated_at = datetime.now()
                self._persist(order)
                print(f"👤 Updated counterparty real_name for {order.order.external_id}: {real_name}")
    
    # -------------------------------------------------------------------------
    # FLAGS
    # -------------------------------------------------------------------------
    
    
    def flag_for_review(self, order_id: str, reason: str) -> None:
        """Flag order for human review."""
        order = self._orders.get(order_id)
        if order:
            order.needs_human_review = True
            order.updated_at = datetime.now()
            self._emit(OrderEvent.ORDER_NEEDS_ATTENTION, order, {"reason": reason})
            self._persist(order)
    
    def flag_as_third_party(self, order_id: str, reason: str) -> None:
        """
        Flag order as having a third-party payment.
        
        This happens when:
        - Reference matches correctly
        - Amount matches
        - But sender name != buyer name
        
        Transition to THIRD_PARTY_CONFIRMED state.
        """
        order = self._orders.get(order_id)
        if order:
            order.is_third_party = True
            order.updated_at = datetime.now()
            self._emit(OrderEvent.THIRD_PARTY_DETECTED, order, {"reason": reason})
            # Transition to THIRD_PARTY_CONFIRMED state
            self.transition(order_id, OrderState.THIRD_PARTY_CONFIRMED, f"third_party: {reason}")
            self._persist(order)
    
    def set_error(self, order_id: str, error: str) -> None:
        """Record an error on the order."""
        order = self._orders.get(order_id)
        if order:
            order.last_error = error
            order.retry_count += 1
            order.updated_at = datetime.now()
            self._emit(OrderEvent.ORDER_ERROR, order, {"error": error})
            self._persist(order)
            
    def complete_refund(self, order_id: str) -> None:
        """Mark order as refunded."""
        # Transition to REFUNDED
        self.transition(order_id, OrderState.REFUNDED, "refund_completed")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global state manager instance - used by all clients and services
state_manager = StateManager()
