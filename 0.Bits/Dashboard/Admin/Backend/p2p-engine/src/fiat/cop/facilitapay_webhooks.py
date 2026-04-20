"""
FACILITAPAY WEBHOOK HANDLER
=============================
FastAPI endpoint for receiving FacilitaPay webhook notifications.

DESIGN (C-03 fix):
- PERSIST event to DB BEFORE returning HTTP response
- ALWAYS return 200 after successful persistence (FP does NOT retry)
- Process handlers AFTER persistence — failures are recoverable via reconciliation
- Atomic dedup via INSERT OR IGNORE on UNIQUE constraint

Handles:
- identified: Funds received (PSE pay-in confirmed) or balance allocated (payout)
- exchange_created: FX conversion completed
- wire_created: COP sent to customer (payout settled)
- payment_expired: PSE link expired unused
- payment_refunded: Funds reversed (critical alert)

Exactly-once semantics:
- DB constraint: UNIQUE(notification_id) on fp_webhook_log
- INSERT OR IGNORE returns rowcount=0 if already exists → skip processing
- No read-then-write race condition
"""

import asyncio
import json
import logging
from typing import Any, Callable, Awaitable

from fastapi import APIRouter, Request, Response

from .facilitapay_client import FacilitaPayCopClient
from .facilitapay_models import (
    FPNotificationEnvelope,
    FPTransactionDirection,
    FPTransactionStatus,
    FPWebhookPayload,
)

logger = logging.getLogger("facilitapay.webhooks")


# Type alias for event handlers
WebhookHandler = Callable[[FPWebhookPayload, dict | None], Awaitable[None]]


def create_webhook_router(
    client: FacilitaPayCopClient,
    on_payin_identified: WebhookHandler | None = None,
    on_exchange_created: WebhookHandler | None = None,
    on_wire_created: WebhookHandler | None = None,
    on_payment_expired: WebhookHandler | None = None,
    on_payment_refunded: WebhookHandler | None = None,
) -> APIRouter:
    """
    Create a FastAPI router for FacilitaPay webhook notifications.
    
    Args:
        client: FacilitaPay client instance (for secret verification + DB)
        on_payin_identified: Called when PSE pay-in is confirmed
        on_exchange_created: Called when FX conversion completes
        on_wire_created: Called when COP payout wire is sent
        on_payment_expired: Called when PSE link expires unused
        on_payment_refunded: Called when payment is reversed
        
    Returns:
        FastAPI APIRouter with /webhooks/facilitapay POST endpoint
    """
    router = APIRouter()

    @router.post("/webhooks/facilitapay")
    async def handle_facilitapay_webhook(request: Request) -> Response:
        """
        FacilitaPay webhook endpoint.
        
        INVARIANTS:
        1. Persist raw event BEFORE returning 200
        2. ALWAYS return 200 after persistence (FP does NOT retry)
        3. Dedup is atomic: INSERT OR IGNORE on UNIQUE(notification_id)
        4. Handler failures are logged but do NOT affect HTTP response
        """
        # ── Step 1: Parse body ────────────────────────────────
        try:
            raw_body = await request.body()
            body = json.loads(raw_body)
        except Exception as e:
            logger.error(f"Invalid webhook body: {e}")
            return Response(status_code=200, content="ok")

        notification_data = body.get("notification", {})
        if not notification_data:
            logger.warning("Webhook received with empty notification payload")
            return Response(status_code=200, content="ok")

        # ── Step 2: Parse webhook payload ─────────────────────
        try:
            webhook = FPWebhookPayload(**notification_data)
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            return Response(status_code=200, content="ok")

        # ── Step 3: Verify secret (FAIL CLOSED) ───────────────
        if not webhook.secret or not client.verify_webhook_secret(webhook.secret):
            logger.critical(
                f"🚨 WEBHOOK SECRET VERIFICATION FAILED: type={webhook.type} "
                f"tx={webhook.transaction_id or webhook.transaction_ids} "
                f"secret_present={bool(webhook.secret)}"
            )
            # Do NOT persist, do NOT process — reject completely
            return Response(status_code=401, content="unauthorized")

        # ── Step 4: Generate dedup key ────────────────────────
        dedup_key = _make_dedup_key(webhook)

        # ── Step 5: ATOMIC persist + dedup ────────────────────
        # INSERT OR IGNORE: if notification_id already exists, rowcount=0
        # This is the ONLY dedup mechanism — no separate read step
        tx_ids_str = json.dumps(webhook.transaction_ids) if webhook.transaction_ids else None
        inserted = client.db.log_webhook_atomic(
            notification_id=dedup_key,
            event_type=webhook.type,
            transaction_id=webhook.transaction_id,
            transaction_ids=tx_ids_str,
            raw_json=json.dumps(notification_data),
        )

        if not inserted:
            logger.info(f"Webhook already processed: {dedup_key[:20]}... — skipping")
            return Response(status_code=200, content="ok")

        logger.info(
            f"📨 Webhook persisted: type={webhook.type} "
            f"tx={webhook.transaction_id or webhook.transaction_ids}"
        )

        # ── Step 6: Process handler (AFTER persistence) ───────
        # At this point the event is durable. HTTP 200 will be returned
        # regardless of handler success. Failed handlers are logged
        # for manual investigation and picked up by reconciliation.
        try:
            # Fetch full transaction details for enrichment
            tx_details = None
            if webhook.transaction_id:
                try:
                    tx_details = await client.get_transaction(webhook.transaction_id)
                    # Update local DB status
                    client.db.update_transaction_status(
                        webhook.transaction_id, tx_details.status.value
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to fetch tx details for {webhook.transaction_id[:8]}...: {e}"
                    )

            await _dispatch_webhook(
                webhook=webhook,
                tx_details=tx_details,
                on_payin_identified=on_payin_identified,
                on_exchange_created=on_exchange_created,
                on_wire_created=on_wire_created,
                on_payment_expired=on_payment_expired,
                on_payment_refunded=on_payment_refunded,
            )

            # Mark as fully processed
            client.db.mark_webhook_processed(dedup_key)

            # Update status for batched events
            if webhook.transaction_ids:
                for tx_id in webhook.transaction_ids:
                    try:
                        tx = await client.get_transaction(tx_id)
                        client.db.update_transaction_status(tx_id, tx.status.value)
                    except Exception as e:
                        logger.error(f"Failed to update batched tx {tx_id[:8]}...: {e}")

        except Exception as e:
            logger.error(
                f"🚨 Webhook handler FAILED for {webhook.type} "
                f"dedup_key={dedup_key[:20]}... error={e}",
                exc_info=True,
            )
            # Event is persisted — will be retried by reconciliation sweep.
            # DO NOT re-raise. HTTP 200 is returned below.

        # ALWAYS return 200 — event is persisted, FP does NOT retry
        return Response(status_code=200, content="ok")

    return router


async def _dispatch_webhook(
    webhook: FPWebhookPayload,
    tx_details: Any | None,
    on_payin_identified: WebhookHandler | None,
    on_exchange_created: WebhookHandler | None,
    on_wire_created: WebhookHandler | None,
    on_payment_expired: WebhookHandler | None,
    on_payment_refunded: WebhookHandler | None,
) -> None:
    """Route webhook to appropriate handler."""
    event_type = webhook.type

    if event_type == "identified":
        # Currency-based routing: MXN transactions go to MXN handler
        tx_currency = None
        if tx_details:
            tx_currency = getattr(tx_details, 'currency', None)
            if not tx_currency and hasattr(tx_details, 'raw_data'):
                tx_currency = tx_details.raw_data.get('currency')
        if not tx_currency and isinstance(tx_details, dict):
            tx_currency = tx_details.get('currency')

        if tx_currency == "MXN":
            try:
                from src.fiat.mxn.mxn_handler import _handler_instance as mxn_handler
                if mxn_handler:
                    meta = {}
                    if tx_details:
                        if hasattr(tx_details, 'meta'):
                            meta = tx_details.meta or {}
                        elif isinstance(tx_details, dict):
                            meta = tx_details.get('meta', {})
                    pear_order_id = meta.get('pear_order_id', '')
                    tx_amount = ''
                    if tx_details:
                        if hasattr(tx_details, 'value'):
                            tx_amount = str(tx_details.value)
                        elif isinstance(tx_details, dict):
                            tx_amount = str(tx_details.get('value', '0'))
                    if pear_order_id:
                        logger.info(f"MXN payment identified: {pear_order_id}")
                        await mxn_handler.handle_webhook(pear_order_id, tx_amount, 'identified')
                    else:
                        logger.warning(f"MXN identified webhook without pear_order_id: {webhook.transaction_id}")
                else:
                    logger.warning("MXN handler not running -- cannot process identified webhook")
            except ImportError:
                logger.warning("MXN module not available for webhook routing")
        elif on_payin_identified:
            await on_payin_identified(webhook, tx_details)
        else:
            logger.info(f"Transaction identified: {webhook.transaction_id}")

    elif event_type == "exchange_created":
        if on_exchange_created:
            await on_exchange_created(webhook, tx_details)
        else:
            logger.info(
                f"💱 Exchange created: {webhook.exchange_id} "
                f"for txs: {webhook.transaction_ids}"
            )

    elif event_type == "wire_created":
        if on_wire_created:
            await on_wire_created(webhook, tx_details)
        else:
            logger.info(
                f"🏦 Wire created: {webhook.wire_id} "
                f"for txs: {webhook.transaction_ids}"
            )

    elif event_type == "payment_expired":
        tx_currency = None
        if tx_details:
            tx_currency = getattr(tx_details, 'currency', None) or (tx_details.get('currency') if isinstance(tx_details, dict) else None)
        if tx_currency == "MXN":
            try:
                from src.fiat.mxn.mxn_handler import _handler_instance as mxn_handler
                if mxn_handler:
                    await mxn_handler.handle_payment_expired(webhook.transaction_id)
            except ImportError:
                pass
        elif on_payment_expired:
            await on_payment_expired(webhook, tx_details)
        else:
            logger.warning(f"Payment expired: {webhook.transaction_id}")

    elif event_type in ("payment_refunded", "refunded"):
        logger.critical(
            f"PAYMENT REFUNDED: {webhook.transaction_id} -- "
            f"MANUAL INTERVENTION REQUIRED"
        )
        tx_currency = None
        if tx_details:
            tx_currency = getattr(tx_details, 'currency', None) or (tx_details.get('currency') if isinstance(tx_details, dict) else None)
        if tx_currency == "MXN":
            try:
                from src.fiat.mxn.mxn_handler import _handler_instance as mxn_handler
                if mxn_handler:
                    await mxn_handler.handle_payment_refunded(webhook.transaction_id, event_type)
            except ImportError:
                pass
        elif on_payment_refunded:
            await on_payment_refunded(webhook, tx_details)

    elif event_type == "canceled":
        logger.critical(
            f"TRANSACTION CANCELED: {webhook.transaction_id} -- "
            f"CHECK IF CRYPTO WAS ALREADY RELEASED"
        )
        tx_currency = None
        if tx_details:
            tx_currency = getattr(tx_details, 'currency', None) or (tx_details.get('currency') if isinstance(tx_details, dict) else None)
        if tx_currency == "MXN":
            try:
                from src.fiat.mxn.mxn_handler import _handler_instance as mxn_handler
                if mxn_handler:
                    await mxn_handler.handle_payment_refunded(webhook.transaction_id, "canceled")
            except ImportError:
                pass
        elif on_payment_refunded:
            await on_payment_refunded(webhook, tx_details)

    elif event_type in ("payment_approved", "payment_failed"):
        # Card events — not used for PSE/payout but log for completeness
        logger.info(f"Card event: {event_type} tx={webhook.transaction_id}")

    else:
        logger.warning(f"Unknown webhook type: {event_type}")


def _make_dedup_key(webhook: FPWebhookPayload) -> str:
    """Generate a unique deduplication key for a webhook event."""
    if webhook.transaction_id:
        return f"{webhook.type}:{webhook.transaction_id}"
    elif webhook.exchange_id:
        return f"{webhook.type}:{webhook.exchange_id}"
    elif webhook.wire_id:
        return f"{webhook.type}:{webhook.wire_id}"
    elif webhook.checkout_id:
        return f"{webhook.type}:{webhook.checkout_id}"
    else:
        # Fallback — should not happen in practice
        import hashlib
        raw = json.dumps(webhook.model_dump(), sort_keys=True)
        return f"{webhook.type}:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
