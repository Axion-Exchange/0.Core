"""
MXN Handler
===========
Main orchestrator for MXN P2P orders on Binance.
Mirrors cop_handler.py architecture with MXN-specific flows:

SELL flow: Dynamic CLABE (auto-reconciled SPEI pay-in)
BUY flow: SPEI payout to seller's CLABE

Safety mechanisms replicated from COP:
- M1: Per-order asyncio.Lock
- P0-2: Atomic release guard (INSERT OR IGNORE)
- P0-3: Atomic payout guard (INSERT OR IGNORE)
- Webhook dedup via FP persistence layer
- CURP reuse detection (cross-account fraud)
- Reconciliation sweep every ~5 minutes
- Urgent check queue from orchestrator
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .mxn_types import MXNOrder, MXNOrderState, MESSAGES
from .mxn_tracker import MXNOrderTracker
from .mxn_info_extractor import extract_info, validate_curp, validate_clabe, MXNCustomerInfo
from .facilitapay_mxn_client import (
    FacilitaPayMXNClient, FacilitaPayMXNError, FacilitaPayMXNDuplicateError,
)

logger = logging.getLogger("mxn_handler")

# Urgent check queue — fed by orchestrator when Binance buyer marks MXN order as paid
_urgent_checks: asyncio.Queue = asyncio.Queue()
_handler_instance: Optional["MXNHandler"] = None


def request_urgent_fp_check(order_id: str) -> None:
    """Non-blocking push to urgent check queue (called by orchestrator)."""
    try:
        _urgent_checks.put_nowait(order_id)
    except asyncio.QueueFull:
        logger.warning(f"Urgent check queue full — skipping {order_id}")


class MXNHandler:
    """Main handler for MXN P2P orders."""

    def __init__(
        self,
        # Binance MXN account
        binance_api_key: str,
        binance_api_secret: str,
        binance_2fa_secret: str = "",
        # FacilitaPay (shared credentials)
        fp_username: str = "",
        fp_password: str = "",
        fp_cashin_account_id: str = "",
        fp_cashout_account_id: str = "",
        fp_webhook_secret: str = "",
        fp_base_url: str = "https://api.facilitapay.com/api/v1",
        # Config
        poll_interval: float = 30.0,
        db_path: str = "data/mxn_orders.db",
        fp_db_path: str = "data/facilitapay_mxn.db",
        auto_send_clabe: bool = True,
    ):
        # Binance chat client (same class as COP, different credentials)
        from src.fiat.cop.binance_chat import BinanceChatClient
        self.binance = BinanceChatClient(
            api_key=binance_api_key,
            api_secret=binance_api_secret,
        )
        self.binance_2fa_secret = binance_2fa_secret

        # FacilitaPay MXN client
        self.facilitapay: FacilitaPayMXNClient | None = None
        if fp_username and fp_password:
            self.facilitapay = FacilitaPayMXNClient(
                username=fp_username,
                password=fp_password,
                cashin_account_id=fp_cashin_account_id,
                cashout_account_id=fp_cashout_account_id,
                webhook_secret=fp_webhook_secret,
                base_url=fp_base_url,
                db_path=fp_db_path,
            )

        # Order tracker
        self.tracker = MXNOrderTracker(db_path=db_path)

        # Config
        self.poll_interval = poll_interval
        self.auto_send_clabe = auto_send_clabe

        # Runtime state
        self._running = False
        self._order_locks: dict[str, asyncio.Lock] = {}
        self._trustpilot_sent: set[str] = set()
        self._seen_messages: dict[str, set] = {}
        self._sweep_counter = 0

    async def start(self):
        """Start the polling loop."""
        from src.core.health import task_registry

        global _handler_instance
        _handler_instance = self

        self._running = True
        self._sweep_counter = 0
        self._consecutive_failures = 0
        _MAX_CONSECUTIVE_FAILURES = 10
        logger.info(f"MXN Handler started (poll every {self.poll_interval}s)")

        # Start urgent check listener
        asyncio.create_task(self._urgent_check_listener())

        while self._running:
            try:
                await self._poll_cycle()
                task_registry.heartbeat("mxn_handler")
                self._consecutive_failures = 0

                # Reconciliation sweep every ~5 minutes
                self._sweep_counter += 1
                sweep_interval = max(1, int(300 / self.poll_interval))
                if self._sweep_counter >= sweep_interval:
                    self._sweep_counter = 0
                    await self._reconciliation_sweep()
            except Exception as e:
                self._consecutive_failures += 1
                logger.error(
                    "Poll cycle error (%d/%d): %s\n%s",
                    self._consecutive_failures,
                    _MAX_CONSECUTIVE_FAILURES,
                    e, traceback.format_exc(),
                )
                task_registry.mark_error("mxn_handler", str(e))
                if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                    logger.critical("MXN handler exceeded %d failures — re-raising", _MAX_CONSECUTIVE_FAILURES)
                    raise

            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False

    # ================================================================
    # Urgent Check Listener
    # ================================================================

    async def _urgent_check_listener(self):
        """Listen for urgent FP check requests from the orchestrator."""
        logger.info("MXN urgent FP check listener started")
        while self._running:
            try:
                order_id = await asyncio.wait_for(_urgent_checks.get(), timeout=5.0)
                logger.info(f"URGENT MXN CHECK: {order_id}")
                await asyncio.sleep(3.0)

                if order_id not in self._order_locks:
                    self._order_locks[order_id] = asyncio.Lock()

                async with self._order_locks[order_id]:
                    order = self.tracker.get_order(order_id)
                    if not order:
                        continue
                    if order.state in (MXNOrderState.COMPLETED, MXNOrderState.CANCELLED):
                        continue
                    if order.state == MXNOrderState.CLABE_SENT:
                        await self._poll_payment_status(order)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Urgent check error: {e}")
                await asyncio.sleep(1.0)

    # ================================================================
    # Poll Cycle
    # ================================================================

    async def _poll_cycle(self):
        """One poll cycle: check active orders, read chat, process."""
        orders = await self.binance.get_active_orders()

        for order_data in orders:
            order_number = order_data.get("orderNumber", "")
            fiat = order_data.get("fiat", "")

            if fiat != "MXN":
                continue

            # M1: Per-order async lock
            if order_number not in self._order_locks:
                self._order_locks[order_number] = asyncio.Lock()

            trade_type = order_data.get("tradeType", "SELL")

            async with self._order_locks[order_number]:
                if trade_type == "BUY":
                    await self._process_buy_order(order_number, order_data)
                else:
                    await self._process_sell_order(order_number, order_data)

    # ================================================================
    # SELL Flow (we sell USDT, buyer pays MXN via SPEI)
    # ================================================================

    async def _process_sell_order(self, order_number: str, order_data: dict):
        """Process a single MXN SELL order."""
        order = self.tracker.get_order(order_number)
        if not order:
            order = self.tracker.create_order(
                binance_order_id=order_number,
                binance_external_id=order_number,
                amount_mxn=order_data.get("totalPrice", "0"),
                amount_usdt=order_data.get("amount", "0"),
                binance_buyer_name=order_data.get("counterPartNickName", ""),
            )
            self.tracker.log_audit(order_number, "ORDER_CREATED",
                f"MXN={order_data.get('totalPrice')} USDT={order_data.get('amount')}")
            logger.info(f"New MXN SELL order: {order_number} - MXN {order_data.get('totalPrice')}")

        # Send welcome message once
        if not order.welcome_sent:
            usdt_raw = order.amount_usdt or order_data.get("amount", "")
            try:
                usdt = f"{float(usdt_raw):.2f}" if usdt_raw else ""
            except (ValueError, TypeError):
                usdt = str(usdt_raw)
            sent = await self.binance.send_chat_message(
                order_number, MESSAGES["welcome"].format(usdt=usdt)
            )
            if sent:
                self.tracker.mark_welcome_sent(order_number)
            else:
                logger.warning(f"Welcome failed for {order_number}, will retry")

        # Skip terminal/active states
        if order.state in (MXNOrderState.COMPLETED, MXNOrderState.RELEASING,
                           MXNOrderState.MANUAL_REVIEW, MXNOrderState.CANCELLED,
                           MXNOrderState.GENERATING_CLABE):
            return
        if order.state == MXNOrderState.CLABE_SENT:
            await self._poll_payment_status(order)
            order = self.tracker.get_order(order_number)
            if not order or order.state != MXNOrderState.CLABE_SENT:
                return
            return  # CLABE valid for 30 days, just wait

        # Read chat for CURP
        await self._read_sell_chat(order_number, order)

        # Re-read order (may have been updated)
        order = self.tracker.get_order(order_number)
        if not order:
            return

        # If we have CURP, generate Dynamic CLABE
        if order.customer_curp and order.state in (MXNOrderState.NEW, MXNOrderState.AWAITING_CURP,
                                                     MXNOrderState.CURP_RECEIVED):
            await self._generate_and_send_clabe(order)

    async def _read_sell_chat(self, order_number: str, order: MXNOrder):
        """Read chat messages, extract CURP."""
        try:
            messages = await self.binance.get_chat_messages(order_number)
        except Exception as e:
            logger.warning(f"Chat read error for {order_number}: {e}")
            return

        if not messages:
            return

        # Track seen messages for dedup
        seen_key = f"seen_{order_number}"
        seen = self._seen_messages.get(seen_key, set())
        new_messages = []

        for msg in messages:
            msg_id = str(msg.get("id", msg.get("uuid", "")))
            is_self = msg.get("self", False)
            content = msg.get("content", "")

            # Only process counterparty messages
            if is_self or not content:
                continue
            if msg_id in seen:
                continue

            seen.add(msg_id)
            stripped = content.strip()
            if stripped.startswith('{') and 'type' in stripped.lower():
                continue
            new_messages.append(content)
            self.tracker.add_message(order_number, content)

        self._seen_messages[seen_key] = seen

        if new_messages:
            # Extract CURP from all accumulated messages
            extracted = extract_info(order.chat_messages)

            if extracted.is_complete_for_sell():
                # Validate CURP
                valid, result = validate_curp(extracted.curp)
                if not valid:
                    await self.binance.send_chat_message(
                        order_number, MESSAGES["invalid_curp"]
                    )
                    return

                # Security: CURP reuse detection
                prev_name = self.tracker.check_curp_different_account(
                    extracted.curp, order.binance_buyer_name
                )
                if prev_name:
                    logger.warning(f"CURP SECURITY: {extracted.curp[:4]}*** used by {prev_name}")
                    await self.binance.send_chat_message(
                        order_number, MESSAGES["curp_security_alert"]
                    )
                    self.tracker.transition(order_number, MXNOrderState.MANUAL_REVIEW)
                    return

                # Save all info
                order.customer_curp = extracted.curp
                order.customer_name = extracted.name
                order.customer_rfc = extracted.rfc
                self.tracker.transition(order_number, MXNOrderState.CURP_RECEIVED)
                self.tracker.log_audit(order_number, "INFO_COMPLETE",
                    f"curp={extracted.curp[:4]}*** name={extracted.name} email={extracted.email[:3] if extracted.email else '?'}***")
            else:
                # Save partial info
                if extracted.curp: order.customer_curp = extracted.curp
                if extracted.name: order.customer_name = extracted.name
                if extracted.rfc: order.customer_rfc = extracted.rfc
                self.tracker._save(order)

                missing = extracted.missing_sell_fields()
                if missing and order.state == MXNOrderState.NEW:
                    self.tracker.transition(order_number, MXNOrderState.AWAITING_CURP)
                if missing:
                    await self.binance.send_chat_message(
                        order_number,
                        MESSAGES["missing_fields"].format(fields=", ".join(missing))
                    )

    async def _generate_and_send_clabe(self, order: MXNOrder):
        """Generate Dynamic CLABE via FacilitaPay and send to buyer."""
        if not self.facilitapay:
            logger.error("No FacilitaPay client available")
            return

        order_id = order.binance_order_id
        self.tracker.transition(order_id, MXNOrderState.GENERATING_CLABE)

        try:
            # Register/get FP subject
            subject_id = self.tracker.get_subject_by_curp(order.customer_curp)
            if not subject_id:
                # Get email from the extraction (stored in tracker)
                customer_email = "noreply@axion.exchange"
                # Look up email from chat messages
                from .mxn_info_extractor import extract_info as _extract
                _info = _extract(order.chat_messages)
                if _info.email:
                    customer_email = _info.email

                subject_id = await self.facilitapay.upsert_mexican_subject(
                    curp=order.customer_curp,
                    social_name=order.customer_name or order.binance_buyer_name or "P2P Buyer",
                    email=customer_email,
                    rfc_pf=order.customer_rfc,
                )
                self.tracker.cache_subject(order.customer_curp, subject_id,
                                           order.customer_name)

            # Create Dynamic CLABE transaction
            try:
                tx = await self.facilitapay.create_dynamic_clabe_payin(
                    subject_id=subject_id,
                    value_mxn=str(order.amount_mxn),
                    pear_order_id=order_id,
                    payment_description=f"Axion P2P {order_id}",
                )
            except FacilitaPayMXNDuplicateError as e:
                logger.warning(f"CLABE dedup: {e}")
                return

            if not tx.dynamic_clabe:
                logger.error(f"Dynamic CLABE missing from API response for {order_id}")
                self.tracker.log_audit(order_id, "CLABE_MISSING",
                    "API returned transaction without dynamic_clabe", "ERROR")
                return

            # Save CLABE and transition
            self.tracker.set_dynamic_clabe(
                order_id=order_id,
                subject_id=subject_id,
                tx_id=tx.id,
                dynamic_clabe=tx.dynamic_clabe,
            )

            if self.auto_send_clabe:
                await self.binance.send_chat_message(
                    order_id,
                    MESSAGES["clabe_sent"].format(
                        clabe=tx.dynamic_clabe,
                        amount=order.amount_mxn,
                        reference=order_id,
                    )
                )
                logger.info(f"CLABE sent: {order_id} → {tx.dynamic_clabe[-4:]}")

        except Exception as e:
            logger.error(f"Error generating CLABE: {e}\n{traceback.format_exc()}")
            self.tracker.log_audit(order_id, "CLABE_ERROR", str(e), "ERROR")

    # ================================================================
    # Payment Status Polling
    # ================================================================

    async def _poll_payment_status(self, order: MXNOrder):
        """Poll FacilitaPay for payment status on CLABE_SENT orders."""
        if not self.facilitapay:
            return

        order_id = order.binance_order_id
        tx_row = self.facilitapay.db.get_transaction_by_order(order_id, "payin")
        if not tx_row:
            return

        tx_id = tx_row["id"]
        local_status = tx_row["status"]

        # If already identified, check if order completed
        if local_status in ("identified", "approved", "settled"):
            order_obj = self.tracker.get_order(order_id)
            if order_obj and order_obj.state in (MXNOrderState.COMPLETED, MXNOrderState.CANCELLED):
                return
            # Payment confirmed but release didn't complete — retry
            logger.warning(f"POLL RETRY: {order_id} FP={local_status} but state={order_obj.state.value if order_obj else 'UNKNOWN'}")
            await self._handle_payment_confirmed(order_id, tx_row.get("amount", "0"))
            return

        # Poll FP API for fresh status
        try:
            new_status = await self.facilitapay.poll_transaction_status(tx_id)
            if new_status in ("identified", "approved", "settled"):
                logger.info(f"MXN payment confirmed (poll): {order_id} status={new_status}")
                self.tracker.log_audit(order_id, "PAYMENT_IDENTIFIED_POLL",
                    f"FP status={new_status}")
                await self._handle_payment_confirmed(order_id, tx_row.get("amount", "0"))
        except Exception as e:
            logger.warning(f"Payment poll error for {order_id}: {e}")

    # ================================================================
    # Webhook Handler (called from webhook router)
    # ================================================================

    async def handle_webhook(self, order_id: str, tx_amount: str,
                             tx_status: str) -> bool:
        """
        Handle FacilitaPay webhook for MXN payment.
        Called when 'identified' webhook arrives for an MXN transaction.

        MUST be called under per-order lock.
        """
        return await self._handle_payment_confirmed(order_id, tx_amount)

    async def _handle_payment_confirmed(self, order_id: str,
                                         tx_amount_mxn: str) -> bool:
        """
        Handle confirmed MXN payment — verify amount and release crypto.

        5-guard release:
        1. Order exists and not terminal
        2. State is in releasable states
        3. Amount matches (≤1 MXN tolerance)
        4. DB release guard (atomic INSERT OR IGNORE)
        5. Binance liveness check
        """
        order = self.tracker.get_order(order_id)
        if not order:
            logger.warning(f"Webhook for unknown order: {order_id}")
            return False

        # Guard 1: Skip terminal
        if order.state in (MXNOrderState.COMPLETED, MXNOrderState.CANCELLED):
            logger.debug(f"Already terminal: {order_id} ({order.state.value})")
            return False

        # Guard 2: State check
        RELEASABLE_STATES = {
            MXNOrderState.CLABE_SENT,
            MXNOrderState.AWAITING_PAYMENT,
            MXNOrderState.PAYMENT_RECEIVED,
            MXNOrderState.RELEASING,
        }
        if order.state not in RELEASABLE_STATES:
            logger.warning(f"Order {order_id} in non-releasable state: {order.state.value}")
            return False

        # Guard 3: Amount match (≤1 MXN tolerance)
        expected_mxn = str(order.amount_mxn or "0")
        try:
            paid_int = int(Decimal(str(tx_amount_mxn)).to_integral_value())
            expected_int = int(Decimal(str(expected_mxn)).to_integral_value())
            diff = abs(paid_int - expected_int)
            if diff > 1:
                self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                    f"Amount mismatch: paid={paid_int} expected={expected_int} diff={diff}",
                    "REJECTED")
                self.tracker.transition(order_id, MXNOrderState.MANUAL_REVIEW)
                logger.error(f"SECURITY: Amount mismatch on {order_id}!")
                return False
            elif diff > 0:
                logger.info(f"MXN rounding accepted: paid={paid_int} expected={expected_int}")
        except Exception as e:
            self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                f"Amount compare error: {e}", "REJECTED")
            return False

        # Record payment
        self.tracker.transition(order_id, MXNOrderState.PAYMENT_RECEIVED)
        self.tracker.log_audit(order_id, "PAYMENT_VERIFIED",
            f"amount={tx_amount_mxn}")

        # Transition to RELEASING
        self.tracker.transition(order_id, MXNOrderState.RELEASING)
        self.tracker.log_audit(order_id, "RELEASE_ATTEMPT",
            f"amount_usdt={order.amount_usdt}")

        # Guard 4: DB release guard
        if not self.tracker.try_claim_release(order_id):
            self.tracker.log_audit(order_id, "RELEASE_BLOCKED",
                "DB guard: release already claimed", "SKIPPED")
            logger.warning(f"RELEASE GUARD: {order_id} already claimed")
            # Verify on Binance
            try:
                bdetail = await self.binance.get_order_detail(order_id)
                if bdetail and str(bdetail.get("orderStatus", "")) in ("5", "COMPLETED"):
                    self.tracker.transition(order_id, MXNOrderState.COMPLETED)
                    return True
            except Exception:
                pass
            self.tracker.transition(order_id, MXNOrderState.MANUAL_REVIEW)
            return False

        # Guard 5: Send thank-you BEFORE release
        try:
            thank_you = (
                "\U0001f389 ¡Transacción completada! Gracias por operar con nosotros.\n"
                "Ayuda a otros traders a encontrarnos — déjanos una reseña rápida:\n"
                "⭐ https://trustpilot.com/review/axionexchange.io\n"
                "¡Tu apoyo significa mucho! \U0001f499"
            )
            await self.binance.send_chat_message(order_id, thank_you)
            self._trustpilot_sent.add(order_id)
        except Exception as e:
            logger.warning(f"Failed to send thank-you for {order_id}: {e}")

        # Guard 5b: Binance liveness check
        try:
            bdetail = await self.binance.get_order_detail(order_id)
        except Exception:
            bdetail = None
        if not bdetail:
            logger.warning(f"RELEASE SKIP: {order_id} not found on Binance (404)")
            self.tracker.transition(order_id, MXNOrderState.COMPLETED)
            self.tracker.mark_release_result(order_id, True)
            return True
        b_status = str(bdetail.get("orderStatus", ""))
        if b_status in ("5", "COMPLETED"):
            self.tracker.transition(order_id, MXNOrderState.COMPLETED)
            self.tracker.mark_release_result(order_id, True)
            return True

        # IRREVERSIBLE: Release crypto
        success = await self.binance.release_crypto(order_id, self.binance_2fa_secret)
        self.tracker.mark_release_result(order_id, success)

        if success:
            self.tracker.transition(order_id, MXNOrderState.COMPLETED)
            self.tracker.log_audit(order_id, "RELEASE_SUCCESS",
                f"Released {order.amount_usdt} USDT", "OK")
            logger.info(f"Crypto released for MXN {order_id}: {order.amount_usdt} USDT")
        else:
            self.tracker.log_audit(order_id, "RELEASE_FAILED",
                "Binance API rejected release", "FAILED")
            self.tracker.transition(order_id, MXNOrderState.MANUAL_REVIEW)

        return success

    # ================================================================
    # BUY Flow (we buy USDT, pay MXN to seller via SPEI)
    # ================================================================

    async def _process_buy_order(self, order_number: str, order_data: dict):
        """Process a MXN BUY order."""
        order = self.tracker.get_order(order_number)
        if not order:
            order = self.tracker.create_order(
                binance_order_id=order_number,
                binance_external_id=order_number,
                amount_mxn=order_data.get("totalPrice", "0"),
                amount_usdt=order_data.get("amount", "0"),
                binance_buyer_name=order_data.get("counterPartNickName", ""),
                order_side="BUY",
            )
            self.tracker.log_audit(order_number, "BUY_ORDER_CREATED",
                f"MXN={order_data.get('totalPrice')} USDT={order_data.get('amount')}")
            logger.info(f"New MXN BUY order: {order_number}")

        # Send welcome once
        if not order.welcome_sent:
            try:
                await self.binance.send_chat_message(order_number, MESSAGES["buy_welcome"])
                self.tracker.mark_welcome_sent(order_number)
            except Exception as e:
                logger.warning(f"BUY welcome failed for {order_number}: {e}")

        # Skip terminal states
        if order.state in (MXNOrderState.COMPLETED, MXNOrderState.CANCELLED,
                           MXNOrderState.MANUAL_REVIEW, MXNOrderState.PAYOUT_SENT,
                           MXNOrderState.MARK_PAID_PENDING):
            # Handle mark_paid retries for MARK_PAID_PENDING
            if order.state == MXNOrderState.MARK_PAID_PENDING:
                await self._retry_mark_paid(order)
            return

        # Skip if payout already sent
        if order.state == MXNOrderState.PAYOUT_PENDING:
            await self._execute_mxn_buy_payout(order)
            return

        # Read chat for seller's CURP + CLABE
        await self._read_buy_chat(order_number, order)

    async def _read_buy_chat(self, order_number: str, order: MXNOrder):
        """Read chat and extract seller's CURP + CLABE for BUY payout."""
        try:
            messages = await self.binance.get_chat_messages(order_number)
        except Exception as e:
            logger.warning(f"BUY chat error for {order_number}: {e}")
            return

        if not messages:
            return

        seen_key = f"seen_{order_number}"
        seen = self._seen_messages.get(seen_key, set())
        new_messages = []

        for msg in messages:
            msg_id = msg.get("id", msg.get("uuid", ""))
            sender = msg.get("sender", "")
            content = msg.get("content", "")
            if sender == "self" or not content:
                continue
            if msg_id in seen:
                continue
            seen.add(msg_id)
            stripped = content.strip()
            if stripped.startswith('{') and 'type' in stripped.lower():
                continue
            new_messages.append(content)
            self.tracker.add_message(order_number, content)

        self._seen_messages[seen_key] = seen

        if new_messages:
            order = self.tracker.get_order(order_number)
            if not order:
                return

            previous = MXNCustomerInfo(
                name=order.customer_name,
                curp=order.customer_curp,
                clabe=order.customer_clabe,
            )
            extracted = extract_info(order.chat_messages, previous=previous)

            if not extracted.is_complete_for_buy():
                # Save partial info
                if extracted.name: order.customer_name = extracted.name
                if extracted.curp: order.customer_curp = extracted.curp
                if extracted.clabe: order.customer_clabe = extracted.clabe
                self.tracker._save(order)
                missing = extracted.missing_buy_fields()
                logger.info(f"BUY partial for {order_number}, missing: {missing}")
                return

            # Validate CURP
            valid, result = validate_curp(extracted.curp)
            if not valid:
                await self.binance.send_chat_message(
                    order_number, MESSAGES["invalid_curp"]
                )
                return

            # Validate CLABE
            valid, result = validate_clabe(extracted.clabe)
            if not valid:
                await self.binance.send_chat_message(
                    order_number,
                    f"[!] La CLABE ingresada no es válida: {result}. Debe tener 18 dígitos."
                )
                return

            # Security: CURP reuse
            prev_name = self.tracker.check_curp_different_account(
                extracted.curp, order.binance_buyer_name
            )
            if prev_name:
                logger.warning(f"BUY SECURITY: CURP reuse detected for {order_number}")
                self.tracker.transition(order_number, MXNOrderState.MANUAL_REVIEW)
                return

            # Save complete info
            self.tracker.set_buy_customer_info(
                order_number,
                name=extracted.name or "P2P Seller",
                curp=extracted.curp,
                clabe=extracted.clabe,
                rfc=extracted.rfc,
            )
            self.tracker.transition(order_number, MXNOrderState.PAYOUT_PENDING)
            self.tracker.log_audit(order_number, "BUY_INFO_COMPLETE",
                f"curp={extracted.curp[:4]}*** clabe=***{extracted.clabe[-4:]}")

            # Auto-execute payout
            order = self.tracker.get_order(order_number)
            if order:
                await self._execute_mxn_buy_payout(order)

    async def _execute_mxn_buy_payout(self, order: MXNOrder):
        """Execute SPEI payout to seller. Protected by 3-layer guard."""
        order_id = order.binance_order_id

        # GUARD 1: State check
        if order.state != MXNOrderState.PAYOUT_PENDING:
            return

        # GUARD 2: DB at-most-once
        if not self.tracker.try_claim_payout(order_id):
            logger.warning(f"PAYOUT GUARD: {order_id} already claimed")
            return

        # GUARD 3: Verify order active on Binance
        try:
            detail = await self.binance.get_order_detail(order_id)
            if not detail:
                self.tracker.mark_payout_result(order_id, False)
                self.tracker.transition(order_id, MXNOrderState.CANCELLED)
                return
            status = str(detail.get("orderStatus", ""))
            if status in ("5", "COMPLETED", "4", "CANCELLED"):
                self.tracker.mark_payout_result(order_id, False)
                self.tracker.transition(order_id, MXNOrderState.CANCELLED)
                return
        except Exception as e:
            self.tracker.mark_payout_result(order_id, False)
            logger.error(f"Cannot verify BUY order {order_id}: {e}")
            return

        if not self.facilitapay:
            self.tracker.mark_payout_result(order_id, False)
            logger.error(f"No FP client for BUY payout {order_id}")
            return

        try:
            # Register subject
            subject_id = self.tracker.get_subject_by_curp(order.customer_curp)
            if not subject_id:
                subject_id = await self.facilitapay.upsert_mexican_subject(
                    curp=order.customer_curp,
                    social_name=order.customer_name or order.binance_buyer_name or "P2P Seller",
                    rfc_pf=order.customer_rfc,
                )
                self.tracker.cache_subject(order.customer_curp, subject_id)

            # Register bank account (CLABE)
            bank_account_id = await self.facilitapay.register_mexican_bank_account(
                subject_id=subject_id,
                clabe=order.customer_clabe,
                owner_name=order.customer_name or order.binance_buyer_name or "P2P Seller",
                owner_curp=order.customer_curp,
            )

            # Send processing message
            await self.binance.send_chat_message(
                order_id,
                MESSAGES["buy_payout_processing"].format(mxn=order.amount_mxn),
            )

            # Create SPEI payout
            tx = await self.facilitapay.create_spei_payout(
                subject_id=subject_id,
                bank_account_id=bank_account_id,
                value_mxn=str(order.amount_mxn),
                pear_order_id=order_id,
                payment_description=f"Axion P2P Payout {order_id}",
            )

            # Record success
            self.tracker.mark_payout_result(order_id, True)
            order.facilitapay_payout_tx_id = tx.id
            order.payout_sent_at = datetime.utcnow()
            order.state = MXNOrderState.PAYOUT_SENT
            self.tracker._save(order)
            self.tracker.log_audit(order_id, "PAYOUT_SENT",
                f"fp_tx={tx.id[:8]} amount={order.amount_mxn} MXN")

            # Send confirmation
            await self.binance.send_chat_message(
                order_id,
                MESSAGES["buy_payout_sent"].format(mxn=order.amount_mxn),
            )

            # Mark order as paid on Binance
            await self._mark_paid_on_binance(order)

        except FacilitaPayMXNDuplicateError as e:
            logger.warning(f"BUY payout dedup: {e}")
        except Exception as e:
            self.tracker.mark_payout_result(order_id, False)
            logger.error(f"BUY payout error for {order_id}: {e}\n{traceback.format_exc()}")
            self.tracker.log_audit(order_id, "PAYOUT_ERROR", str(e), "ERROR")

    async def _mark_paid_on_binance(self, order: MXNOrder):
        """Mark BUY order as paid on Binance with retries."""
        order_id = order.binance_order_id
        self.tracker.transition(order_id, MXNOrderState.MARK_PAID_PENDING)

        for attempt in range(1, 4):
            try:
                success = await self.binance.mark_order_paid(order_id)
                if success:
                    order.mark_paid_at = datetime.utcnow()
                    self.tracker.transition(order_id, MXNOrderState.COMPLETED)
                    self.tracker.log_audit(order_id, "MARK_PAID_SUCCESS",
                        f"attempt={attempt}")

                    # Send thank-you
                    try:
                        thank_you = (
                            "\U0001f389 ¡Transacción completada! Gracias por operar con nosotros.\n"
                            "Ayuda a otros traders a encontrarnos — déjanos una reseña rápida:\n"
                            "⭐ https://trustpilot.com/review/axionexchange.io\n"
                            "¡Tu apoyo significa mucho! \U0001f499"
                        )
                        await self.binance.send_chat_message(order_id, thank_you)
                        self._trustpilot_sent.add(order_id)
                    except Exception:
                        pass
                    return
            except Exception as e:
                logger.warning(f"mark_paid attempt {attempt}/3 for {order_id}: {e}")
            if attempt < 3:
                await asyncio.sleep(2 * attempt)

        # All retries exhausted — reconciliation will pick up
        order.mark_paid_retries = 3
        self.tracker._save(order)
        self.tracker.log_audit(order_id, "MARK_PAID_EXHAUSTED",
            "3 attempts failed — reconciliation will retry", "WARNING")

    async def _retry_mark_paid(self, order: MXNOrder):
        """Retry mark_paid for orders stuck in MARK_PAID_PENDING."""
        if order.mark_paid_retries >= 10:
            return  # Give up after 10 total attempts
        try:
            success = await self.binance.mark_order_paid(order.binance_order_id)
            if success:
                order.mark_paid_at = datetime.utcnow()
                self.tracker.transition(order.binance_order_id, MXNOrderState.COMPLETED)
                return
        except Exception as e:
            logger.warning(f"mark_paid retry for {order.binance_order_id}: {e}")
        order.mark_paid_retries += 1
        self.tracker._save(order)

    # ================================================================
    # Reconciliation Sweep
    # ================================================================

    async def _reconciliation_sweep(self):
        """
        Reconciliation sweep — runs every ~5 minutes.
        Handles: stuck RELEASING recovery, stale orders, manual releases.
        """
        try:
            # Prune locks for terminal orders
            terminal_states = {MXNOrderState.COMPLETED, MXNOrderState.CANCELLED}
            stale_ids = [oid for oid in list(self._order_locks.keys())
                         if (o := self.tracker.get_order(oid)) and o.state in terminal_states
                         or not self.tracker.get_order(oid)]
            for oid in stale_ids:
                self._order_locks.pop(oid, None)

            # Check active orders on Binance
            for order in self.tracker.get_all_active_orders():
                oid = order.binance_order_id
                state = order.state

                # M2: RELEASING recovery
                if state == MXNOrderState.RELEASING:
                    try:
                        bdetail = await self.binance.get_order_detail(oid)
                        if bdetail and str(bdetail.get("orderStatus", "")) in ("5", "COMPLETED"):
                            self.tracker.transition(oid, MXNOrderState.COMPLETED)
                            self.tracker.log_audit(oid, "RELEASE_RECOVERED",
                                "Binance COMPLETED during reconciliation")
                        elif bdetail and str(bdetail.get("orderStatus", "")) in ("4", "CANCELLED"):
                            self.tracker.transition(oid, MXNOrderState.CANCELLED)
                    except Exception as e:
                        logger.warning(f"Recon check error for {oid}: {e}")

                # Stale detection (>2h in non-terminal state)
                elif order.created_at:
                    elapsed = (datetime.utcnow() - order.created_at).total_seconds()
                    if elapsed > 7200:
                        try:
                            bdetail = await self.binance.get_order_detail(oid)
                            if not bdetail:
                                self.tracker.transition(oid, MXNOrderState.CANCELLED)
                                self.tracker.log_audit(oid, "STALE_CANCELLED", "Binance 404 after 2h")
                            elif str(bdetail.get("orderStatus", "")) in ("5", "COMPLETED"):
                                # Manual release detected
                                if oid not in self._trustpilot_sent:
                                    try:
                                        thank_you = (
                                            "\U0001f389 ¡Transacción completada! Gracias por operar con nosotros.\n"
                                            "Ayuda a otros traders a encontrarnos — déjanos una reseña rápida:\n"
                                            "⭐ https://trustpilot.com/review/axionexchange.io\n"
                                            "¡Tu apoyo significa mucho! \U0001f499"
                                        )
                                        await self.binance.send_chat_message(oid, thank_you)
                                        self._trustpilot_sent.add(oid)
                                    except Exception:
                                        pass
                                self.tracker.transition(oid, MXNOrderState.COMPLETED)
                                self.tracker.log_audit(oid, "MANUAL_RELEASE_DETECTED",
                                    "Binance COMPLETED — Trustpilot sent")
                            elif str(bdetail.get("orderStatus", "")) in ("4", "CANCELLED"):
                                self.tracker.transition(oid, MXNOrderState.CANCELLED)
                        except Exception as e:
                            logger.warning(f"Stale check error for {oid}: {e}")

        except Exception as e:
            logger.error(f"Reconciliation sweep error: {e}")

    # ================================================================
    # Payment Expiry/Refund Handlers (from webhooks)
    # ================================================================

    async def handle_payment_expired(self, transaction_id: str):
        """Handle Dynamic CLABE expiry (30 days — extremely rare)."""
        if not self.facilitapay:
            return
        tx_data = self.facilitapay.db.get_transaction(transaction_id)
        if not tx_data:
            return
        order_id = tx_data.get("pear_order_id")
        if not order_id:
            return
        order = self.tracker.get_order(order_id)
        if not order:
            return
        self.facilitapay.db.update_transaction_status(transaction_id, "expired")
        if order.state in (MXNOrderState.CLABE_SENT, MXNOrderState.AWAITING_PAYMENT):
            self.tracker.transition(order_id, MXNOrderState.AWAITING_CURP)
            logger.info(f"CLABE expired for {order_id} — reset to AWAITING_CURP")

    async def handle_payment_refunded(self, transaction_id: str, event_type: str):
        """Handle payment refund/cancellation. CRITICAL if crypto released."""
        if not self.facilitapay:
            return
        tx_data = self.facilitapay.db.get_transaction(transaction_id)
        if not tx_data:
            return
        order_id = tx_data.get("pear_order_id")
        if not order_id:
            return
        order = self.tracker.get_order(order_id)
        if not order:
            return
        self.facilitapay.db.update_transaction_status(transaction_id, event_type)
        if order.state in (MXNOrderState.COMPLETED, MXNOrderState.RELEASING):
            self.tracker.log_audit(order_id, "FUNDS_AT_RISK",
                f"🚨 CRITICAL: {event_type} after crypto release!", "CRITICAL")
            logger.critical(f"🚨 FUNDS AT RISK: {order_id} — {event_type} after release!")
        self.tracker.transition(order_id, MXNOrderState.MANUAL_REVIEW)

    # ================================================================
    # Cleanup
    # ================================================================

    async def close(self):
        await self.binance.close()
        if self.facilitapay:
            await self.facilitapay.close()
