"""
COP Chat Handler (Main Orchestrator)
======================================
Ties together Binance chat, FacilitaPay PSE, info extraction, and order tracking
into a single polling-based automation loop.

Extracted from cop_standalone.py for PearV2.

SAFETY ARCHITECTURE:
1. Per-order asyncio.Lock (M1) — prevents concurrent processing of same order
2. RELEASING state recovery (M2) — reconciliation sweep recovers stuck orders
3. Amount verification — exact COP integer match before release
4. State machine enforcement — VALID_TRANSITIONS prevent invalid transitions
5. Audit log — all actions recorded in immutable SQLite table
6. CC security check — detects cédula reuse across Binance accounts

IRREVERSIBLE ACTIONS:
- release_crypto() — once called, crypto is gone. Protected by 4 guards:
  1. Per-order lock (M1)
  2. State must be in RELEASABLE_STATES
  3. Amount must match exactly
  4. State transitions: PAYMENT_RECEIVED → RELEASING (durable) → release_crypto → COMPLETED (durable)
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from .cop_types import COPOrder, COPOrderState, MESSAGES
from .cop_tracker import COPOrderTracker
from .binance_chat import BinanceChatClient
from .info_extractor import COPInfoExtractor, CustomerInfo

logger = logging.getLogger(__name__)

# Production FacilitaPay client (replaces inline FacilitapayClient)
try:
    from src.fiat.cop import FacilitaPayCopClient, FPDocumentType, FPAccountType
    _HAS_FP_CLIENT = True
except ImportError:
    _HAS_FP_CLIENT = False

# ---- Event-driven FP check queue ----
# When Binance buyer marks a COP order as paid, the orchestrator pushes
# the order ID here so we check FacilitaPay immediately instead of waiting
# for the next 30s poll cycle.
_urgent_checks: asyncio.Queue = asyncio.Queue()
_handler_instance: 'COPChatHandler | None' = None


def request_urgent_fp_check(order_id: str):
    """Called by the orchestrator when Binance detects MARKED_AS_PAID on a COP sell order."""
    try:
        _urgent_checks.put_nowait(order_id)
    except asyncio.QueueFull:
        logger.warning(f"Urgent check queue full — skipping {order_id}")


class COPChatHandler:
    """
    Main COP orchestrator. Ties together:
    - Binance chat (read/send messages)
    - FacilitaPay (PSE payment links)
    - Info extractor (AI-powered customer data parsing)
    - Order tracker (SQLite state machine)

    Usage:
        handler = COPChatHandler(
            binance_api_key="...", binance_api_secret="...",
            facilitapay_username="...", facilitapay_password="...",
            facilitapay_cash_in_account_id="...",
        )
        await handler.start()  # Starts polling loop
    """

    def __init__(
        self,
        binance_api_key: str = "",
        binance_api_secret: str = "",
        binance_2fa_secret: str = "",
        facilitapay_username: str = "",
        facilitapay_password: str = "",
        facilitapay_cash_in_account_id: str = "",
        facilitapay_cashout_account_id: str = "",
        facilitapay_webhook_secret: str = "",
        facilitapay_base_url: str = "https://api.facilitapay.com/api/v1",
        gemini_api_key: str = "",
        poll_interval: float = 30.0,
        db_path: str = "data/cop_orders.db",
        fp_db_path: str = "data/facilitapay.db",
        auto_send_link: bool = True,
    ):
        self.binance = BinanceChatClient(binance_api_key, binance_api_secret)
        self.binance_2fa_secret = binance_2fa_secret

        # Production FacilitaPay client (typed, persistent, with dedup)
        if _HAS_FP_CLIENT:
            self.facilitapay = FacilitaPayCopClient(
                username=facilitapay_username,
                password=facilitapay_password,
                base_url=facilitapay_base_url,
                cashin_account_id=facilitapay_cash_in_account_id,
                cashout_account_id=facilitapay_cashout_account_id,
                webhook_secret=facilitapay_webhook_secret,
                db_path=fp_db_path,
            )
        else:
            self.facilitapay = None
            logger.warning("FacilitaPay client not available — COP handler in limited mode")

        self.extractor = COPInfoExtractor(gemini_api_key)
        self.tracker = COPOrderTracker(db_path)
        self.poll_interval = poll_interval
        self._running = False
        # M1: Per-order async locks — prevents concurrent release race conditions
        self._order_locks: dict[str, asyncio.Lock] = {}
        self.auto_send_link = auto_send_link  # False = queue for manual approval
        self.pending_approvals: list[dict] = []  # links waiting for manual send
        self._error_notified: set[str] = set()   # prevent duplicate error messages
        self._trustpilot_sent: set[str] = set()   # prevent duplicate Trustpilot messages
        self._use_new_client = _HAS_FP_CLIENT

    # ================================================================
    # Polling Loop
    # ================================================================

    async def start(self):
        """Start the polling loop."""
        from src.core.health import task_registry

        global _handler_instance
        _handler_instance = self

        self._running = True
        self._sweep_counter = 0
        self._consecutive_failures = 0
        _MAX_CONSECUTIVE_FAILURES = 10
        logger.info(f"COP Handler started (poll every {self.poll_interval}s)")

        # Start the urgent-check listener as a background task
        asyncio.create_task(self._urgent_check_listener())

        while self._running:
            try:
                await self._poll_cycle()
                # P1-1: Update heartbeat on each successful poll
                task_registry.heartbeat("cop_handler")
                self._consecutive_failures = 0

                # Run reconciliation sweep every ~5 minutes
                self._sweep_counter += 1
                sweep_interval = max(1, int(60 / self.poll_interval))
                if self._sweep_counter >= sweep_interval:
                    self._sweep_counter = 0
                    await self._reconciliation_sweep()
            except Exception as e:
                # P1-2: Track consecutive failures with full traceback
                self._consecutive_failures += 1
                import traceback
                logger.error(
                    "Poll cycle error (%d/%d consecutive failures): %s\n%s",
                    self._consecutive_failures,
                    _MAX_CONSECUTIVE_FAILURES,
                    e,
                    traceback.format_exc(),
                )
                task_registry.mark_error("cop_handler", str(e))
                if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                    logger.critical(
                        "COP handler exceeded %d consecutive failures — re-raising to supervisor",
                        _MAX_CONSECUTIVE_FAILURES,
                    )
                    raise

            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False

    async def _urgent_check_listener(self):
        """Listen for urgent FP check requests from the orchestrator.

        When Binance buyer marks a COP order as paid, the orchestrator pushes
        the order ID here. We wait a few seconds for FP to process the PSE
        payment, then immediately check FP status and trigger release if
        the payment is confirmed — no need to wait for the next 30s poll.
        """
        logger.info("Urgent FP check listener started")
        while self._running:
            try:
                order_id = await asyncio.wait_for(_urgent_checks.get(), timeout=5.0)
                logger.info(f"URGENT FP CHECK: {order_id} — Binance buyer marked paid, checking FP now")

                # Small delay: give FP a moment to process the PSE payment
                await asyncio.sleep(3.0)

                # Acquire per-order lock to avoid racing with the poll cycle
                if order_id not in self._order_locks:
                    self._order_locks[order_id] = asyncio.Lock()

                async with self._order_locks[order_id]:
                    order = self.tracker.get_order(order_id)
                    if not order:
                        logger.debug(f"URGENT: {order_id} not found in tracker — skipping")
                        continue
                    if order.state in (COPOrderState.COMPLETED, COPOrderState.CANCELLED):
                        logger.debug(f"URGENT: {order_id} already terminal ({order.state.value})")
                        continue
                    if order.state == COPOrderState.LINK_SENT:
                        await self._poll_payment_status(order)
                    else:
                        logger.info(f"URGENT: {order_id} in state {order.state.value} — "
                                    "not LINK_SENT, skipping FP check")
            except asyncio.TimeoutError:
                continue  # Normal — just loop and check _running
            except Exception as e:
                logger.error(f"Urgent check listener error: {e}")
                await asyncio.sleep(1.0)
        logger.info("Urgent FP check listener stopped")

    async def _poll_cycle(self):
        """One poll cycle: check active orders, read chat, process."""
        orders = await self.binance.get_active_orders()

        for order_data in orders:
            order_number = order_data.get("orderNumber", "")
            fiat = order_data.get("fiat", "")

            if fiat != "COP":
                continue

            # M1: Per-order async lock — prevents race conditions between
            # concurrent poll cycles and webhook handlers
            if order_number not in self._order_locks:
                self._order_locks[order_number] = asyncio.Lock()

            trade_type = order_data.get("tradeType", "SELL")

            async with self._order_locks[order_number]:
                if trade_type == "BUY":
                    await self._process_buy_order(order_number, order_data)
                else:
                    await self._process_order(order_number, order_data)

    async def _process_order(self, order_number: str, order_data: dict):
        """Process a single COP order (called under per-order lock)."""
        cop_order = self.tracker.get_order(order_number)
        if not cop_order:
            cop_order = self.tracker.create_order(
                binance_order_id=order_number,
                binance_external_id=order_number,
                amount_cop=order_data.get("totalPrice", "0"),
                amount_usdt=order_data.get("amount", "0"),
                binance_buyer_name=order_data.get("counterPartNickName", ""),
            )
            self.tracker.log_audit(order_number, "ORDER_CREATED",
                f"COP={order_data.get('totalPrice')} USDT={order_data.get('amount')}")
            logger.info(f"New COP order: {order_number} - COP {order_data.get('totalPrice')}")

        # Send welcome message once
        if not cop_order.welcome_sent:
            usdt_raw = cop_order.amount_usdt or order_data.get("amount", "")
            try:
                usdt = f"{float(usdt_raw):.2f}" if usdt_raw else ""
            except (ValueError, TypeError):
                usdt = str(usdt_raw)
            sent = await self.binance.send_chat_message(
                order_number, MESSAGES["welcome"].format(usdt=usdt)
            )
            if sent:
                self.tracker.mark_welcome_sent(order_number)
                # Send PSE-only follow-up message
                try:
                    await self.binance.send_chat_message(
                        order_number, MESSAGES["pse_only"]
                    )
                except Exception as e:
                    logger.debug(f"PSE-only follow-up failed for {order_number}: {e}")
            else:
                logger.warning(f"Welcome message failed for {order_number}, will retry next cycle")

        # Skip terminal/active-link states
        if cop_order.state in (COPOrderState.COMPLETED, COPOrderState.RELEASING,
                               COPOrderState.MANUAL_REVIEW, COPOrderState.CANCELLED,
                               COPOrderState.GENERATING_LINK):
            return
        if cop_order.state == COPOrderState.LINK_SENT:
            # ALWAYS poll FacilitaPay for payment status — payment could arrive
            # even after PSE link expiry (customer completed just before expiry)
            await self._poll_payment_status(cop_order)
            # Re-read order: poll may have triggered release → state changed
            cop_order = self.tracker.get_order(order_number)
            if not cop_order or cop_order.state != COPOrderState.LINK_SENT:
                return  # Released or transitioned — done
            if not cop_order.is_link_expired():
                return  # Link still valid, just waiting for payment

        # Read chat — use DB-persisted message IDs for dedup
        messages = await self.binance.get_chat_messages(order_number)
        new_customer_messages = []

        for msg in messages:
            msg_id = str(msg.get("id", ""))
            if not msg_id:
                continue
            # Check DB, not RAM — survives restarts
            if self.tracker.is_message_seen(order_number, msg_id):
                continue
            self.tracker.mark_message_seen(order_number, msg_id)

            is_self = msg.get("self", False)
            content = msg.get("content", "")
            if not is_self and content:
                # Skip Binance system messages (JSON-like notifications)
                stripped = content.strip()
                if stripped.startswith('{') and 'type' in stripped.lower():
                    self.tracker.mark_message_seen(order_number, msg_id)
                    continue
                new_customer_messages.append(content)
                self.tracker.add_message(order_number, content)

        # Process new messages
        if new_customer_messages:
            await self._process_customer_messages(cop_order, new_customer_messages)
        elif cop_order.state == COPOrderState.INFO_RECEIVED and cop_order.customer_cc and cop_order.customer_email and cop_order.bank_code:
            # Recovery: order has complete info but no new messages (e.g. reset from stuck state)
            logger.info(f"Recovery: {order_number} has complete info, generating link directly")
            info = CustomerInfo(
                name=cop_order.customer_name, cc=cop_order.customer_cc,
                email=cop_order.customer_email, bank_code=cop_order.bank_code,
                bank_name=cop_order.bank_name,
            )
            await self._generate_and_send_link(cop_order, info)

    # ================================================================
    # Customer Message Processing
    # ================================================================

    async def _process_customer_messages(self, order: COPOrder, new_messages: list[str]):
        """Process incoming customer messages."""
        # Check for new link request
        if order.state in (COPOrderState.LINK_SENT, COPOrderState.LINK_EXPIRED):
            for msg in new_messages:
                lower = msg.lower()
                if any(kw in lower for kw in ["nuevo enlace", "new link", "otro enlace", "expired", "no funciona"]):
                    await self._regenerate_link(order)
                    return

        # Extract info from ALL messages (including previous ones)
        previous_info = None
        if order.customer_name or order.customer_cc or order.customer_email:
            previous_info = CustomerInfo(
                name=order.customer_name, cc=order.customer_cc,
                email=order.customer_email, bank_code=order.bank_code,
                bank_name=order.bank_name,
            )

        # Refresh order to get all messages
        order = self.tracker.get_order(order.binance_order_id)
        extracted = await self.extractor.extract(order.chat_messages, previous=previous_info)

        # Check completeness
        if not extracted.is_complete():
            missing = extracted.missing_fields()
            # Save partial info — wait silently for customer to send remaining details
            if extracted.name: order.customer_name = extracted.name
            if extracted.cc: order.customer_cc = extracted.cc
            if extracted.email: order.customer_email = extracted.email
            if extracted.bank_code:
                order.bank_code = extracted.bank_code
                order.bank_name = extracted.bank_name
            self.tracker._save(order)
            logger.debug(f"Partial info for {order.binance_order_id}, still missing: {missing}")
            return

        # Security check: CC used by different Binance account?
        prev_name = self.tracker.check_cc_different_account(extracted.cc, order.binance_buyer_name)
        if prev_name:
            logger.warning(f"SECURITY: CC {extracted.cc[:4]}*** used by different account!")
            self.tracker.transition(order.binance_order_id, COPOrderState.MANUAL_REVIEW)
            return

        # Save complete info
        self.tracker.set_customer_info(
            order.binance_order_id,
            name=extracted.name, cc=extracted.cc,
            email=extracted.email, bank_code=extracted.bank_code,
            bank_name=extracted.bank_name,
        )

        # Generate PSE link
        await self._generate_and_send_link(order, extracted)

    # ================================================================
    # PSE Link Generation
    # ================================================================

    async def _generate_and_send_link(self, order: COPOrder, info: CustomerInfo):
        """Generate PSE payment link and send to customer."""
        try:
            # Get or create FacilitaPay subject
            subject_id = self.tracker.get_subject_by_cc(info.cc)
            if not subject_id:
                if self._use_new_client:
                    doc_type = FPDocumentType.CC if (info.cc_type or "cc") == "cc" else FPDocumentType.CE
                    # Sanitize name: strip system messages, JSON, and limit length
                    raw_name = info.name or order.binance_buyer_name or "P2P Customer"
                    # Remove JSON-like fragments and system noise
                    import re as _re
                    raw_name = _re.sub(r'\{[^}]*\}', '', raw_name)
                    raw_name = _re.sub(r'[{}"\[\]]', '', raw_name)
                    # Keep only first 2-3 name parts (first + last + optional middle)
                    name_words = [w for w in raw_name.split() if len(w) > 1 and not w.startswith('{')]
                    social_name = ' '.join(name_words[:4])[:100].strip()
                    if len(social_name) < 3:
                        social_name = order.binance_buyer_name or "P2P Customer"
                    subject = await self.facilitapay.upsert_subject_person(
                        document_number=info.cc,
                        document_type=doc_type,
                        social_name=social_name,
                        email=info.email or "noreply@axion.exchange",
                        phone_area_code="300",
                        phone_number="0000000",
                        address_street="No registrada",
                        address_number="0",
                        address_city="Bogota",
                    )
                    subject_id = subject.id
                else:
                    logger.error("No FacilitaPay client available")
                    return
                self.tracker.cache_subject(info.cc, subject_id, info.name, info.email)

            # Create PSE payment
            self.tracker.transition(order.binance_order_id, COPOrderState.GENERATING_LINK)

            if self._use_new_client:
                from src.fiat.cop.facilitapay_client import FacilitaPayDuplicateError
                try:
                    tx = await self.facilitapay.create_pse_payin(
                        subject_id=subject_id,
                        value_cop=str(order.amount_cop),
                        financial_institution_code=info.bank_code,
                        redirect_url="https://axion.exchange/payment-complete",
                        pear_order_id=order.binance_order_id,
                        payment_description=f"Axion P2P {order.binance_order_id}",
                    )
                    tx_id = tx.id
                    payment_url = tx.from_pse.payment_url if tx.from_pse else None
                except FacilitaPayDuplicateError as e:
                    logger.warning(f"PSE dedup: {e}")
                    return
            else:
                logger.error("No FacilitaPay client available for PSE payment creation")
                return

            if not payment_url:
                logger.error(f"PSE link missing from API response for {order.binance_order_id}")
                return

            # Save link
            self.tracker.set_payment_link(
                order.binance_order_id,
                subject_id=subject_id,
                tx_id=tx_id,
                payment_url=payment_url,
            )

            if self.auto_send_link:
                # AUTO MODE: send link directly to buyer
                await self.binance.send_chat_message(
                    order.binance_order_id,
                    MESSAGES["link_sent"].format(payment_url=payment_url)
                )
                logger.info(f"PSE link sent: {order.binance_order_id}")
            else:
                # MANUAL MODE: queue for dashboard approval
                approval = {
                    "id": str(uuid4())[:8],
                    "order_id": order.binance_order_id,
                    "customer_name": info.name,
                    "customer_cc": info.cc,
                    "customer_email": info.email,
                    "bank_name": info.bank_name or info.bank_code,
                    "amount_cop": order.amount_cop,
                    "amount_usdt": order.amount_usdt,
                    "payment_url": payment_url,
                    "buyer_nickname": order.binance_buyer_name,
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "pending",
                }
                self.pending_approvals.append(approval)
                self.tracker.log_audit(order.binance_order_id, "LINK_QUEUED",
                    f"PSE link queued for manual approval: {payment_url}")
                logger.info(f"PSE link QUEUED (manual mode): {order.binance_order_id} -> dashboard")

        except Exception as e:
            import traceback
            logger.error(f"Error generating link: {e}\n{traceback.format_exc()}")
            # Do NOT message customer about errors — log only
            self.tracker.log_audit(order.binance_order_id, "LINK_ERROR", str(e), "ERROR")

    async def _regenerate_link(self, order: COPOrder):
        """Regenerate expired link."""
        order = self.tracker.get_order(order.binance_order_id)
        if not order or not order.customer_cc:
            return

        info = CustomerInfo(
            name=order.customer_name, cc=order.customer_cc,
            cc_type="cc" if len(order.customer_cc or "") >= 8 else "ce",
            email=order.customer_email, bank_code=order.bank_code,
            bank_name=order.bank_name,
        )
        if info.is_complete():
            await self._generate_and_send_link(order, info)

    # ================================================================
    # Dashboard Approval/Rejection
    # ================================================================

    async def approve_link(self, approval_id: str) -> bool:
        """Manually approve and send a queued PSE link to buyer."""
        for item in self.pending_approvals:
            if item["id"] == approval_id and item["status"] == "pending":
                order_id = item["order_id"]
                payment_url = item["payment_url"]

                await self.binance.send_chat_message(
                    order_id,
                    MESSAGES["link_sent"].format(payment_url=payment_url)
                )
                item["status"] = "approved"
                self.tracker.log_audit(order_id, "LINK_APPROVED",
                    f"Manually approved and sent: {payment_url}")
                logger.info(f"APPROVED: Link sent for order {order_id}")
                return True
        return False

    async def reject_link(self, approval_id: str, reason: str = "") -> bool:
        """Reject a queued PSE link."""
        for item in self.pending_approvals:
            if item["id"] == approval_id and item["status"] == "pending":
                item["status"] = "rejected"
                item["reject_reason"] = reason
                self.tracker.log_audit(item["order_id"], "LINK_REJECTED",
                    f"Manually rejected: {reason}")
                logger.info(f"REJECTED: Link for order {item['order_id']} — {reason}")
                return True
        return False

    # ================================================================
    # Payment Status Polling (fallback when webhooks not configured)
    # ================================================================

    async def _poll_payment_status(self, order):
        """Poll FacilitaPay API for payment status on LINK_SENT orders.
        
        This is the critical fallback when FACILITAPAY_WEBHOOK_SECRET is not set.
        Checks FP transaction status and triggers release if payment is confirmed.
        """
        if not self._use_new_client:
            return

        order_id = order.binance_order_id

        # Look up FP transaction for this order from local DB
        try:
            tx_row = self.facilitapay.db.get_transaction_by_order(order_id, "payin")
        except Exception as e:
            logger.warning(f"Payment poll DB error for {order_id}: {e}")
            return

        if not tx_row:
            return  # No FP transaction yet

        tx_id = tx_row["id"]
        local_status = tx_row["status"]

        # If payment was already identified, check if order actually completed.
        # BUG FIX: Previously this returned unconditionally, causing orders to
        # get stuck in LINK_SENT if the initial release attempt failed —
        # subsequent polls would see "identified" in local DB and skip retry.
        if local_status in ("identified", "approved", "settled"):
            order_obj = self.tracker.get_order(order_id)
            if order_obj and order_obj.state in (COPOrderState.COMPLETED, COPOrderState.CANCELLED):
                return  # Truly done — no action needed
            # Payment confirmed but release didn't complete — retry
            logger.warning(f"POLL RETRY: {order_id} has FP status '{local_status}' but order state is "
                           f"'{order_obj.state.value if order_obj else 'UNKNOWN'}' — retrying release")
            self.tracker.log_audit(order_id, "POLL_RETRY_RELEASE",
                f"FP status={local_status} but order not completed — retrying webhook flow")
            # NOTE: We are already inside _order_locks[order_id] via _poll_cycle → _process_order.
            # Calling handle_webhook() would deadlock (asyncio.Lock is NOT reentrant).
            # Call _handle_webhook_locked() directly instead.
            order_obj_for_webhook = self.tracker.get_order(order_id) or order_obj
            try:
                await asyncio.wait_for(
                    self._handle_webhook_locked(tx_id, "identified", order_obj_for_webhook),
                    timeout=30
                )
            except asyncio.TimeoutError:
                logger.error(f"POLL RETRY TIMEOUT: _handle_webhook_locked hung for {order_id} — skipping")
            return

        try:
            result = await self.facilitapay.get_transaction_status(tx_id)
            fp_status = result.get("status", "unknown")

            if fp_status in ("identified", "approved", "settled"):
                logger.warning(f"POLL RECOVERY: Payment detected for {order_id} (status={fp_status})")
                self.tracker.log_audit(order_id, "POLL_PAYMENT_DETECTED",
                    f"FP tx {tx_id[:8]}... status={fp_status} — triggering release")
                # Update local status
                self.facilitapay.db.update_transaction_status(tx_id, fp_status)
                # Trigger the release flow
                # NOTE: Already inside _order_locks[order_id] — call locked version directly.
                order_obj_for_recovery = self.tracker.get_order(order_id)
                if order_obj_for_recovery:
                    try:
                        await asyncio.wait_for(
                            self._handle_webhook_locked(tx_id, "identified", order_obj_for_recovery),
                            timeout=30
                        )
                    except asyncio.TimeoutError:
                        logger.error(f"POLL RECOVERY TIMEOUT: _handle_webhook_locked hung for {order_id} — skipping")
            elif fp_status == "expired":
                self.facilitapay.db.update_transaction_status(tx_id, "expired")
                self.tracker.log_audit(order_id, "PSE_LINK_EXPIRED",
                    f"PSE link expired (polling) — tx {tx_id[:8]}...")
                self.tracker.transition(order_id, COPOrderState.INFO_RECEIVED)
                logger.info(f"PSE link expired for {order_id} — reset to INFO_RECEIVED for retry")
        except Exception as e:
            logger.warning(f"Payment poll error for {order_id}: {e}")

    # ================================================================
    # Webhook Handler (M1: per-order lock)
    # ================================================================

    async def handle_webhook(self, transaction_id: str, event_type: str) -> bool:
        """
        Handle FacilitaPay webhook with full safety checks.

        PROTECTIONS:
        1. Per-order lock: prevents concurrent release race (M1)
        2. State guard: only release from valid states
        3. Idempotency: skip if already COMPLETED/RELEASING
        4. Amount verification: call FacilitaPay API and compare amounts
        5. Audit logging: every attempt is logged

        SAFETY: This is the entry point for ALL webhook processing.
        It acquires a per-order lock before delegating to _handle_webhook_locked.
        """
        order = self.tracker.get_order_by_tx_id(transaction_id)
        if not order:
            logger.warning(f"WEBHOOK IGNORED: No order found for tx {transaction_id}")
            self.tracker.log_audit("UNKNOWN", "WEBHOOK_NO_ORDER",
                f"tx_id={transaction_id} event={event_type}", "IGNORED")
            return False

        # M1: Per-order lock — prevents concurrent webhook / reconciliation race
        order_id = order.binance_order_id
        if order_id not in self._order_locks:
            self._order_locks[order_id] = asyncio.Lock()

        lock = self._order_locks[order_id]
        if lock.locked():
            logger.warning(f"WEBHOOK LOCK BUSY: {order_id} — skipping (another coroutine holds lock)")
            return False

        logger.info(f"WEBHOOK LOCK: acquiring for {order_id}")
        async with lock:
            logger.info(f"WEBHOOK LOCK: acquired for {order_id}")
            return await self._handle_webhook_locked(transaction_id, event_type, order)

    async def _handle_webhook_locked(self, transaction_id: str, event_type: str, order) -> bool:
        """
        Internal webhook handler — MUST be called under per-order lock.

        CRITICAL PATH: This method controls whether crypto is released.
        Every guard here protects against a specific money-loss scenario.
        """
        order_id = order.binance_order_id
        # Re-read order under lock to get freshest state (prevents TOCTOU race)
        order = self.tracker.get_order(order_id) or order
        self.tracker.log_audit(order_id, "WEBHOOK_RECEIVED",
            f"tx_id={transaction_id} event={event_type} current_state={order.state.value}")

        if event_type != "identified":
            return True  # Non-payment events are fine

        # --- GUARD 1: Idempotency — already released? ---
        # Prevents double release from duplicate webhooks
        if order.state in (COPOrderState.COMPLETED, COPOrderState.RELEASING):
            self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                f"Already in {order.state.value} — duplicate webhook", "SKIPPED")
            logger.info(f"DUPLICATE WEBHOOK: Order {order_id} already {order.state.value}")
            return True  # Not an error, just already done

        # --- GUARD 2: State check — only release from expected states ---
        # Prevents release from wrong states (e.g., CANCELLED, MANUAL_REVIEW)
        RELEASABLE_STATES = {
            COPOrderState.LINK_SENT,
            COPOrderState.AWAITING_PAYMENT,
            COPOrderState.PAYMENT_RECEIVED,
        }
        if order.state not in RELEASABLE_STATES:
            self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                f"Order in {order.state.value}, not in releasable states", "REJECTED")
            logger.warning(f"SECURITY: Cannot release order {order_id} in state {order.state.value}")
            return False

        # --- GUARD 3: Currency-aware amount verification ---
        # Prevents releasing crypto for wrong/partial payment amount
        logger.info(f"WEBHOOK STEP 1: {order_id} — verifying FP tx {transaction_id[:12]}...")
        try:
            if self._use_new_client:
                tx = await self.facilitapay.get_transaction(transaction_id)
                tx_status = tx.status.value

                if tx.currency == "COP":
                    tx_amount_cop = tx.value
                elif getattr(tx, 'exchange_currency', None) == "COP" and getattr(tx, 'exchanged_value', None):
                    tx_amount_cop = tx.exchanged_value
                else:
                    # Can't determine COP amount — fail safe (do NOT release)
                    self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                        f"Cannot determine COP amount: currency={tx.currency} "
                        f"exchange_currency={getattr(tx, 'exchange_currency', None)}",
                        "NEEDS_REVIEW")
                    self.tracker.transition(order_id, COPOrderState.MANUAL_REVIEW)
                    logger.error(f"SECURITY: Cannot determine COP amount for {order_id} — MANUAL_REVIEW")
                    return False
            else:
                logger.error("No FacilitaPay client for tx verification")
                return False
        except Exception as e:
            self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                f"Failed to verify transaction: {e}", "REJECTED")
            logger.error(f"SECURITY: Cannot verify tx {transaction_id} — NOT releasing")
            return False

        expected_cop = str(order.amount_cop or "0")

        # Compare COP amounts — allow <=1 COP difference for rounding
        # PSE only accepts integer COP amounts, so 261698.39 → 261698 is expected.
        # SAFETY: We use Decimal→int to avoid floating-point precision issues.
        # Difference > 1 COP → MANUAL_REVIEW (fail-safe)
        try:
            paid_int = int(Decimal(str(tx_amount_cop)).to_integral_value())
            expected_int = int(Decimal(str(expected_cop)).to_integral_value())
            diff = abs(paid_int - expected_int)
            if diff > 1:
                self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                    f"Amount mismatch: paid={paid_int} COP expected={expected_int} COP (diff={diff})",
                    "REJECTED")
                self.tracker.transition(order_id, COPOrderState.MANUAL_REVIEW)
                logger.error(f"SECURITY: Amount mismatch on {order_id}! Paid={paid_int} Expected={expected_int} Diff={diff}")
                return False
            elif diff > 0:
                logger.info(f"COP rounding accepted for {order_id}: paid={paid_int} expected={expected_int} (diff={diff})")
        except Exception as e:
            self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                f"Amount comparison error: {e}", "REJECTED")
            return False

        # --- ALL CHECKS PASSED — Release ---
        # Pattern: durable write → side effect → durable write
        # Step 1: Record payment verification (durable)
        self.tracker.transition(order_id, COPOrderState.PAYMENT_RECEIVED)
        self.tracker.log_audit(order_id, "PAYMENT_VERIFIED",
            f"amount={tx_amount_cop} status={tx_status}")

        logger.info(f"Payment verified for {order_id}: {order.amount_usdt} USDT")

        logger.info(f"WEBHOOK STEP 2: {order_id} — transitioning to RELEASING")

        # Step 2: Transition to RELEASING (durable) BEFORE calling release_crypto
        # If we crash here, M2 recovery will find the order in RELEASING and retry
        self.tracker.transition(order_id, COPOrderState.RELEASING)
        self.tracker.log_audit(order_id, "RELEASE_ATTEMPT",
            f"amount_usdt={order.amount_usdt}")

        # P0-2: DB release guard — atomic at-most-once claim BEFORE Binance call.
        # If another path already claimed this release, we must NOT call Binance.
        if not self.tracker.try_claim_release(order_id):
            self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                "DB guard: release already claimed by another path", "SKIPPED")
            logger.warning(f"RELEASE GUARD: {order_id} already claimed — verifying Binance status instead")
            # Verify on Binance instead of re-releasing
            try:
                bdetail = await self.binance.get_order_detail(order_id)
                if bdetail and str(bdetail.get("orderStatus", "")) in ("5", "COMPLETED"):
                    self.tracker.transition(order_id, COPOrderState.COMPLETED)
                    self.tracker.log_audit(order_id, "RELEASE_VERIFIED",
                        "Binance confirms COMPLETED (guarded duplicate)")
                    return True
            except Exception:
                pass
            # Cannot confirm — escalate
            self.tracker.transition(order_id, COPOrderState.MANUAL_REVIEW)
            return False

        # Step 3: Send thank-you message BEFORE release so buyer sees it
        logger.info(f"WEBHOOK STEP 3: {order_id} — sending thank-you chat")
        try:
            thank_you_msg = (
                "\U0001f389 ¡Transacción completada! Gracias por operar con nosotros.\n"
                "Ayuda a otros traders a encontrarnos — déjanos una reseña rápida:\n"
                "⭐ https://trustpilot.com/review/axionexchange.io\n"
                "¡Tu apoyo significa mucho! \U0001f499"
            )
            await self.binance.send_chat_message(order_id, thank_you_msg)
            logger.info(f"Sent thank-you message for COP order {order_id}")
        except Exception as e:
            logger.warning(f"Failed to send thank-you for COP {order_id}: {e}")

        # GUARD: Verify order still exists on Binance before release.
        # If Binance returns 404, the order was already released externally.
        # Attempting release on a 404 order hangs indefinitely.
        logger.info(f"WEBHOOK STEP 4: {order_id} — Binance liveness check")
        try:
            bdetail = await self.binance.get_order_detail(order_id)
        except Exception:
            bdetail = None
        if not bdetail:
            logger.warning(f"RELEASE SKIP: {order_id} not found on Binance (404) — marking COMPLETED")
            self.tracker.transition(order_id, COPOrderState.COMPLETED)
            self.tracker.log_audit(order_id, "RELEASE_SKIP_404",
                "Binance 404 — order already released externally")
            self.tracker.mark_release_result(order_id, True)
            return True
        # If Binance already shows COMPLETED, skip release
        b_status = str(bdetail.get("orderStatus", ""))
        if b_status in ("5", "COMPLETED"):
            logger.info(f"RELEASE SKIP: {order_id} already COMPLETED on Binance")
            self.tracker.transition(order_id, COPOrderState.COMPLETED)
            self.tracker.log_audit(order_id, "RELEASE_ALREADY_DONE",
                "Binance shows COMPLETED — no release needed")
            self.tracker.mark_release_result(order_id, True)
            return True

        # Step 4: Irreversible action — release crypto
        success = await self.binance.release_crypto(order_id, self.binance_2fa_secret)

        # P0-2: Record release outcome in guard table
        self.tracker.mark_release_result(order_id, success)

        # Step 4: Record outcome (durable)
        if success:
            self.tracker.transition(order_id, COPOrderState.COMPLETED)
            self.tracker.log_audit(order_id, "RELEASE_SUCCESS",
                f"Released {order.amount_usdt} USDT", "OK")
            logger.info(f"Crypto released for {order_id}: {order.amount_usdt} USDT")
        else:
            # Release failed — escalate to manual review
            self.tracker.log_audit(order_id, "RELEASE_FAILED",
                f"Binance API rejected release", "FAILED")
            self.tracker.transition(order_id, COPOrderState.MANUAL_REVIEW)

        return success

    # ================================================================
    # Reconciliation Sweep (M2: RELEASING recovery)
    # ================================================================

    async def _reconciliation_sweep(self):
        """
        Reconciliation sweep — catches stuck orders from:
        - Webhook failures (missed payment notifications)
        - Expired PSE links
        - Crash-before-release scenarios (M2)
        - Stuck GENERATING_LINK states

        Runs every ~5 minutes from the polling loop.
        """
        # AUDIT FIX: Prune per-order locks for terminal orders to prevent memory leak.
        # _order_locks dict grew unboundedly — locks for completed/cancelled orders
        # were never cleaned up. We prune here rather than at each of the 13+
        # transition sites for simplicity and safety.
        terminal_cop_states = {COPOrderState.COMPLETED, COPOrderState.CANCELLED}
        stale_lock_ids = []
        for oid in list(self._order_locks.keys()):
            order = self.tracker.get_order(oid)
            if order and order.state in terminal_cop_states:
                stale_lock_ids.append(oid)
            elif not order:
                stale_lock_ids.append(oid)  # Order no longer tracked
        for oid in stale_lock_ids:
            self._order_locks.pop(oid, None)
        if stale_lock_ids:
            logger.debug("Pruned %d stale order locks", len(stale_lock_ids))

        if not self._use_new_client:
            return  # Only works with typed client (needs FP persistence)

        now = datetime.utcnow()

        try:
            # 1. Orders with expired PSE links — check if payment arrived via polling
            expired_txs = self.facilitapay.db.get_expired_pse_links(minutes=25)
            for tx in expired_txs:
                pear_order_id = tx.get("pear_order_id")
                if not pear_order_id:
                    continue
                order = self.tracker.get_order(pear_order_id)
                if order and order.state == COPOrderState.LINK_SENT:
                    try:
                        fp_tx = await self.facilitapay.get_transaction(tx["id"])
                        if fp_tx.status.value == "identified":
                            # Payment arrived but webhook was missed!
                            logger.warning(f"RECOVERY: Payment found for {pear_order_id} via polling")
                            self.tracker.log_audit(pear_order_id, "RECOVERY_POLL",
                                f"Missed webhook recovered — tx {tx['id'][:8]}... is identified")
                            await self.handle_webhook(tx["id"], "identified")
                        elif fp_tx.status.value == "pending":
                            # Link expired, no payment — update local status
                            self.facilitapay.db.update_transaction_status(tx["id"], "expired")
                            self.tracker.log_audit(pear_order_id, "PSE_LINK_EXPIRED",
                                f"PSE link expired after 25 min — tx {tx['id'][:8]}...")
                            logger.info(f"PSE link expired: {pear_order_id}")
                    except Exception as e:
                        logger.error(f"Recovery poll failed for tx {tx['id'][:8]}...: {e}")

            # 2. Orders in PAYMENT_RECEIVED for > 5 minutes — retry release
            stuck_orders = self.tracker.get_orders_by_state(COPOrderState.PAYMENT_RECEIVED)
            for order in stuck_orders:
                if order.created_at and (now - order.created_at) > timedelta(minutes=5):
                    self.tracker.log_audit(order.binance_order_id, "RECOVERY_RETRY",
                        "Order stuck in PAYMENT_RECEIVED > 5 min — retrying release")
                    logger.warning(f"RECOVERY: Retrying release for {order.binance_order_id}")
                    if order.facilitapay_tx_id:
                        await self.handle_webhook(order.facilitapay_tx_id, "identified")

            # M2: Orders stuck in RELEASING for > 2 minutes — check Binance for actual status
            # SAFETY: This handles the case where release_crypto() succeeded but the process
            # crashed before we could transition to COMPLETED. Without this recovery, the order
            # stays stuck in RELEASING forever (funds released but system doesn't know).
            stuck_releasing = self.tracker.get_orders_by_state(COPOrderState.RELEASING)
            for order in stuck_releasing:
                if order.created_at and (now - order.created_at) > timedelta(minutes=2):
                    oid = order.binance_order_id
                    self.tracker.log_audit(oid, "RECOVERY_RELEASING",
                        "Order stuck in RELEASING > 2 min — checking Binance")
                    try:
                        bdetail = await self.binance.get_order_detail(oid)
                        if bdetail:
                            b_status = str(bdetail.get("orderStatus", ""))
                            if b_status in ("5", "COMPLETED"):
                                # Release went through — finalize
                                self.tracker.transition(oid, COPOrderState.COMPLETED)
                                self.tracker.log_audit(oid, "RECOVERY_COMPLETED",
                                    f"Binance shows COMPLETED — finalising locally")
                                logger.info(f"RECOVERY: {oid} completed on Binance — marking COMPLETED")
                            elif b_status in ("4", "CANCELLED"):
                                self.tracker.transition(oid, COPOrderState.CANCELLED)
                                self.tracker.log_audit(oid, "RECOVERY_CANCELLED",
                                    f"Binance shows CANCELLED — marking CANCELLED")
                                logger.info(f"RECOVERY: {oid} cancelled on Binance")
                            else:
                                # Still active on Binance — retry only if not already claimed
                                # P0-2: Check DB guard before retrying release
                                if not self.tracker.try_claim_release(oid):
                                    self.tracker.log_audit(oid, "RECOVERY_BLOCKED",
                                        "DB guard: release already claimed — escalating to MANUAL_REVIEW")
                                    self.tracker.transition(oid, COPOrderState.MANUAL_REVIEW)
                                else:
                                    logger.warning(f"RECOVERY: {oid} still active on Binance (status={b_status}) — retrying release")
                                    success = await self.binance.release_crypto(oid, self.binance_2fa_secret)
                                    self.tracker.mark_release_result(oid, success)
                                    if success:
                                        self.tracker.transition(oid, COPOrderState.COMPLETED)
                                        self.tracker.log_audit(oid, "RECOVERY_RELEASED",
                                            "Release retried successfully")
                                    else:
                                        self.tracker.transition(oid, COPOrderState.MANUAL_REVIEW)
                                        self.tracker.log_audit(oid, "RECOVERY_FAILED",
                                            "Release retry failed — escalated to MANUAL_REVIEW")
                        else:
                            self.tracker.log_audit(oid, "RECOVERY_ERROR",
                                "Cannot fetch order from Binance — skipping")
                    except Exception as e:
                        logger.error(f"RECOVERY error for {oid}: {e}")

            # 3. Orders in GENERATING_LINK for > 10 minutes — stuck, escalate
            stuck_generating = self.tracker.get_orders_by_state(COPOrderState.GENERATING_LINK)
            for order in stuck_generating:
                if order.created_at and (now - order.created_at) > timedelta(minutes=10):
                    self.tracker.transition(order.binance_order_id, COPOrderState.MANUAL_REVIEW)
                    self.tracker.log_audit(order.binance_order_id, "RECOVERY_ESCALATE",
                        "Stuck in GENERATING_LINK > 10 min — escalated to MANUAL_REVIEW")
                    logger.warning(f"RECOVERY: Escalated {order.binance_order_id} to MANUAL_REVIEW")

            # 4. Detect manual releases — orders the operator released directly on Binance.
            #    These never go through _handle_webhook_locked, so the Trustpilot message
            #    is never sent. Check non-terminal orders against Binance status.
            MANUAL_RELEASE_STATES = {
                COPOrderState.LINK_SENT,
                COPOrderState.AWAITING_PAYMENT,
                COPOrderState.PAYMENT_RECEIVED,
                COPOrderState.MANUAL_REVIEW,
                COPOrderState.RELEASING,
            }
            for state in MANUAL_RELEASE_STATES:
                orders_in_state = self.tracker.get_orders_by_state(state)
                if orders_in_state:
                    logger.info(f"SWEEP: Checking {len(orders_in_state)} orders in {state.value}")
                for order in orders_in_state:
                    oid = order.binance_order_id
                    try:
                        bdetail = await self.binance.get_order_detail(oid)
                        if not bdetail:
                            logger.info(f"SWEEP 404: {oid} (was {state.value}) — Binance returned None")
                            # Binance 404 — order no longer exists in their API.
                            # Check LIVE FP API status (local DB may be stale).
                            try:
                                fp_row = self.facilitapay.db.get_transaction_by_order(oid, "payin")
                                if not fp_row:
                                    logger.debug(f"Binance 404 for {oid}, no FP transaction — skipping")
                                else:
                                    tx_id = fp_row["id"]
                                    local_status = fp_row["status"]
                                    # Query live FP API for the real status
                                    try:
                                        fp_result = await self.facilitapay.get_transaction_status(tx_id)
                                        fp_status = fp_result.get("status", local_status)
                                    except Exception:
                                        fp_status = local_status  # Fallback to local if API fails
                                    # Update local DB if different
                                    if fp_status != local_status:
                                        self.facilitapay.db.update_transaction_status(tx_id, fp_status)
                                    if fp_status in ("identified", "approved", "settled"):
                                        logger.info(f"STALE ORDER CLEANUP: {oid} (was {state.value}) — "
                                                    f"Binance 404 but FP shows {fp_status}, marking COMPLETED")
                                        self.tracker.log_audit(oid, "STALE_ORDER_COMPLETED",
                                            f"Binance 404, FP live status={fp_status} — marking completed")
                                        self.tracker.transition(oid, COPOrderState.COMPLETED)
                                    elif fp_status in ("canceled", "expired"):
                                        logger.info(f"STALE ORDER CLEANUP: {oid} (was {state.value}) — "
                                                    f"Binance 404, FP shows {fp_status}, marking CANCELLED")
                                        self.tracker.transition(oid, COPOrderState.CANCELLED)
                                        self.tracker.log_audit(oid, "STALE_ORDER_CANCELLED",
                                            f"Binance 404, FP live status={fp_status}")
                                    else:
                                        logger.debug(f"Binance 404 for {oid}, FP live status={fp_status} — skipping")
                            except Exception as db_err:
                                logger.warning(f"FP lookup failed for {oid}: {db_err}")
                            continue
                        b_status = str(bdetail.get("orderStatus", ""))
                        if b_status in ("5", "COMPLETED"):
                            # Order was released (manually or otherwise) but bot didn't process it
                            logger.info(f"MANUAL RELEASE DETECTED: {oid} (was {state.value})")
                            self.tracker.log_audit(oid, "MANUAL_RELEASE_DETECTED",
                                f"Binance shows COMPLETED but tracker had {state.value}")
                            # Send Trustpilot thank-you message (with dedup guard)
                            if oid not in self._trustpilot_sent:
                                try:
                                    thank_you_msg = (
                                        "\U0001f389 ¡Transacción completada! Gracias por operar con nosotros.\n"
                                        "Ayuda a otros traders a encontrarnos — déjanos una reseña rápida:\n"
                                        "⭐ https://trustpilot.com/review/axionexchange.io\n"
                                        "¡Tu apoyo significa mucho! \U0001f499"
                                    )
                                    await self.binance.send_chat_message(oid, thank_you_msg)
                                    self._trustpilot_sent.add(oid)
                                    logger.info(f"Sent Trustpilot message for manually released {oid}")
                                except Exception as e:
                                    logger.warning(f"Failed to send Trustpilot for {oid}: {e}")
                            self.tracker.transition(oid, COPOrderState.COMPLETED)
                            self.tracker.log_audit(oid, "MANUAL_RELEASE_COMPLETED",
                                "Marked COMPLETED + Trustpilot sent after manual release detection")
                        elif b_status in ("4", "CANCELLED"):
                            self.tracker.transition(oid, COPOrderState.CANCELLED)
                            self.tracker.log_audit(oid, "ORDER_CANCELLED_BINANCE",
                                f"Binance shows CANCELLED — was {state.value}")
                    except Exception as e:
                        logger.warning(f"Manual release check error for {oid}: {e}")

        except Exception as e:
            logger.error(f"Reconciliation sweep error: {e}")

    # ================================================================
    # Payment Expiry/Refund Handlers
    # ================================================================

    async def handle_payment_expired(self, transaction_id: str):
        """Handle PSE payment link expiry webhook."""
        if not self._use_new_client:
            return

        tx_data = self.facilitapay.db.get_transaction(transaction_id)
        if not tx_data:
            logger.warning(f"Expired webhook for unknown tx: {transaction_id[:8]}...")
            return
        order_id = tx_data.get("pear_order_id")
        if not order_id:
            return

        order = self.tracker.get_order(order_id)
        if not order:
            return

        self.facilitapay.db.update_transaction_status(transaction_id, "expired")

        if order.state in (COPOrderState.LINK_SENT, COPOrderState.AWAITING_PAYMENT):
            self.tracker.log_audit(order_id, "PSE_LINK_EXPIRED",
                f"PSE payment link expired (webhook) — tx {transaction_id[:8]}...")
            self.tracker.transition(order_id, COPOrderState.AWAITING_INFO)
            logger.info(f"PSE link expired for {order_id} — will regenerate")
            logger.info(f"PSE link expired for {order_id} — reset to AWAITING_INFO")

    async def handle_payment_refunded(self, transaction_id: str, event_type: str):
        """
        Handle payment refund/cancellation webhook.
        CRITICAL: If crypto was already released, this is a fund loss event.
        """
        if not self._use_new_client:
            return

        tx_data = self.facilitapay.db.get_transaction(transaction_id)
        if not tx_data:
            logger.warning(f"Refund webhook for unknown tx: {transaction_id[:8]}...")
            return
        order_id = tx_data.get("pear_order_id")
        if not order_id:
            return

        order = self.tracker.get_order(order_id)
        if not order:
            return

        self.facilitapay.db.update_transaction_status(transaction_id, event_type)

        # CRITICAL: Check if crypto was already released
        if order.state in (COPOrderState.COMPLETED, COPOrderState.RELEASING):
            self.tracker.log_audit(order_id, "FUNDS_AT_RISK",
                f"🚨 CRITICAL: {event_type} received AFTER crypto release — "
                f"tx {transaction_id[:8]}... — MANUAL RECOVERY REQUIRED",
                "CRITICAL")
            logger.critical(f"🚨 FUNDS AT RISK: {order_id} — {event_type} after release!")
        else:
            self.tracker.log_audit(order_id, "PAYMENT_CANCELLED",
                f"{event_type} received — tx {transaction_id[:8]}...",
                "WARNING")

        self.tracker.transition(order_id, COPOrderState.MANUAL_REVIEW)
        logger.warning(f"Payment refunded/cancelled for {order_id} — MANUAL_REVIEW")
        logger.warning(f"Payment {event_type} for {order_id} — moved to MANUAL_REVIEW")

    # ================================================================
    # Cleanup
    # ================================================================

    async def close(self):
        await self.binance.close()
        if self._use_new_client and self.facilitapay:
            await self.facilitapay.close()
        await self.extractor.close()

    # ================================================================
    # COP BUY Flow (we buy USDT, pay COP to seller)
    # ================================================================

    async def _process_buy_order(self, order_number: str, order_data: dict):
        """Process a COP BUY order (we pay COP, receive USDT).

        Called under per-order lock.
        """
        cop_order = self.tracker.get_order(order_number)
        if not cop_order:
            cop_order = self.tracker.create_order(
                binance_order_id=order_number,
                binance_external_id=order_number,
                amount_cop=order_data.get("totalPrice", "0"),
                amount_usdt=order_data.get("amount", "0"),
                binance_buyer_name=order_data.get("counterPartNickName", ""),
                order_side="BUY",
            )
            self.tracker.log_audit(order_number, "BUY_ORDER_CREATED",
                f"COP={order_data.get('totalPrice')} USDT={order_data.get('amount')} "
                f"seller={order_data.get('counterPartNickName', '')}")
            logger.info(f"New COP BUY order: {order_number} - COP {order_data.get('totalPrice')}")

        # Send welcome message once
        if not cop_order.welcome_sent:
            try:
                await self.binance.send_chat_message(
                    order_number,
                    MESSAGES["buy_welcome"],
                )
                self.tracker.mark_welcome_sent(order_number)
                logger.info(f"BUY welcome sent: {order_number}")
            except Exception as e:
                logger.warning(f"Failed to send BUY welcome for {order_number}: {e}")

        # Re-read order (welcome_sent may have been updated)
        cop_order = self.tracker.get_order(order_number)
        if not cop_order:
            return

        # Terminal states — nothing to do
        if cop_order.state in (COPOrderState.COMPLETED, COPOrderState.CANCELLED,
                               COPOrderState.MANUAL_REVIEW):
            logger.info(f"BUY {order_number[-8:]}: terminal state {cop_order.state.value}, skipping")
            return

        # If payout already sent, run mark_paid reconciliation
        if cop_order.state in (COPOrderState.PAYOUT_SENT, COPOrderState.MARK_PAID_PENDING):
            await self._reconcile_buy_mark_paid(cop_order)
            return

        # If payout pending (info collected but payout not yet executed), execute it
        if cop_order.state == COPOrderState.PAYOUT_PENDING:
            await self._execute_cop_buy_payout(cop_order)
            return

        # Collect bank info from chat
        if cop_order.state == COPOrderState.COLLECTING_BANK_INFO:
            logger.info(f"BUY {order_number[-8:]}: reading chat for bank info")
            try:
                messages = await self.binance.get_chat_messages(order_number)
            except Exception as e:
                logger.error(f"Failed to get chat for BUY {order_number}: {e}")
                return

            # F1-FIX: Use sender field + message ID dedup (mirrors SELL side)
            new_customer_messages = []
            for msg in messages:
                msg_id = str(msg.get("id", ""))
                if not msg_id:
                    continue
                # DB-persisted dedup — survives restarts
                if self.tracker.is_message_seen(order_number, msg_id):
                    continue
                self.tracker.mark_message_seen(order_number, msg_id)

                is_self = msg.get("self", False)
                content = msg.get("content", "")
                if not is_self and content:
                    # Skip Binance system messages (JSON-like notifications)
                    stripped = content.strip()
                    if stripped.startswith('{') and 'type' in stripped.lower():
                        continue
                    new_customer_messages.append(content)
                    self.tracker.add_message(order_number, content)

            # Process if new customer messages found
            if new_customer_messages:
                cop_order = self.tracker.get_order(order_number)
                logger.info(f"BUY chat: {len(new_customer_messages)} new messages for {order_number}")
                await self._process_buy_messages(cop_order, cop_order.chat_messages)

    async def _process_buy_messages(self, order: COPOrder, all_messages: list[str]):
        """Extract seller's bank details from chat messages."""
        # Build previous info from saved order data
        previous_info = None
        if order.customer_name or order.customer_cc or order.bank_code:
            previous_info = CustomerInfo(
                name=order.customer_name, cc=order.customer_cc,
                email=order.customer_email, bank_code=order.bank_code,
                bank_name=order.bank_name,
                account_number=order.seller_account_number,
                account_type=order.seller_account_type,
            )

        extracted = await self.extractor.extract(all_messages, previous=previous_info,
                                                   force_regex=True)

        if not extracted.is_complete_for_buy():
            missing = extracted.missing_buy_fields()
            # Save partial info
            if extracted.name or extracted.cc or extracted.bank_code:
                order_fresh = self.tracker.get_order(order.binance_order_id)
                if order_fresh:
                    if extracted.name: order_fresh.customer_name = extracted.name
                    if extracted.cc: order_fresh.customer_cc = extracted.cc
                    if extracted.email: order_fresh.customer_email = extracted.email
                    if extracted.bank_code:
                        order_fresh.bank_code = extracted.bank_code
                        order_fresh.bank_name = extracted.bank_name
                    if extracted.account_number:
                        order_fresh.seller_account_number = extracted.account_number
                    if extracted.account_type:
                        order_fresh.seller_account_type = extracted.account_type
                    self.tracker._save(order_fresh)
            logger.info(f"BUY partial info for {order.binance_order_id}, missing: {missing}")
            return

        # Security check: CC used by different Binance account?
        prev_name = self.tracker.check_cc_different_account(extracted.cc, order.binance_buyer_name)
        if prev_name:
            logger.warning(f"BUY SECURITY: CC {extracted.cc[:4]}*** used by different account!")
            self.tracker.transition(order.binance_order_id, COPOrderState.MANUAL_REVIEW)
            return

        # Validate CC
        from .info_extractor import validate_colombian_cc
        valid, normalized, result = validate_colombian_cc(extracted.cc)
        if not valid:
            await self.binance.send_chat_message(
                order.binance_order_id,
                f"[!] La cédula ingresada no es válida: {result}. Por favor verifica el número.",
            )
            return

        # F3-FIX: Respect extracted account type; default to checking
        acct_type = extracted.account_type or "checking"

        # Save complete info and transition to PAYOUT_PENDING
        self.tracker.set_buy_customer_info(
            order.binance_order_id,
            name=extracted.name, cc=normalized,
            email=extracted.email or "noreply@axion.exchange",
            bank_code=extracted.bank_code,
            bank_name=extracted.bank_name,
            account_number=extracted.account_number,
            account_type=acct_type,
        )
        self.tracker.transition(order.binance_order_id, COPOrderState.PAYOUT_PENDING)
        self.tracker.log_audit(order.binance_order_id, "BUY_INFO_COMPLETE",
            f"name={extracted.name} cc={normalized[:4]}*** bank={extracted.bank_code} "
            f"acct=***{extracted.account_number[-4:] if extracted.account_number else '?'} "
            f"type={acct_type}")

        # Auto-execute payout
        order = self.tracker.get_order(order.binance_order_id)
        if order:
            await self._execute_cop_buy_payout(order)

    async def _execute_cop_buy_payout(self, order: COPOrder):
        """Execute COP payout to seller.

        CRITICAL: This method sends real money. Protected by 3-layer guard:
        1. State check (must be PAYOUT_PENDING)
        2. DB at-most-once claim (cop_payout_claims table)
        3. Exchange verification (order still active on Binance)
        """
        order_id = order.binance_order_id

        # GUARD 1: State check
        if order.state != COPOrderState.PAYOUT_PENDING:
            self.tracker.log_audit(order_id, "PAYOUT_BLOCKED",
                f"State is {order.state.value}, expected PAYOUT_PENDING", "REJECTED")
            return

        # GUARD 2: DB at-most-once claim
        if not self.tracker.try_claim_payout(order_id):
            self.tracker.log_audit(order_id, "PAYOUT_BLOCKED",
                "DB guard: payout already claimed by another path", "SKIPPED")
            logger.warning(f"PAYOUT GUARD: {order_id} already claimed")
            return

        # GUARD 3: Verify order still active on Binance
        try:
            detail = await self.binance.get_order_detail(order_id)
            if not detail:
                self.tracker.mark_payout_result(order_id, False)
                self.tracker.log_audit(order_id, "PAYOUT_BLOCKED",
                    "Order not found on Binance", "REJECTED")
                self.tracker.transition(order_id, COPOrderState.CANCELLED)
                return
            order_status = str(detail.get("orderStatus", ""))
            if order_status in ("5", "COMPLETED", "4", "CANCELLED"):
                self.tracker.mark_payout_result(order_id, False)
                self.tracker.log_audit(order_id, "PAYOUT_BLOCKED",
                    f"Order already {order_status} on Binance", "REJECTED")
                self.tracker.transition(order_id, COPOrderState.CANCELLED)
                return
        except Exception as e:
            self.tracker.mark_payout_result(order_id, False)
            self.tracker.log_audit(order_id, "PAYOUT_BLOCKED",
                f"Failed to verify order on Binance: {e}", "REJECTED")
            logger.error(f"Cannot verify BUY order {order_id} on Binance: {e}")
            return

        if not self._use_new_client or not self.facilitapay:
            self.tracker.mark_payout_result(order_id, False)
            self.tracker.log_audit(order_id, "PAYOUT_BLOCKED",
                "FacilitaPay client not available", "ERROR")
            logger.error(f"No FacilitaPay client for BUY payout {order_id}")
            return

        try:
            # Step 1: Register/get FP subject (idempotent via DB dedup)
            subject_id = self.tracker.get_subject_by_cc(order.customer_cc)
            if not subject_id:
                doc_type = FPDocumentType.CC if (order.customer_cc and len(order.customer_cc) >= 8) else FPDocumentType.CE
                subject = await self.facilitapay.upsert_subject_person(
                    document_number=order.customer_cc,
                    document_type=doc_type,
                    social_name=order.customer_name or "P2P Seller",
                    email=order.customer_email or "noreply@axion.exchange",
                    phone_area_code="300",
                    phone_number="0000000",
                    address_street="No registrada",
                    address_number="0",
                    address_city="Bogota",
                )
                subject_id = subject.id
                self.tracker.cache_subject(order.customer_cc, subject_id,
                                          order.customer_name, order.customer_email)
            self.tracker.log_audit(order_id, "FP_SUBJECT_READY", f"subject_id={subject_id}")

            # Step 2: Register bank account (idempotent via FP DB dedup)
            acct_type = FPAccountType.SAVINGS if order.seller_account_type == "savings" else FPAccountType.CHECKING
            bank_acct = await self.facilitapay.register_customer_bank_account(
                subject_id=subject_id,
                account_number=order.seller_account_number,
                branch_number="0001",
                bank_code=order.bank_code,
                bank_name=order.bank_name or "",
                owner_name=order.customer_name or "",
                owner_document_number=order.customer_cc,
                account_type=acct_type,
            )
            self.tracker.set_seller_bank_account_id(order_id, bank_acct.id if hasattr(bank_acct, 'id') else str(bank_acct))
            self.tracker.log_audit(order_id, "FP_BANK_ACCT_READY",
                f"bank_account_id={bank_acct.id if hasattr(bank_acct, 'id') else bank_acct}")

            # Step 3: Execute COP payout (FP has its own DB dedup)
            from .facilitapay_client import FacilitaPayDuplicateError
            try:
                tx = await self.facilitapay.create_cop_payout(
                    subject_id=subject_id,
                    to_bank_account_id=bank_acct.id if hasattr(bank_acct, 'id') else str(bank_acct),
                    value_cop=str(order.amount_cop),
                    pear_order_id=order_id,
                )
            except FacilitaPayDuplicateError as e:
                self.tracker.log_audit(order_id, "PAYOUT_DEDUP",
                    f"FP duplicate payout: {e}", "SKIPPED")
                logger.warning(f"FP payout dedup for {order_id}: {e}")
                # Payout was already sent — transition to PAYOUT_SENT
                self.tracker.mark_payout_result(order_id, True)
                self.tracker.transition(order_id, COPOrderState.PAYOUT_SENT)
                order = self.tracker.get_order(order_id)
                if order:
                    await self._buy_mark_paid_with_retries(order)
                return

            # Record payout success
            self.tracker.mark_payout_result(order_id, True)
            self.tracker.set_payout_tx_id(order_id, tx.id)
            self.tracker.transition(order_id, COPOrderState.PAYOUT_SENT)
            self.tracker.log_audit(order_id, "PAYOUT_SENT",
                f"FP tx_id={tx.id} amount_cop={order.amount_cop}")
            logger.info(f"COP PAYOUT SENT for {order_id}: {order.amount_cop} COP (tx={tx.id})")

            # Step 4: Mark order as paid on Binance (with retries)
            order = self.tracker.get_order(order_id)
            if order:
                await self._buy_mark_paid_with_retries(order)

        except Exception as e:
            import traceback
            self.tracker.mark_payout_result(order_id, False)
            self.tracker.log_audit(order_id, "PAYOUT_ERROR",
                f"{type(e).__name__}: {e}", "ERROR")
            self.tracker.transition(order_id, COPOrderState.MANUAL_REVIEW)
            logger.error(f"BUY PAYOUT ERROR for {order_id}: {e}\n{traceback.format_exc()}")

    async def _buy_mark_paid_with_retries(self, order: COPOrder):
        """Mark BUY order as paid with inline retries + reconciliation fallback.

        Mirrors EUR P0-A pattern:
        - 3 inline retries with 2s backoff
        - If all fail, transition to MARK_PAID_PENDING for reconciliation
        """
        order_id = order.binance_order_id
        self.tracker.set_mark_paid_pending(order_id)

        for attempt in range(1, 4):
            try:
                success = await self.binance.mark_order_paid(order_id)
                if success:
                    self.tracker.resolve_mark_paid(order_id)
                    self.tracker.transition(order_id, COPOrderState.COMPLETED)
                    self.tracker.log_audit(order_id, "MARK_PAID_SUCCESS",
                        f"Attempt {attempt}/3")
                    # Notify seller
                    try:
                        cop_formatted = f"{float(order.amount_cop):,.0f}" if order.amount_cop else "?"
                    except (ValueError, TypeError):
                        cop_formatted = str(order.amount_cop)
                    try:
                        await self.binance.send_chat_message(
                            order_id,
                            MESSAGES["buy_payout_sent"].format(cop=cop_formatted),
                        )
                    except Exception:
                        pass  # Non-critical
                    logger.info(f"BUY mark_paid SUCCESS for {order_id} (attempt {attempt})")
                    return
            except Exception as e:
                logger.warning(f"BUY mark_paid attempt {attempt}/3 failed for {order_id}: {e}")

            await asyncio.sleep(2 * attempt)

        # All inline retries failed — reconciliation will handle it
        self.tracker.transition(order_id, COPOrderState.MARK_PAID_PENDING)
        self.tracker.log_audit(order_id, "MARK_PAID_FAILED",
            "3 inline retries exhausted — reconciliation pending", "WARNING")
        logger.critical(
            f"COP SENT but mark_paid FAILED for {order_id} — reconciliation will retry"
        )

    async def _reconcile_buy_mark_paid(self, order: COPOrder):
        """Retry mark_paid for BUY orders where COP was sent but Binance mark failed.

        Called on each poll cycle for orders in PAYOUT_SENT or MARK_PAID_PENDING.
        Uses exponential backoff up to 10 retries (max 5 minutes between attempts).
        """
        order_id = order.binance_order_id

        if order.mark_paid_retries >= 10:
            self.tracker.transition(order_id, COPOrderState.MANUAL_REVIEW)
            self.tracker.log_audit(order_id, "MARK_PAID_EXHAUSTED",
                "10 reconciliation retries exhausted — escalating", "CRITICAL")
            logger.critical(f"BUY mark_paid EXHAUSTED for {order_id} — MANUAL_REVIEW")
            return

        # Exponential backoff: 30s, 60s, 120s, 240s, 300s (cap)
        backoff_seconds = min(300, 30 * (2 ** order.mark_paid_retries))
        if order.payout_sent_at:
            elapsed = (datetime.utcnow() - order.payout_sent_at).total_seconds()
            needed = backoff_seconds * (order.mark_paid_retries + 1)
            if elapsed < needed:
                return  # Not time yet

        try:
            success = await self.binance.mark_order_paid(order_id)
        except Exception as e:
            logger.warning(f"BUY reconciliation mark_paid error for {order_id}: {e}")
            success = False

        retry_count = self.tracker.increment_mark_paid_retries(order_id)

        if success:
            self.tracker.resolve_mark_paid(order_id)
            self.tracker.transition(order_id, COPOrderState.COMPLETED)
            self.tracker.log_audit(order_id, "MARK_PAID_RECONCILED",
                f"Succeeded on reconciliation retry {retry_count}")
            # Notify seller
            try:
                cop_formatted = f"{float(order.amount_cop):,.0f}" if order.amount_cop else "?"
                await self.binance.send_chat_message(
                    order_id,
                    MESSAGES["buy_payout_sent"].format(cop=cop_formatted),
                )
            except Exception:
                pass
            logger.info(f"BUY mark_paid RECONCILED for {order_id} (retry {retry_count})")
        else:
            self.tracker.log_audit(order_id, "MARK_PAID_RETRY",
                f"Retry {retry_count}/10 failed — next in {backoff_seconds}s", "WARNING")
            logger.warning(f"BUY mark_paid retry {retry_count}/10 failed for {order_id}")

