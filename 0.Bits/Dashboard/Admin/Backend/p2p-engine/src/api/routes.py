"""
UNIFIED API ROUTES
==================
FastAPI routes providing a unified interface to all clients.
"""

import logging
import subprocess

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from typing import Any

from src.api.auth import verify_api_key
from src.core.types import (
    ApiResponse,
    ExchangeId,
    UnifiedOrder,
    UnifiedBalance,
    UnifiedPayment,
    UnifiedAd,
    ChatMessage,
)

# V4-01: All routes require X-API-Key authentication
router = APIRouter(prefix="/api", tags=["unified"], dependencies=[Depends(verify_api_key)])

_logger = logging.getLogger("api.routes")


# =============================================================================
# P0-4: Git SHA helper (cached at import time)
# =============================================================================

def get_git_sha() -> str:
    """Return short git SHA of HEAD. Returns 'unknown' if git is unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True, timeout=5, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"

_GIT_SHA = get_git_sha()


# =============================================================================
# HELPER: Resolve Order by Internal Order Number
# =============================================================================

def resolve_order(internal_order_number: str):
    """
    Resolve an order by internal order number (e.g., BI085824).
    
    Supports:
    - Internal order number: BI085824 (preferred)
    - Managed order ID: mo_abc123def456
    - External order ID: 22852216329195085824 (fallback for backwards compatibility)
    
    Returns:
        ManagedOrder or None
    """
    from src.core.state_manager import state_manager
    
    # Try internal order number first (e.g., BI085824)
    managed = state_manager.get_by_internal(internal_order_number)
    if managed:
        return managed
    
    # Try managed order ID (e.g., mo_abc123def456)
    if internal_order_number.startswith("mo_"):
        managed = state_manager.get_order(internal_order_number)
        if managed:
            return managed
    
    # Fallback: Try external order ID for backwards compatibility
    managed = state_manager.get_by_external(internal_order_number)
    return managed


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def health_check() -> dict[str, str]:
    """API health check."""
    return {"status": "ok", "service": "p2p-automation"}


@router.get("/version")
async def get_version() -> dict[str, str]:
    """P0-4: Return deployed version for deployment drift detection."""
    return {"git_sha": _GIT_SHA, "service": "PearV2"}


# =============================================================================
# ORDERS
# =============================================================================

@router.get("/orders")
async def get_orders(
    exchange: ExchangeId | None = Query(None, description="Filter by exchange"),
    status: str | None = Query(None, description="Filter by status"),
) -> ApiResponse[list[dict]]:
    """
    Get all managed orders from state manager.
    
    Optionally filter by exchange or status.
    """
    from src.core.state_manager import state_manager
    
    all_orders = state_manager.get_active_orders()
    
    result = []
    for managed in all_orders:
        order_dict = managed.order.model_dump()
        order_dict["internal_order_number"] = managed.order.internal_order_number
        order_dict["internal_state"] = managed.state.value
        order_dict["needs_human_review"] = managed.needs_human_review
        order_dict["is_third_party"] = managed.is_third_party
        order_dict["auto_release_approved"] = managed.auto_release_approved
        
        # Apply filters
        if exchange and managed.order.exchange != exchange:
            continue
        if status and managed.state.value != status:
            continue
            
        result.append(order_dict)
    
    return ApiResponse(success=True, data=result)


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
) -> ApiResponse[dict | None]:
    """
    Get a specific order.
    
    Accepts: internal order number (BI085824), managed ID (mo_xxx), or external ID.
    """
    managed = resolve_order(order_id)
    
    if not managed:
        return ApiResponse(success=True, data=None)
    
    order_dict = managed.order.model_dump()
    order_dict["internal_order_number"] = managed.order.internal_order_number
    order_dict["internal_state"] = managed.state.value
    order_dict["needs_human_review"] = managed.needs_human_review
    order_dict["is_third_party"] = managed.is_third_party
    order_dict["auto_release_approved"] = managed.auto_release_approved
    order_dict["matched_payment"] = managed.matched_payment.model_dump() if managed.matched_payment else None
    
    return ApiResponse(success=True, data=order_dict)


@router.post("/orders/{order_id}/mark-paid")
async def mark_order_paid(
    order_id: str,
) -> ApiResponse[dict]:
    """
    Mark a buy order as paid (triggers exchange API call).
    
    Accepts: internal order number (BI085824), managed ID (mo_xxx), or external ID.
    """
    from src.core.registry import registry
    
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(success=False, data={"marked": False, "error": f"Order not found: {order_id}"})
    
    client = registry.get_exchange_api(managed.order.exchange)
    if not client:
        return ApiResponse(success=False, data={"marked": False, "error": f"No client for {managed.order.exchange.value}"})
    
    try:
        result = await client.mark_order_paid(managed.order.external_id)
        return ApiResponse(success=True, data={
            "marked": result, 
            "order_id": order_id,
            "internal_order_number": managed.order.internal_order_number,
            "exchange": managed.order.exchange.value,
        })
    except Exception as e:
        return ApiResponse(success=False, data={"marked": False, "error": str(e)})


@router.post("/orders/{order_id}/release")
async def release_order(
    order_id: str,
) -> ApiResponse[dict]:
    """
    Release crypto for a sell order.
    
    Accepts: internal order number (BI085824), managed ID (mo_xxx), or external ID.
    Routes through orchestrator to ensure per-order locking and state guards.
    """
    from src.services.order_orchestrator import orchestrator
    
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(success=False, data={"released": False, "error": f"Order not found: {order_id}"})
    
    try:
        result = await orchestrator.release_crypto(managed.id)
        return ApiResponse(success=True, data={
            "released": result, 
            "order_id": order_id,
            "internal_order_number": managed.order.internal_order_number,
            "exchange": managed.order.exchange.value,
        })
    except Exception as e:
        return ApiResponse(success=False, data={"released": False, "error": str(e)})


@router.post("/orders/{order_id}/execute-payout")
async def execute_buy_payout(
    order_id: str,
    recipient_name: str | None = Query(None, description="Override recipient name"),
    recipient_iban: str | None = Query(None, description="Override recipient IBAN"),
    admin_reason: str | None = Query(None, description="Required justification for manual override"),
) -> ApiResponse[dict]:
    """
    Execute a buy-order payout (send EUR to seller + mark paid on Binance).
    
    If recipient_name and recipient_iban are provided, they override the 
    auto-fetched payment details (manual payout). Requires admin_reason.
    
    Accepts: internal order number (BI085824), managed ID (mo_xxx), or external ID.
    """
    from src.services.order_orchestrator import orchestrator
    
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(success=False, data={"paid": False, "error": f"Order not found: {order_id}"})
    
    # P0-B: If manual override params provided, require admin_reason and re-screen
    if recipient_name and recipient_iban:
        if not admin_reason:
            return ApiResponse(
                success=False,
                data={"paid": False, "error": "admin_reason required for manual payout override"},
            )
        
        # P0-B: Screen the override IBAN before proceeding
        from src.services.iban_screener import screen_iban
        screening = screen_iban(recipient_iban)
        if screening.is_blocked:
            _logger.critical(
                "MANUAL PAYOUT BLOCKED: order=%s iban=%s*** reason=%s admin=%s",
                order_id, recipient_iban[:4], screening.reason, admin_reason,
            )
            return ApiResponse(
                success=False,
                data={"paid": False, "error": f"IBAN blocked: {screening.reason}"},
            )
        
        # Audit log for manual override
        _logger.warning(
            "MANUAL PAYOUT OVERRIDE: order=%s reason='%s' iban=%s*** name=%s screening=%s",
            order_id, admin_reason, recipient_iban[:4], recipient_name, screening.risk_level.value,
        )
        
        managed.payout_details = {
            "amount": managed.order.fiat_amount,
            "currency": managed.order.fiat_currency.value,
            "recipient_name": recipient_name,
            "recipient_account": recipient_iban,
            "reference": managed.order.internal_order_number,
            "internal_note": f"Manual buy payout: {managed.order.external_id} | reason: {admin_reason}",
            "screening_passed": True,
            "manual_override": True,
            "admin_reason": admin_reason,
            "prepared_at": __import__("datetime").datetime.now().isoformat(),
        }
    
    try:
        result = await orchestrator.execute_buy_payout(managed.id)
        return ApiResponse(success=result, data={
            "paid": result,
            "order_id": order_id,
            "internal_order_number": managed.order.internal_order_number,
            "exchange": managed.order.exchange.value,
            "payout_details": managed.payout_details,
        })
    except Exception as e:
        return ApiResponse(success=False, data={"paid": False, "error": str(e)})

# =============================================================================
# AGENT ENDPOINTS (State Manager Access)
# =============================================================================

@router.get("/state/{state}/orders")
async def get_orders_by_state(
    state: str,
) -> ApiResponse[list[dict]]:
    """
    Get all orders in a specific internal state.
    
    Valid states: new, awaiting_payment, marked_as_paid, delayed, 
                  third_party_confirmed, releasing,
                  completed, cancelled, expired, error, 
                  agent_required, agent_processing, refunded
    """
    from src.core.state_manager import state_manager
    from src.core.types import OrderState
    
    try:
        order_state = OrderState(state)
    except ValueError:
        return ApiResponse(
            success=False, 
            data=[], 
            error=f"Invalid state: {state}. Valid states: {[s.value for s in OrderState]}"
        )
    
    orders = state_manager.get_orders_by_state(order_state)
    
    result = []
    for managed in orders:
        order_dict = managed.order.model_dump()
        order_dict["internal_state"] = managed.state.value
        order_dict["needs_human_review"] = managed.needs_human_review
        order_dict["is_third_party"] = managed.is_third_party
        order_dict["auto_release_approved"] = managed.auto_release_approved
        order_dict["paid_at"] = managed.paid_at.isoformat() if managed.paid_at else None
        order_dict["matched_payment_id"] = managed.matched_payment.external_id if managed.matched_payment else None
        result.append(order_dict)
    
    return ApiResponse(success=True, data=result, meta={"state": state, "count": len(result)})


@router.get("/order/{order_id}/details")
async def get_order_full_details(
    order_id: str,
) -> ApiResponse[dict | None]:
    """
    Get full order details including matched payment and all metadata.
    
    Accepts:
    - Internal order number: BI085824 (preferred)
    - Managed order ID: mo_abc123def456
    - External order ID: 22852216329195085824 (backwards compatible)
    """
    managed = resolve_order(order_id)
    
    if not managed:
        return ApiResponse(success=True, data=None)
    
    return ApiResponse(success=True, data={
        # Core identifiers
        "id": managed.id,
        "external_id": managed.order.external_id,
        "internal_order_number": managed.order.internal_order_number,
        "exchange": managed.order.exchange.value,
        "side": managed.order.side.value,
        
        # State machine
        "state": managed.state.value,
        "state_history": managed.state_history,
        
        # Trade details
        "crypto_asset": managed.order.crypto_asset.value,
        "crypto_amount": managed.order.crypto_amount,
        "fiat_currency": managed.order.fiat_currency.value,
        "fiat_amount": managed.order.fiat_amount,
        "price": managed.order.price,
        
        # Counterparty info
        "counterparty": {
            "name": managed.order.counterparty.name,
            "real_name": managed.order.counterparty.real_name,
            "trade_count": managed.order.counterparty.trade_count,
            "completion_rate": managed.order.counterparty.completion_rate,
        },
        "payment_method": managed.order.payment_method,
        
        # Flags
        "needs_human_review": managed.needs_human_review,
        "is_third_party": managed.is_third_party,
        "auto_release_approved": managed.auto_release_approved,
        
        # Matched payment
        "matched_payment": managed.matched_payment.model_dump() if managed.matched_payment else None,
        
        # Timestamps
        "paid_at": managed.paid_at.isoformat() if managed.paid_at else None,
        "created_at": managed.created_at.isoformat(),
        "updated_at": managed.updated_at.isoformat(),
        "expires_at": managed.order.expires_at.isoformat() if managed.order.expires_at else None,
        "chat_last_read": managed.chat_last_read.isoformat() if managed.chat_last_read else None,
        
        # Error tracking
        "last_error": managed.last_error,
        "retry_count": managed.retry_count,
        
        # Raw exchange data (for debugging)
        "raw": managed.order.raw,
    })


@router.get("/order/{order_id}/history")
async def get_order_history(
    order_id: str,
) -> ApiResponse[list[dict]]:
    """
    Get state transition history for an order.
    
    Accepts: internal order number (BI085824), managed ID (mo_xxx), or external ID.
    Returns chronological list of all state changes.
    """
    from src.core.persistence import order_db
    
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(success=True, data=[], meta={"order_found": False})
    
    history = order_db.get_order_history(managed.id)
    
    return ApiResponse(success=True, data=history, meta={"order_id": order_id, "internal_order_number": managed.order.internal_order_number, "count": len(history)})


@router.get("/system/valid-transitions")
async def get_valid_transitions() -> ApiResponse[dict]:
    """
    Get all valid state transitions.
    
    Returns a map of: { state: [valid_target_states] }
    """
    from src.core.types import OrderState
    
    transitions = OrderState.valid_transitions()
    
    result = {}
    for state, targets in transitions.items():
        result[state.value] = sorted([t.value for t in targets])
    
    return ApiResponse(success=True, data=result)


@router.post("/order/{order_id}/transition")
async def transition_order_state(
    order_id: str,
    to_state: str = Query(..., description="Target state"),
    reason: str = Query("manual_transition", description="Reason for transition"),
) -> ApiResponse[dict]:
    """
    Manually transition an order to a new state.
    
    Accepts: internal order number (BI085824), managed ID (mo_xxx), or external ID.
    All transitions must pass state validation — no force bypass.
    """
    from src.core.state_manager import state_manager
    from src.core.types import OrderState
    
    # Validate target state
    try:
        target_state = OrderState(to_state)
    except ValueError:
        return ApiResponse(
            success=False, 
            data={"transitioned": False},
            error=f"Invalid state: {to_state}"
        )
    
    # Find order
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(
            success=False, 
            data={"transitioned": False},
            error=f"Order not found: {order_id}"
        )
    
    old_state = managed.state.value
    
    # Attempt transition — always validated, no force bypass (FIX B4)
    success = state_manager.transition(managed.id, target_state, reason)
    
    return ApiResponse(success=True, data={
        "transitioned": success,
        "order_id": order_id,
        "from_state": old_state,
        "to_state": to_state,
        "reason": reason,
    })


# =============================================================================
# BALANCES
# =============================================================================

@router.get("/balances")
async def get_balances(
    source: str | None = Query(None, description="Filter by source: binance, januar"),
) -> ApiResponse[list[dict]]:
    """
    Get balances from all sources.
    
    Sources: binance (spot + funding), januar (EUR).
    """
    from src.core.registry import registry
    
    balances = []
    
    # Binance balances
    if not source or source.lower() == "binance":
        client = registry.get_exchange_api(ExchangeId.BINANCE)
        if client:
            try:
                # Spot balances
                spot = await client.get_spot_balance()
                for asset, amount in spot.items():
                    if float(amount) > 0:
                        balances.append({
                            "source": "binance",
                            "wallet": "spot",
                            "asset": asset,
                            "amount": amount,
                        })
                
                # Funding balances
                funding = await client.get_funding_balance()
                for asset, amount in funding.items():
                    if float(amount) > 0:
                        balances.append({
                            "source": "binance",
                            "wallet": "funding",
                            "asset": asset,
                            "amount": amount,
                        })
            except Exception as e:
                balances.append({"source": "binance", "error": str(e)})
    
    # Januar balances
    if not source or source.lower() == "januar":
        januar = registry.get_payment_api("januar")
        if januar:
            try:
                januar_balances = await januar.get_balances()
                for bal in januar_balances:
                    balances.append({
                        "source": "januar",
                        "wallet": "main",
                        "asset": bal.currency.value,
                        "amount": bal.available,
                    })
            except Exception as e:
                balances.append({"source": "januar", "error": str(e)})
    
    return ApiResponse(success=True, data=balances)




# =============================================================================
# PAYMENTS
# =============================================================================

@router.get("/payments")
async def get_payments(
    provider: str | None = Query(None, description="Filter by provider: januar"),
    currency: str | None = Query(None, description="Filter by currency: EUR"),
    direction: str | None = Query(None, description="incoming or outgoing"),
    limit: int = Query(50, le=100),
) -> ApiResponse[list[dict]]:
    """Get payment transactions from Januar."""
    from src.core.registry import registry
    
    januar = registry.get_payment_api("januar")
    if not januar:
        return ApiResponse(success=False, data=[], error="Januar not configured")
    
    try:
        payments = await januar.get_transactions(
            direction=direction,
            limit=limit
        )
        
        result = []
        for p in payments:
            payment_dict = p.model_dump()
            
            # Apply filters
            if currency and p.currency.value.upper() != currency.upper():
                continue
            
            result.append(payment_dict)
        
        return ApiResponse(success=True, data=result)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))


@router.post("/payments/payout")
async def initiate_payout(
    amount: str = Query(..., description="Amount to send"),
    currency: str = Query("EUR", description="Currency (EUR)"),
    recipient_name: str = Query(..., description="Recipient full name"),
    recipient_iban: str = Query(..., description="Recipient IBAN"),
    reference: str | None = Query(None, description="Payment reference"),
    idempotency_key: str = Query(..., description="V4-03: Unique idempotency key — prevents double sends. Use order ID or UUID."),
) -> ApiResponse[dict | None]:
    """
    Initiate an outgoing EUR payment via Januar.
    
    V4-03 SAFETY: Requires idempotency_key to prevent duplicate payouts.
    The key is forwarded to Januar as replay_id.
    """
    from src.core.registry import registry
    
    januar = registry.get_payment_api("januar")
    if not januar:
        return ApiResponse(success=False, data=None, error="Januar not configured")
    
    try:
        result = await januar.send_payment(
            amount=amount,
            currency=currency,
            recipient_name=recipient_name,
            recipient_iban=recipient_iban,
            reference=reference,
            replay_id=f"manual-payout-{idempotency_key}",
        )
        
        return ApiResponse(success=True, data={
            "payment_id": result.id if result else None,
            "status": result.status.value if result else "failed",
            "amount": amount,
            "recipient": recipient_name,
            "idempotency_key": idempotency_key,
        })
    except Exception as e:
        return ApiResponse(success=False, data=None, error=str(e))


# =============================================================================
# ADVERTISEMENTS
# =============================================================================

@router.get("/ads")
async def get_ads(
    exchange: ExchangeId | None = Query(None),
    side: str | None = Query(None, description="buy or sell"),
) -> ApiResponse[list[dict]]:
    """Get P2P advertisements from exchange."""
    from src.core.registry import registry
    
    target_exchange = exchange or ExchangeId.BINANCE
    client = registry.get_exchange_api(target_exchange)
    
    if not client:
        return ApiResponse(success=False, data=[], error=f"No client for {target_exchange}")
    
    try:
        ads = await client.get_ads()
        
        result = []
        for ad in ads:
            ad_dict = ad.model_dump()
            
            # Apply filters
            if side and ad.side.value.lower() != side.lower():
                continue
            
            result.append(ad_dict)
        
        return ApiResponse(success=True, data=result)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))


@router.patch("/ads/{exchange}/{ad_id}")
async def update_ad(
    exchange: ExchangeId,
    ad_id: str,
    price: str | None = Query(None, description="New price"),
    active: bool | None = Query(None, description="Enable/disable ad"),
    quantity: str | None = Query(None, description="New quantity"),
) -> ApiResponse[dict]:
    """Update an ad's price, status, or quantity."""
    from src.core.registry import registry
    
    client = registry.get_exchange_api(exchange)
    if not client:
        return ApiResponse(success=False, data={"updated": False, "error": f"No client for {exchange}"})
    
    try:
        updated = False
        
        if price is not None:
            await client.update_ad_price(ad_id, price)
            updated = True
        
        if active is not None:
            await client.update_ad_status(ad_id, active)
            updated = True
        
        if quantity is not None:
            await client.update_ad_quantity(ad_id, quantity)
            updated = True
        
        return ApiResponse(success=True, data={
            "updated": updated,
            "ad_id": ad_id,
            "changes": {
                "price": price,
                "active": active,
                "quantity": quantity,
            }
        })
    except Exception as e:
        return ApiResponse(success=False, data={"updated": False, "error": str(e)})


# =============================================================================
# CHAT (Exchange Chat)
# =============================================================================

@router.get("/chat/{order_id}")
async def get_chat_messages(
    order_id: str,
) -> ApiResponse[list[dict]]:
    """
    Get chat messages for an order from exchange.
    
    Accepts: internal order number (BI085824), managed ID (mo_xxx), or external ID.
    """
    from src.core.registry import registry
    
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(success=False, data=[], error=f"Order not found: {order_id}")
    
    client = registry.get_exchange_api(managed.order.exchange)
    if not client:
        return ApiResponse(success=False, data=[], error=f"No client for {managed.order.exchange.value}")
    
    try:
        messages = await client.get_chat_messages(managed.order.external_id)
        return ApiResponse(success=True, data=[m.model_dump() for m in messages])
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))


@router.post("/chat/{order_id}")
async def send_chat_message(
    order_id: str,
    message: str = Query(..., description="Message to send"),
) -> ApiResponse[dict]:
    """
    Send a chat message on an order.
    
    Accepts: internal order number (BI085824), managed ID (mo_xxx), or external ID.
    """
    from src.core.registry import registry
    
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(success=False, data={"sent": False, "error": f"Order not found: {order_id}"})
    
    client = registry.get_exchange_api(managed.order.exchange)
    if not client:
        return ApiResponse(success=False, data={"sent": False, "error": f"No client for {managed.order.exchange.value}"})
    
    try:
        result = await client.send_chat_message(managed.order.external_id, message)
        return ApiResponse(success=True, data={
            "sent": result, 
            "order_id": order_id,
            "internal_order_number": managed.order.internal_order_number,
        })
    except Exception as e:
        return ApiResponse(success=False, data={"sent": False, "error": str(e)})


# =============================================================================
# IBAN BLOCKLISTS
# =============================================================================

@router.get("/compliance/blocklists")
async def get_blocklists() -> ApiResponse[dict]:
    """Get current IBAN country blocklists and banned banks."""
    from src.services.iban_screener import get_blocklists
    return ApiResponse(success=True, data=get_blocklists())


@router.post("/compliance/blocklists")
async def update_blocklists(body: dict = Body(...)) -> ApiResponse[dict]:
    """
    FIX B7: Blocklist modification disabled at runtime.
    Blocklists are immutable — changes require code deployment and review.
    """
    return ApiResponse(
        success=False,
        data={},
        error="Blocklist modification disabled. Sanctions lists are immutable at runtime. Update via code deployment."
    )


@router.post("/compliance/iban/check")
async def check_iban(
    iban: str = Query(..., description="IBAN to check"),
    bank_name: str | None = Query(None, description="Optional bank name"),
) -> ApiResponse[dict]:
    """Screen an IBAN against current blocklists."""
    from src.services.iban_screener import screen_iban_with_bank
    result = screen_iban_with_bank(iban, bank_name)
    return ApiResponse(success=True, data=result.to_dict())


# =============================================================================
# AUDIT & COMPLIANCE
# =============================================================================




@router.post("/audit/chat")
async def log_chat_exchange(
    order_id: str = Query(..., description="Order ID"),
    customer_message: str = Query(..., description="Last message from customer"),
    our_reply: str = Query(..., description="Our reply to customer"),
    order_state: str | None = Query(None, description="Current order state"),
) -> ApiResponse[dict]:
    """
    Log a chat exchange (customer message + our reply).
    
    Used for delayed order handling and audit trail.
    """
    from datetime import datetime
    import json
    from pathlib import Path
    
    # Get log directory
    log_dir = Path(__file__).parent.parent.parent / "data" / "chat_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "order_id": order_id,
        "order_state": order_state,
        "customer_message": customer_message,
        "our_reply": our_reply,
    }
    
    # Append to daily log file
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    return ApiResponse(success=True, data={
        "logged": True,
        "order_id": order_id,
        "timestamp": entry["timestamp"],
    })


@router.get("/audit/chat/{order_id}")
async def get_chat_audit_logs(order_id: str) -> ApiResponse[list[dict]]:
    """
    Get chat audit logs for a specific order.
    """
    import json
    from pathlib import Path
    from datetime import datetime, timedelta
    
    log_dir = Path(__file__).parent.parent.parent / "data" / "chat_logs"
    logs = []
    
    # Search last 7 days of logs
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        log_file = log_dir / f"{date.strftime('%Y-%m-%d')}.jsonl"
        
        if log_file.exists():
            with open(log_file, "r") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get("order_id") == order_id:
                        logs.append(entry)
    
    return ApiResponse(success=True, data=logs)


# =============================================================================
# THIRD-PARTY & REFUND
# =============================================================================

@router.post("/order/{order_id}/third-party")
async def mark_third_party(
    order_id: str,
    transaction_id: str = Query(..., description="Januar transaction UUID for the incoming payment"),
) -> ApiResponse[dict]:
    """
    Manually assign a payment as third-party to an order.
    
    Agent provides the Januar transaction ID they found in the Januar app.
    System fetches the payment details, stores it as matched_payment,
    and transitions the order to third_party_confirmed.
    """
    from src.core.state_manager import state_manager
    from src.core.registry import registry
    
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(success=False, data={}, error=f"Order not found: {order_id}")
    
    januar = registry.get_payment_api("januar")
    if not januar:
        return ApiResponse(success=False, data={}, error="Januar not configured")
    
    payment = await januar.get_payment_by_id(transaction_id)
    if not payment:
        return ApiResponse(success=False, data={}, error=f"Payment not found: {transaction_id}")
    
    # Store payment and flag as third party
    state_manager.match_payment(managed.id, payment)
    state_manager.flag_as_third_party(managed.id, f"Manual: agent assigned {transaction_id}")
    
    return ApiResponse(success=True, data={
        "order_id": order_id,
        "internal_order_number": managed.order.internal_order_number,
        "state": "third_party_confirmed",
        "payment": {
            "transaction_id": payment.external_id,
            "amount": payment.amount,
            "sender": payment.sender_name,
            "iban": f"{payment.sender_account[:4]}...{payment.sender_account[-4:]}" if payment.sender_account else None,
        },
    })


@router.post("/order/{order_id}/refund")
async def refund_order(
    order_id: str,
    reason: str = Query("agent_refund", description="Refund reason tag"),
    dry_run: bool = Query(False, description="Validate without sending money"),
) -> ApiResponse[dict]:
    """
    Refund an order's matched payment via Januar and transition to REFUNDED.
    
    Requires matched_payment to be set (either auto-matched or via /third-party).
    """
    from src.core.state_manager import state_manager
    from src.core.registry import registry
    
    managed = resolve_order(order_id)
    if not managed:
        return ApiResponse(success=False, data={"refunded": False}, error=f"Order not found: {order_id}")
    
    payment = managed.matched_payment
    if not payment:
        return ApiResponse(success=False, data={"refunded": False}, error="No matched payment. Use /third-party first to assign a payment.")
    
    if not payment.sender_account or not payment.sender_name:
        return ApiResponse(success=False, data={"refunded": False}, error="Missing sender IBAN/name on payment")
    
    if dry_run:
        return ApiResponse(success=True, data={
            "refunded": False,
            "dry_run": True,
            "order_id": order_id,
            "internal_order_number": managed.order.internal_order_number,
            "amount": payment.amount,
            "recipient": payment.sender_name,
            "iban": f"{payment.sender_account[:4]}...{payment.sender_account[-4:]}",
            "message": "Dry run — no money sent",
        })
    
    januar = registry.get_payment_api("januar")
    if not januar:
        return ApiResponse(success=False, data={"refunded": False}, error="Januar not configured")
    
    try:
        payout = await januar.refund_payment(
            payment=payment,
            reason_tag=reason,
            order=managed,
        )
        
        if not payout:
            return ApiResponse(success=False, data={"refunded": False}, error="Payout initiation failed")
        
        state_manager.complete_refund(managed.id)
        
        return ApiResponse(success=True, data={
            "refunded": True,
            "order_id": order_id,
            "internal_order_number": managed.order.internal_order_number,
            "payout_id": payout.external_id,
            "amount": payment.amount,
            "recipient": payment.sender_name,
            "iban": f"{payment.sender_account[:4]}...{payment.sender_account[-4:]}",
        })
    except Exception as e:
        return ApiResponse(success=False, data={"refunded": False}, error=str(e))
