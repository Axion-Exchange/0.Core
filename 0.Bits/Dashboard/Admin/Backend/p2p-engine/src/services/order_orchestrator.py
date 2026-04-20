"""
ORDER ORCHESTRATOR
==================
Main polling loop that coordinates order processing across all exchanges.
Uses state manager for state tracking and clients for API calls.
"""

import logging
import os
import asyncio
import json
import random
from datetime import datetime
from typing import Any

from src.core.state_manager import (
    StateManager,
    ManagedOrder,
    OrderEvent,
    state_manager,
)
from src.core.types import OrderSide, OrderStatus, OrderState, UnifiedOrder, Currency
from src.core.registry import registry



class OrderOrchestrator:
    """
    Orchestrates order processing across all registered exchanges.
    
    Responsibilities:
    - Poll exchanges for new/updated orders
    - Trigger state transitions based on order changes
    - Trigger bank polling via the Januar Client
    - Trigger Chat Orchestrator for communication
    """
    
    def __init__(
        self,
        state: StateManager | None = None,
        poll_interval: float = 5.0,
        ad_rebalancer=None,
    ):
        self.state = state or state_manager
        self.poll_interval = poll_interval
        self._running = False
        self._last_poll: dict[str, datetime] = {}
        self._ad_rebalancer = ad_rebalancer

        # Exchange polling configuration (unified with Januar)
        self._exchange_poll_config = {
            "idle": 40.0,    # No active orders
            "active": 20.0,  # Active orders
        }
        
        # Configurable timeout: orders marked paid with no bank payment -> DELAYED
        self.delay_timeout_minutes = 30
        
        # Exchange robustness (Exponential backoff)
        self._error_counts: dict[str, int] = {}
        self._max_backoff = 300.0
        self._jitter_factor = 0.2
        self._last_poll_time = None  # FIX C8: Heartbeat tracking
        self._thank_you_sent: set[str] = set()  # Dedup: order IDs that got the completion message
        self._logger = logging.getLogger("orchestrator")
    
    # -------------------------------------------------------------------------
    # LIFECYCLE
    # -------------------------------------------------------------------------
    
    async def start(self) -> None:
        """Start the orchestrator polling loop."""
        from src.core.health import task_registry

        self._running = True
        self._consecutive_failures = 0
        _MAX_CONSECUTIVE_FAILURES = 10
        self._logger.info("Order Orchestrator started")
        
        # Sync DB with live exchange orders on startup
        await self._sync_with_exchange()
        
        while self._running:
            try:
                await self._poll_cycle()
                # P1-1: Update heartbeat on each successful poll
                task_registry.heartbeat("orchestrator")
                self._consecutive_failures = 0
            except Exception as e:
                import traceback
                self._consecutive_failures += 1
                self._logger.error(
                    "Orchestrator poll error (%d/%d): %s\n%s",
                    self._consecutive_failures,
                    _MAX_CONSECUTIVE_FAILURES,
                    e,
                    traceback.format_exc(),
                )
                task_registry.mark_error("orchestrator", str(e))
                if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                    self._logger.critical(
                        "Orchestrator exceeded %d consecutive failures — re-raising to supervisor",
                        _MAX_CONSECUTIVE_FAILURES,
                    )
                    raise
            
            # Use adaptive interval for exchange polling
            interval = self._get_exchange_poll_interval()
            await asyncio.sleep(interval)
    
    def stop(self) -> None:
        """Stop the orchestrator."""
        self._running = False
        self._logger.info("Order Orchestrator stopped")
    
    async def _sync_with_exchange(self) -> None:
        """
        INITIAL SYNC: Archive old DB, clear memory, import all live orders from exchange.
        
        This is called ONCE at startup. It treats the exchange as the source of truth.
        The old database is archived (not deleted) for reference.
        """
        from src.core.persistence import order_db
        
        self._logger.info("INITIAL SYNC: Rebuilding state from exchange...")
        
        # 1. Archive old database and clear in-memory state
        order_db.archive_and_reset()
        self.state.reset_in_memory()
        
        # 2. Fetch all live orders from each exchange
        for exchange in registry.all_exchange_apis():
            exchange_id = exchange.exchange_id.value
            
            try:
                # Fetch all active orders from exchange (pending, paid, appealed)
                pending = await exchange.get_orders(state=OrderState.AWAITING_PAYMENT)
                paid = await exchange.get_orders(state=OrderState.MARKED_AS_PAID)
                appealed = await exchange.get_orders(state=OrderState.APPEALED)
                live_orders = pending + paid + appealed
                
                self._logger.info("%s: Found %d live orders on exchange", exchange_id, len(live_orders))
                
                # 3. Import each order
                added_count = 0
                for order in live_orders:
                    try:
                        # COP SELL orders are managed exclusively by the COP handler.
                        # Importing them here causes race conditions (orchestrator calls
                        # mark_as_paid, COP handler tries releaseCoin → Binance 400).
                        if (order.fiat_currency == Currency.COP and order.side == OrderSide.SELL) or (order.fiat_currency == Currency.MXN and order.side == OrderSide.SELL):
                            self._logger.debug("   Skipping COP sell: %s (handled by COP handler)", order.external_id[-8:])
                            continue

                        # Hydrate: Get full details (real_name, payment methods, etc.)
                        hydrated = await exchange.get_order(order.external_id)
                        order_to_track = hydrated if hydrated else order
                        
                        # Track the order (adds to memory and DB)
                        managed = self.state.track_order(order_to_track)
                        added_count += 1
                        self._logger.info("   Imported: %s (%s %s)", order.external_id[-8:], order.fiat_amount, order.fiat_currency.value)
                        
                        # Process new order (trigger BUY payout, SELL matching, etc.)
                        try:
                            await self._handle_new_order(managed)
                        except Exception as e:
                            self._logger.warning("   Error processing imported %s: %s", order.external_id[-8:], e)
                    except Exception as e:
                        self._logger.warning("   Failed to import %s: %s", order.external_id[-8:], e)
                
                self._logger.info("%s: Imported %d/%d orders", exchange_id, added_count, len(live_orders))
                
            except Exception as e:
                self._logger.error("Error syncing %s: %s", exchange_id, e)
        
        self._logger.info("INITIAL SYNC COMPLETE: %d active orders tracked", len(self.state.get_active_orders()))

    
    # -------------------------------------------------------------------------
    # POLLING LOGIC
    # -------------------------------------------------------------------------
    
    async def _poll_cycle(self) -> None:
        """
        Run one poll cycle.
        1. Polls Exchanges for Order Status.
        2. Triggers the Januar Client's smart poll.
        3. Reconciles pending mark_paid retries (P0-A).
        """
        # SEQUENTIAL EXECUTION to prevent race conditions
        # 1. Update from Exchange (get fresh state)
        await self._poll_all_exchanges()
        
        # 2. Match Payments (using fresh state)
        januar_client = registry.get_bank("januar")
        if januar_client:
            await januar_client.run_smart_poll()
        
        # Check for orders that should be marked as DELAYED
        self._check_payment_timeouts()
        
        # P0-A: Retry any pending mark_paids from previous cycles
        await self._reconcile_pending_mark_paids()
        
        # FIX C8: Update heartbeat timestamp
        self._last_poll_time = datetime.utcnow()
    
    async def _poll_all_exchanges(self) -> None:
        """Poll all exchanges with individual error handling and backoff."""
        for exchange in registry.all_exchange_apis():
            exchange_id = exchange.exchange_id.value
            
            # Check backoff
            backoff = self._get_backoff_delay(exchange_id)
            if backoff > 0:
                last = self._last_poll.get(exchange_id)
                if last and (datetime.now() - last).total_seconds() < backoff:
                    continue
            
            try:
                await self._poll_exchange(exchange_id)
                self._record_success(exchange_id)
                self._last_poll[exchange_id] = datetime.now()
            except Exception as e:
                self._record_error(exchange_id)
                import traceback
                self._logger.error("Error polling %s: %s\n%s", exchange.display_name, e, traceback.format_exc())

    async def _poll_exchange(self, exchange_id: str) -> None:
        """
        CONTINUOUS RECONCILIATION: Poll exchange and sync state on every cycle.
        
        Uses a 3-step pattern:
        1. IMPORT: Orders on exchange but NOT in our tracker → track them
        2. UPDATE: Orders in both → update status if changed
        3. PRUNE: Orders in our tracker but NOT on exchange → mark completed
        """
        client = registry.get_exchange_api(exchange_id)
        if not client:
            return
        
        # 1. Get all live orders from the exchange (the ONLY source of truth)
        all_orders = []
        for trade_type in ["SELL", "BUY"]:
            for order_state in [OrderState.AWAITING_PAYMENT, OrderState.MARKED_AS_PAID, OrderState.APPEALED]:
                orders = await client.get_orders(trade_type=trade_type, state=order_state)
                all_orders.extend(orders)
        
        live_ids = {o.external_id for o in all_orders}
        
        # 2. Get all orders we are currently tracking for this exchange
        tracked_orders = [
            m for m in self.state.get_active_orders() 
            if m.order.exchange.value == exchange_id
        ]
        tracked_ids = {m.order.external_id for m in tracked_orders}
        
        # Log summary
        self._logger.info("%s: Live=%d | Tracked=%d", exchange_id, len(live_ids), len(tracked_ids))
        
        # === STEP 1: IMPORT ===
        # Orders on exchange but NOT in our tracker
        for order in all_orders:
            if order.external_id not in tracked_ids:
                # COP/MXN SELL orders: skip — managed exclusively by their handlers
                if (order.fiat_currency == Currency.COP and order.side == OrderSide.SELL) or (order.fiat_currency == Currency.MXN and order.side == OrderSide.SELL):
                    continue

                self._logger.info("   IMPORTING missing: %s", order.external_id[-8:])
                try:
                    # Hydrate for full details
                    hydrated = await client.get_order(order.external_id)
                    order_to_track = hydrated if hydrated else order
                    
                    managed = self.state.track_order(order_to_track)
                    await self._handle_new_order(managed)
                except Exception as e:
                    self._logger.warning("   Import failed for %s: %s", order.external_id[-8:], e)
        
        # === STEP 2: UPDATE ===
        # Orders in both → check for status changes
        for order in all_orders:
            managed = self.state.get_by_external(order.external_id)
            if managed:
                await self._handle_order_update(managed, order)
                # Fetch new chat messages
                await self._fetch_new_chat_messages(client, managed)
        
        # === STEP 3: PRUNE (SAFE — verify individually before completing) ===
        # Orders in our tracker but NOT returned by bulk poll.
        # FIX A3: Do NOT blindly force-complete. Query each order individually first.
        for managed in tracked_orders:
            if managed.order.external_id not in live_ids:
                terminal_states = {OrderState.COMPLETED, OrderState.CANCELLED, OrderState.REFUNDED, OrderState.EXPIRED}
                if managed.state not in terminal_states:
                    # Verify the order's actual status before pruning
                    try:
                        verified_order = await client.get_order(managed.order.external_id)
                        if verified_order:
                            exchange_status = verified_order.status
                            if exchange_status == OrderState.COMPLETED:
                                self._logger.info("   PRUNE VERIFIED: %s confirmed COMPLETED on exchange", managed.order.external_id[-8:])
                                self.state.transition(managed.id, OrderState.COMPLETED, "exchange_verified_completed")
                                self._trigger_sell_topup(managed)  # AUDIT FIX: prune path was missing topup trigger
                            elif exchange_status == OrderState.CANCELLED:
                                self._logger.info("   PRUNE VERIFIED: %s confirmed CANCELLED on exchange", managed.order.external_id[-8:])
                                self.state.transition(managed.id, OrderState.CANCELLED, "exchange_verified_cancelled")
                            elif exchange_status == OrderState.EXPIRED:
                                self._logger.info("   PRUNE VERIFIED: %s confirmed EXPIRED on exchange", managed.order.external_id[-8:])
                                self.state.transition(managed.id, OrderState.EXPIRED, "exchange_verified_expired")
                            else:
                                # Order is still active but wasn't in our bulk poll (pagination miss)
                                self._logger.warning("   PRUNE SKIPPED: %s is still %s on exchange — pagination miss", managed.order.external_id[-8:], exchange_status.value)
                        else:
                            # get_order returned None — API error or order truly gone
                            self._logger.warning("   PRUNE UNVERIFIED: %s — get_order returned None, marking COMPLETED with warning", managed.order.external_id[-8:])
                            self.state.transition(managed.id, OrderState.COMPLETED, "exchange_sync_unverified_completed")
                            self._trigger_sell_topup(managed)  # AUDIT FIX: prune path was missing topup trigger
                    except Exception as e:
                        self._logger.error("   PRUNE ERROR: Could not verify %s: %s — skipping prune", managed.order.external_id[-8:], e)


    async def _send_chat_messages(
        self, 
        client: Any, 
        order_id: str, 
        messages: list[str]
    ) -> None:
        """Send chat messages to the exchange."""
        for msg in messages:
            try:
                result = await client.send_chat_message(order_id, msg)
                if result:
                    self._logger.info("Sent: %s...", msg[:50])
                else:
                    self._logger.warning("Failed to send message to %s", order_id)
            except Exception as e:
                self._logger.error("Chat send error: %s", e)

    async def _fetch_new_chat_messages(
        self, 
        client: Any, 
        managed: ManagedOrder
    ) -> list[str]:
        """Fetch new chat messages from counterparty and sync history to memory."""
        try:
            # Fetch generic messages (includes system messages)
            messages = await client.get_chat_messages(managed.order.external_id)
            self._logger.debug("CHAT: Fetched %d messages for %s", len(messages), managed.order.external_id)
            
            from src.core.types import MessageSender
            
            # Extract real name from system/hidden messages
            for msg in messages:
                if msg.content.strip().startswith("{") and "realName" in msg.content:
                    self._logger.debug("CHAT JSON found: %s...", msg.content[:50])
                    try:
                        data = json.loads(msg.content)
                        if "realName" in data and data["realName"]:
                            self._logger.debug("CHAT: Extracting realName: %s", data['realName'])
                            self.state.update_counterparty_real_name(managed.id, data["realName"])
                    except Exception as e:
                        self._logger.debug("CHAT JSON parse error: %s", e)
            
            # Track seen message IDs to avoid processing duplicates
            seen_key = f"_seen_msgs_{managed.id}"
            if not hasattr(self, '_seen_messages'):
                self._seen_messages = {}
            seen = self._seen_messages.get(seen_key, set())
            
            new_messages = []
            for msg in messages:
                # Only process counterparty messages we haven't seen
                if msg.sender == MessageSender.COUNTERPARTY and msg.id not in seen:
                    seen.add(msg.id)
                    new_messages.append(msg.content)
                    self._logger.info("New message from %s: %s...", managed.order.counterparty.name, msg.content[:50])
            
            self._seen_messages[seen_key] = seen
            return new_messages
            
        except Exception as e:
            self._logger.warning("Error fetching chat messages: %s", e)
            return []

    # -------------------------------------------------------------------------
    # ORDER HANDLERS
    # -------------------------------------------------------------------------
    
    async def _handle_new_order(self, managed: ManagedOrder) -> None:
        """Handle a newly discovered order."""
        order = managed.order
        self._logger.info("New %s order: %s (%s %s)", order.side.value, order.external_id, order.fiat_amount, order.fiat_currency.value)
        
        # COP SELL orders: managed exclusively by COP handler — do not process here
        if order.fiat_currency == Currency.COP and order.side == OrderSide.SELL:
            self._logger.info("   COP sell order — skipping (handled by COP handler)")
            return

        # MXN SELL orders: managed exclusively by MXN handler
        if order.fiat_currency == Currency.MXN and order.side == OrderSide.SELL:
            self._logger.info("   MXN sell order — skipping (handled by MXN handler)")
            return

        # BUY orders: fetch payment details, screen, prepare + auto-execute payout
        if order.side == OrderSide.BUY:
            await self._handle_new_buy_order(managed)
            return
        
        # SELL: If it enters as PAID, trigger payment check
        if order.status == OrderStatus.MARKED_AS_PAID:
            await self._handle_payment_received(managed)

    async def _handle_order_update(self, managed: ManagedOrder, new_order_data: Any) -> None:
        """Handle an update to an existing order."""
        old_status = managed.order.status
        new_status = new_order_data.status
        
        if old_status == new_status:
            # FIX: If we are internally DELAYED but external is PAID, we must re-process
            # (This happens when an order times out locally, but then we poll and see it's still PAID active)
            if managed.state == OrderState.DELAYED and new_status == OrderState.MARKED_AS_PAID:
                # Keep it DELAYED, do not re-process as new payment
                return
            else:
                return
        
        managed.order = new_order_data
        managed.updated_at = datetime.now()
        self._logger.info("Order %s status: %s → %s", managed.order.external_id, old_status.value, new_status.value)
        
        # Map exchange statuses to internal states
        STATUS_TO_STATE_MAP: dict[OrderState, tuple[OrderState, str]] = {
            OrderState.COMPLETED: (OrderState.COMPLETED, "exchange_completed"),
            OrderState.CANCELLED: (OrderState.CANCELLED, "exchange_cancelled"),
            OrderState.APPEALED: (OrderState.APPEALED, "exchange_appealed"),
            OrderState.EXPIRED: (OrderState.EXPIRED, "exchange_expired"),
        }
        
        if new_status == OrderState.MARKED_AS_PAID:
            # BUY orders: we marked paid ourselves, don't trigger sell-side payment matching
            if managed.order.side == OrderSide.BUY:
                self.state.transition(managed.id, OrderState.MARKED_AS_PAID, "buy_order_marked_paid")
            elif managed.order.fiat_currency == Currency.COP:
                # COP sell orders: managed by COP handler, trigger immediate FP check
                self._logger.info("COP sell %s marked paid — triggering urgent FP check", managed.order.external_id[-8:])
                try:
                    from src.fiat.cop.cop_handler import request_urgent_fp_check
                    request_urgent_fp_check(managed.order.external_id)
                except ImportError:
                    pass
            elif managed.order.fiat_currency == Currency.MXN:
                # MXN sell orders: trigger immediate FP check
                self._logger.info("MXN sell %s marked paid — triggering urgent FP check", managed.order.external_id[-8:])
                try:
                    from src.fiat.mxn.mxn_handler import request_urgent_fp_check as request_mxn_fp_check
                    request_mxn_fp_check(managed.order.external_id)
                except ImportError:
                    pass
            else:
                await self._handle_payment_received(managed)
        elif new_status in STATUS_TO_STATE_MAP:
            target_state, reason = STATUS_TO_STATE_MAP[new_status]
            
            # If agent is processing, ONLY allow terminal transitions (Completed/Cancelled)
            # Do NOT allow auto-re-transitions to other states
            is_agent_active = managed.state in [OrderState.AGENT_REQUIRED, OrderState.AGENT_PROCESSING]
            is_terminal = target_state in [OrderState.COMPLETED, OrderState.CANCELLED, OrderState.EXPIRED]
            
            if is_agent_active and not is_terminal:
                return

            self.state.transition(managed.id, target_state, reason)

            # ── SELL AD AUTO-TOPUP ──
            # When a BUY order completes (seller released USDT to us),
            # trigger SELL ad topup. Uses shared helper for DRY.
            if target_state == OrderState.COMPLETED:
                self._trigger_sell_topup(managed)
                # Send Trustpilot thank-you for BUY orders (SELL sends in release_crypto)
                if managed.order.side == OrderSide.BUY:
                    try:
                        buy_client = registry.get_exchange_api(managed.order.exchange.value)
                        if buy_client:
                            asyncio.create_task(self._send_completion_message(buy_client, managed))
                    except Exception as e:
                        self._logger.warning("Failed to send BUY completion message: %s", e)

    def _trigger_sell_topup(self, managed: ManagedOrder) -> None:
        """
        Fire-and-forget SELL ad topup if this is a completed BUY order.
        Safe to call from any completion path — the rebalancer's own guards
        (DB at-most-once, sequential lock) handle dedup.
        """
        if (
            managed.order.side == OrderSide.BUY
            and self._ad_rebalancer is not None
        ):
            usdt_amount = float(managed.order.crypto_amount or 0)
            if usdt_amount > 0:
                task = asyncio.create_task(
                    self._ad_rebalancer.on_buy_order_completed(
                        managed.order.external_id, usdt_amount
                    )
                )
                # AUDIT FIX: Log exceptions from fire-and-forget tasks
                # Without this, exceptions would be silently garbage-collected
                task.add_done_callback(self._topup_task_done)
                self._logger.info(
                    "SELL topup task created for BUY order %s (+%.2f USDT)",
                    managed.order.external_id[-8:], usdt_amount,
                )

    @staticmethod
    def _topup_task_done(task: asyncio.Task) -> None:
        """Log exceptions from fire-and-forget SELL topup tasks."""
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            import logging
            logging.getLogger(__name__).error(
                "SELL topup task failed: %s", exc, exc_info=exc,
            )

    async def _send_completion_message(self, client: Any, managed: ManagedOrder) -> None:
        """
        Send a thank-you message with Trustpilot link after order completion.
        
        SAFETY:
        - In-memory dedup set prevents double-sends within same process lifetime
        - Completed orders are NOT re-imported on restart (only active orders are)
        - Single attempt, no retries — a missed thank-you is better than spam
        """
        from src.core.persistence import order_db
        order_id = managed.order.external_id
        
        # Dedup check — persistent in DB (survives restarts)
        if order_db.is_trustpilot_sent_by_ext_id(order_id):
            self._logger.debug("Trustpilot already sent for %s (DB dedup)", order_id[-8:])
            return
        
        # Select language based on fiat currency
        if managed.order.fiat_currency == Currency.COP:
            message = (
                "\U0001f389 ¡Transacción completada! Gracias por operar con nosotros.\n"
                "Ayuda a otros traders a encontrarnos — déjanos una reseña rápida:\n"
                "⭐ https://trustpilot.com/review/axionexchange.io\n"
                "¡Tu apoyo significa mucho! \U0001f499"
            )
        elif managed.order.fiat_currency == Currency.MXN:
            message = (
                "\U0001f389 Â¡TransacciÃ³n completada! Gracias por operar con nosotros.\n"
                "Ayuda a otros traders a encontrarnos â dÃ©janos una reseÃ±a rÃ¡pida:\n"
                "â­ https://trustpilot.com/review/axionexchange.io\n"
                "Â¡Tu apoyo significa mucho! \U0001f499"
            )
        elif managed.order.fiat_currency == Currency.BRL:
            message = (
                "\U0001f389 Transação concluída! Obrigado por negociar conosco.\n"
                "Ajude outros traders a nos encontrar — deixe uma avaliação rápida:\n"
                "⭐ https://trustpilot.com/review/axionexchange.io\n"
                "Seu apoio significa muito! \U0001f499"
            )
        else:
            message = (
                "\U0001f389 Transaction complete! Thank you for trading with us.\n"
                "Help other traders find us — leave a quick review:\n"
                "⭐ https://trustpilot.com/review/axionexchange.io\n"
                "Your support means a lot! \U0001f499"
            )
        
        try:
            await client.send_chat_message(order_id, message)
            order_db.mark_trustpilot_sent_by_ext_id(order_id)
            self._logger.info("Sent thank-you message for order %s (persisted)", order_id[-8:])
        except Exception as e:
            # Don't retry — missed thank-you is harmless, spam is not
            self._logger.warning("Failed to send thank-you for %s: %s", order_id[-8:], e)

    async def _handle_payment_received(self, managed: ManagedOrder) -> None:
        """
        Handle when buyer marks order as paid (SELL orders only).
        Now calls the Januar Client directly for urgent checks.
        """
        # SKIP if under agent review
        if managed.state in [OrderState.AGENT_REQUIRED, OrderState.AGENT_PROCESSING]:
            return

        # ANTI-SPAM: Rate limit per counterparty — max 3 active orders at a time
        # Prevents IMRAN996-style rapid-fire order spam (21 orders in minutes)
        cp_name = managed.order.counterparty.name if managed.order.counterparty else None
        if cp_name:
            active_orders = [
                m for m in self.state.get_all_managed()
                if m.order.counterparty and m.order.counterparty.name == cp_name
                and m.state not in (OrderState.COMPLETED, OrderState.CANCELLED, OrderState.EXPIRED)
                and m.id != managed.id
            ]
            if len(active_orders) >= 3:
                self._logger.warning(
                    "🚨 RATE LIMIT: %s has %d active orders — delaying %s (anti-spam)",
                    cp_name, len(active_orders), managed.order.external_id[-8:]
                )
                self.state.flag_for_review(
                    managed.id,
                    f"Rate-limited: {cp_name} has {len(active_orders)} active orders — possible spam"
                )
                return

        # RE-HYDRATE if real_name is missing (happens when imported during awaiting_payment)
        if not managed.order.counterparty.real_name:
            try:
                client = registry.get_exchange_api(managed.order.exchange.value)
                if client:
                    hydrated = await client.get_order(managed.order.external_id)
                    if hydrated and hydrated.counterparty.real_name:
                        managed.order = hydrated
                        self._logger.info("Re-hydrated order %s: real_name=%s", managed.order.external_id[-8:], hydrated.counterparty.real_name)
            except Exception as e:
                self._logger.warning("Re-hydration failed for %s: %s", managed.order.external_id[-8:], e)

        if managed.paid_at is None:
            managed.paid_at = datetime.now()
        self.state.transition(managed.id, OrderState.MARKED_AS_PAID, "buyer_marked_paid")
        self._logger.info("Payment marked for order %s", managed.order.external_id)

    async def _extract_name_from_chat(self, managed: ManagedOrder) -> str | None:
        """Extract a Latin-character name from chat messages as payout name fallback.

        Reads counterparty messages and looks for text that looks like a person's name
        (at least 2 words, Latin characters only). Skips JSON system messages and
        IBAN-only messages.

        Returns the sanitized name if found, None otherwise.
        """
        import re
        from src.services.name_sanitizer import sanitize_sepa_name

        client = registry.get_exchange_api(managed.order.exchange.value)
        if not client:
            return None

        try:
            messages = await client.get_chat_messages(managed.order.external_id)
        except Exception as e:
            self._logger.warning("Chat fallback: could not read chat for %s: %s", managed.order.external_id[-8:], e)
            return None

        if not messages:
            return None

        from src.core.types import MessageSender

        # Collect counterparty text messages (skip JSON system messages)
        candidate_names: list[str] = []
        for msg in messages:
            if msg.sender != MessageSender.COUNTERPARTY:
                continue
            text = msg.content.strip()
            # Skip JSON system messages
            if text.startswith("{"):
                continue
            # Skip messages that are only an IBAN (starts with 2 letters + digits)
            if re.match(r"^[A-Z]{2}\d{2}", text.replace(" ", "").upper()):
                # But check if it also has a name before the IBAN
                parts = text.split(",")
                for part in parts:
                    part = part.strip()
                    # Skip parts that look like IBAN
                    if re.match(r"^(IBAN:?\s*)?[A-Z]{2}\d{2}", part.replace(" ", "").upper()):
                        continue
                    # This part might be a name
                    sanitized = sanitize_sepa_name(part)
                    words = sanitized.split()
                    if len(words) >= 2 and all(len(w) >= 2 for w in words):
                        candidate_names.append(sanitized)
                continue

            # Check if this message contains "IBAN:" with a name
            if "IBAN" in text.upper():
                # Split on "IBAN" and take the part before it as potential name
                before_iban = re.split(r"[,;]?\s*IBAN\s*:?\s*", text, flags=re.IGNORECASE)[0].strip()
                if before_iban:
                    sanitized = sanitize_sepa_name(before_iban)
                    words = sanitized.split()
                    if len(words) >= 2 and all(len(w) >= 2 for w in words):
                        candidate_names.append(sanitized)
                continue

            # Regular text message — check if it looks like a name
            sanitized = sanitize_sepa_name(text)
            words = sanitized.split()
            # A name should have at least 2 words, each at least 2 chars, and be mostly letters
            if len(words) >= 2 and all(len(w) >= 2 and w.isalpha() for w in words):
                candidate_names.append(sanitized)

        if candidate_names:
            # Prefer the first name-like message (usually the first one they send)
            chosen = candidate_names[0]
            self._logger.info("Chat fallback: extracted name '%s' from %d candidates for %s",
                            chosen, len(candidate_names), managed.order.external_id[-8:])
            return chosen

        self._logger.warning("Chat fallback: no name candidates found in chat for %s", managed.order.external_id[-8:])
        return None

    # =========================================================================
    # BUY ORDER FLOW
    # =========================================================================



    async def _extract_iban_from_chat(self, managed) -> str | None:
        """Extract an IBAN from counterparty chat messages.

        Scans all counterparty messages for a pattern matching an IBAN:
        2 uppercase letters + 2 digits + 4-30 alphanumeric chars.
        Skips JSON system messages.

        Returns the first valid IBAN found (normalized, no spaces), or None.
        """
        import re
        client = registry.get_exchange_api(managed.order.exchange.value)
        if not client:
            return None

        try:
            messages = await client.get_chat_messages(managed.order.external_id)
        except Exception as e:
            self._logger.warning("Chat IBAN fallback: could not read chat for %s: %s",
                                 managed.order.external_id[-8:], e)
            return None

        if not messages:
            return None

        from src.core.types import MessageSender

        for msg in messages:
            if msg.sender != MessageSender.COUNTERPARTY:
                continue
            text = msg.content.strip()
            # Skip JSON system messages
            if text.startswith("{"):
                continue

            # Normalize: remove spaces and dashes for matching
            normalized = text.replace(" ", "").replace("-", "").upper()

            # Look for IBAN pattern anywhere in the message
            match = re.search(r"[A-Z]{2}\d{2}[A-Z0-9]{4,30}", normalized)
            if match:
                iban = match.group(0)
                self._logger.info("Chat IBAN fallback: found IBAN %s*** in chat for %s",
                                  iban[:4], managed.order.external_id[-8:])
                return iban

        self._logger.info("Chat IBAN fallback: no IBAN found in chat for %s",
                          managed.order.external_id[-8:])
        return None

    def _dump_buy_debug(self, managed, payment_info, extra=None):
        """Save full BUY order details to disk for debugging."""
        import json, os
        from datetime import datetime, timezone
        debug_dir = os.path.join(os.getenv("DATA_DIR", "/data/PearV2/data"), "debug_profiles")
        os.makedirs(debug_dir, exist_ok=True)
        
        order = managed.order
        ext_id = order.external_id
        
        # Collect everything
        debug = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "order_id": managed.id,
            "external_id": ext_id,
            "side": str(order.side),
            "fiat_amount": order.fiat_amount,
            "fiat_currency": str(order.fiat_currency),
            "crypto_amount": order.crypto_amount,
            "crypto_asset": str(order.crypto_asset),
            "price": order.price,
            "counterparty": {
                "name": order.counterparty.name if order.counterparty else None,
                "real_name": order.counterparty.real_name if order.counterparty else None,
            },
            "payment_method": order.payment_method,
            "payment_info": payment_info,
            "raw_order": order.raw if hasattr(order, "raw") else None,
        }
        if extra:
            debug["extra"] = extra
        
        filename = f"{ext_id[-12:]}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(debug_dir, filename)
        try:
            with open(filepath, "w") as f:
                json.dump(debug, f, default=str, indent=2)
            self._logger.info("   Saved debug profile: %s", filename)
        except Exception as e:
            self._logger.warning("   Failed to save debug profile: %s", e)

    async def _handle_new_buy_order(self, managed: ManagedOrder) -> None:
        """
        Handle a newly discovered BUY order.
        
        Flow:
        1. Fetch seller's payment details (IBAN, name) from Binance
        2. Screen IBAN against sanctions / blocked countries
        3. [FUTURE] Ask seller for bank name via chat, screen against banned banks
        4. Prepare payout payload for Januar
        5. Auto-execute payout
        """
        order = managed.order
        ext_id = order.external_id
        self._logger.info("Processing BUY order: %s (%s %s)", ext_id[-8:], order.fiat_amount, order.fiat_currency.value)

        # Currency-aware routing: only EUR buy orders go through Januar payout
        if order.fiat_currency == Currency.BRL:
            self._logger.info("   BRL buy order detected — PIX payout not yet implemented, skipping auto-payout")
            return
        elif order.fiat_currency == Currency.COP:
            self._logger.info("   COP buy order detected — handled by COP handler, skipping")
            return
        elif order.fiat_currency == Currency.MXN:
            self._logger.info("   MXN buy order detected — handled by MXN handler, skipping")
            return
        elif order.fiat_currency != Currency.EUR:
            self._logger.warning("   Unsupported currency %s for auto-payout, skipping", order.fiat_currency.value)
            return

        # EUR flow: Fetch seller's payment details from Binance
        client = registry.get_exchange_api(order.exchange.value)
        if not client:
            self._logger.warning("   No client for %s", order.exchange.value)
            return

        payment_info = await client.get_payment_details(ext_id)
        if not payment_info:
            self._logger.warning("   Could not fetch payment details for %s", ext_id[-8:])
            self._dump_buy_debug(managed, None, extra={"reason": "no_payment_info"})
            return

        # Check for error (no IBAN found)
        if payment_info.get("error"):
            self._logger.warning("   %s for %s", payment_info['error'], ext_id[-8:])
            self._logger.warning("   Raw methods: %s", payment_info.get('raw_methods', []))
            self._dump_buy_debug(managed, payment_info, extra={"reason": "no_iban_in_profile"})

            # ── FALLBACK: Spawn background task (non-blocking) ──
            self._logger.info("   Chat IBAN fallback: spawning background task for %s", ext_id[-8:])
            if not hasattr(self, '_iban_tasks'):
                self._iban_tasks = {}
            # Don't spawn duplicate tasks for the same order
            if ext_id not in self._iban_tasks or self._iban_tasks[ext_id].done():
                task = asyncio.create_task(
                    self._iban_chat_fallback_task(managed, client, payment_info)
                )
                self._iban_tasks[ext_id] = task
            return  # Return immediately — don't block the poll loop
        iban = payment_info.get("iban", "").replace(" ", "").upper()
        account_name_raw = payment_info.get("account_name")
        bank_name = payment_info.get("bank_name")
        screening = payment_info.get("screening_result")

        # Sanitize name for SEPA (transliterate Cyrillic, strip accents)
        from src.services.name_sanitizer import sanitize_sepa_name, has_non_latin
        account_name = account_name_raw
        if account_name_raw and has_non_latin(account_name_raw):
            account_name = sanitize_sepa_name(account_name_raw)
            self._logger.info("   Name sanitized: '%s' → '%s'", account_name_raw, account_name)

        self._logger.info("   Seller details: name=%s, IBAN=%s***, bank=%s", account_name, iban[:4], bank_name)

        # 2. IBAN Sanctions Screening (already done in get_payment_details but check result)
        if screening and screening.is_blocked:
            self._logger.warning("   IBAN BLOCKED: %s", screening.reason)
            self.state.set_error(managed.id, f"Payout blocked: {screening.reason}")
            self._dump_buy_debug(managed, payment_info, extra={"reason": "iban_blocked", "screening_reason": screening.reason})
            # Notify seller via chat if non-SEPA
            if "Non-SEPA" in str(screening.reason):
                try:
                    await client.send_chat_message(
                        ext_id,
                        "Sorry, we can only send payments to SEPA-zone bank accounts (EU/EEA). "
                        "Your IBAN appears to be from a non-SEPA country. "
                        "Please provide a SEPA IBAN if you have one."
                    )
                    self._logger.info("   Sent non-SEPA notification to seller for %s", ext_id[-8:])
                except Exception as e:
                    self._logger.warning("   Failed to send non-SEPA chat message: %s", e)
            return

        # 3. [FUTURE] Bank name screening via chat
        # When the chatter is ready, this is where we would:
        #   - Send a chat message asking the seller for their bank name
        #   - Parse the response
        #   - Run through is_bank_banned() from iban_screener
        #   - Block if banned
        #
        # from src.services.iban_screener import is_bank_banned
        # if bank_name and is_bank_banned(bank_name):
        #     print(f"   🚫 BANK BANNED: {bank_name}")
        #     self.state.set_error(managed.id, f"Payout blocked: banned bank {bank_name}")
        #     return
        #
        # If no bank_name available yet, the chatter would:
        #   1. await self._request_bank_name_via_chat(managed)
        #   2. Parse response and validate
        #   3. Continue or block

        # 4. Prepare payout payload for Januar
        payout_payload = {
            "amount": order.fiat_amount,
            "currency": order.fiat_currency.value,
            "recipient_name": account_name,
            "recipient_account": iban,
            "reference": f"{order.internal_order_number}",
            "internal_note": f"Buy order payout: {ext_id}",
            # Metadata for tracking
            "bank_name": bank_name,
            "screening_passed": True,
            "prepared_at": datetime.now().isoformat(),
        }

        managed.payout_details = payout_payload
        self.state._persist(managed)

        self._dump_buy_debug(managed, payment_info, extra={"reason": "payout_prepared", "payout_payload": payout_payload})
        self._logger.info("   Payout payload ready for %s: %s %s to %s, IBAN=%s***, ref=%s",
                          ext_id[-8:], payout_payload['amount'], payout_payload['currency'],
                          account_name, iban[:4], payout_payload['reference'])

        # 5. Auto-execute payout
        await self.execute_buy_payout(managed.id)

    async def _iban_chat_fallback_task(self, managed, client, payment_info) -> None:
        """Background task: poll Binance chat for seller's IBAN. Non-blocking."""
        import time as _time
        ext_id = managed.order.external_id
        order = managed.order
        iban_request_count = 0
        last_iban_request_time = 0
        poll_count = 0
        chat_iban = None

        self._logger.info("   IBAN background task started for %s", ext_id[-8:])

        try:
            while True:
                poll_count += 1

                # 1. Check if order is still active
                try:
                    live_order = await client.get_order(ext_id)
                    if live_order:
                        live_status = str(live_order.status).upper()
                        if "CANCEL" in live_status or "COMPLET" in live_status or "EXPIRED" in live_status:
                            self._logger.info("   IBAN task: order %s is %s — stopping", ext_id[-8:], live_status)
                            break
                except Exception as e:
                    self._logger.warning("   IBAN task: status check error: %s", e)

                # 2. Try to extract IBAN from chat
                chat_iban = await self._extract_iban_from_chat(managed)
                if chat_iban:
                    self._logger.info("   IBAN task: found IBAN after %d polls for %s", poll_count, ext_id[-8:])
                    break

                # 3. Send IBAN request message (max 2, 5 min apart)
                now = _time.time()
                if iban_request_count < 2:
                    time_since_last = now - last_iban_request_time
                    if iban_request_count == 0 or time_since_last >= 300:
                        try:
                            await client.send_chat_message(
                                ext_id,
                                "Could you please send your IBAN details? We are transferring now \U0001f3e6"
                            )
                            iban_request_count += 1
                            last_iban_request_time = now
                            self._logger.info("   IBAN request sent (%d/2) for %s", iban_request_count, ext_id[-8:])
                        except Exception as e:
                            self._logger.warning("   Failed to send IBAN request: %s", e)

                # 4. Wait 30s before next poll
                self._logger.info("   Chat IBAN fallback: no IBAN found in chat for %s", ext_id[-8:])
                await asyncio.sleep(30)

            if not chat_iban:
                self._logger.warning("   IBAN task: order ended without IBAN for %s", ext_id[-8:])
                self._dump_buy_debug(managed, payment_info, extra={"reason": "no_iban_order_ended", "polls": poll_count})
                return

            # Got IBAN — screen and prepare payout
            iban = chat_iban
            account_name_raw = (order.counterparty.real_name
                                or order.counterparty.name
                                or "Unknown")
            self._logger.info("   IBAN task SUCCESS: IBAN=%s***, name=%s for %s",
                              iban[:4], account_name_raw, ext_id[-8:])

            from src.services.iban_screener import screen_iban as _screen_iban
            screening = _screen_iban(iban)
            if screening.is_blocked:
                self._logger.warning("   Chat IBAN BLOCKED: %s", screening.reason)
                self.state.set_error(managed.id, f"Payout blocked: {screening.reason}")
                self._dump_buy_debug(managed, payment_info, extra={"reason": "chat_iban_blocked", "iban": iban[:4]})
                if "Non-SEPA" in str(screening.reason):
                    try:
                        await client.send_chat_message(
                            ext_id,
                            "Sorry, we can only send payments to SEPA-zone bank accounts (EU/EEA). "
                            "Your IBAN appears to be from a non-SEPA country. "
                            "Please provide a SEPA IBAN if you have one."
                        )
                    except Exception:
                        pass
                return

            from src.services.name_sanitizer import sanitize_sepa_name, has_non_latin
            account_name = account_name_raw
            if account_name_raw and has_non_latin(account_name_raw):
                account_name = sanitize_sepa_name(account_name_raw)
                self._logger.info("   Name sanitized: '%s' -> '%s'", account_name_raw, account_name)

            bank_name = screening.bank_name if screening else None

            payout_payload = {
                "amount": str(order.fiat_amount),
                "currency": order.fiat_currency.value,
                "recipient_name": account_name,
                "recipient_account": iban,
                "reference": f"{order.internal_order_number}",
                "internal_note": f"Buy order payout (chat IBAN fallback): {ext_id}",
                "bank_name": bank_name,
                "screening_passed": True,
                "prepared_at": datetime.now().isoformat(),
                "iban_source": "chat",
            }

            managed.payout_details = payout_payload
            self.state._persist(managed)

            self._logger.info("   Payout ready (IBAN task) for %s: %s %s to %s, IBAN=%s***",
                              ext_id[-8:], payout_payload['amount'], payout_payload['currency'],
                              account_name, iban[:4])

            await self.execute_buy_payout(managed.id)

        except asyncio.CancelledError:
            self._logger.info("   IBAN task cancelled for %s", ext_id[-8:])
        except Exception as e:
            self._logger.error("   IBAN task error for %s: %s", ext_id[-8:], e)
            import traceback
            traceback.print_exc()

    async def execute_buy_payout(self, order_id: str) -> bool:
        """Execute a prepared buy-order payout with per-order locking to prevent double-send.
        
        Flow:
        1. Send EUR to seller via Januar payout
        2. Mark order as paid on Binance
        3. Record timestamps
        4. Transition state to MARKED_AS_PAID
        
        After this, _check_payment_timeouts() monitors for seller release.
        If seller doesn't release in 30 mins → DELAYED.
        When seller releases, exchange poll detects COMPLETED.
        """
        # FIX: Per-order lock prevents double-payout race condition
        lock = self.state.get_lock(order_id)
        async with lock:
            return await self._execute_buy_payout_locked(order_id)

    async def _execute_buy_payout_locked(self, order_id: str) -> bool:
        """Internal payout logic — must be called under per-order lock.
        
        Guards (in order):
        1. payout_details exist
        2. In-memory payout_sent_at check
        3. P0-B: IBAN screening enforcement
        4. Exchange re-verification
        5. P0-5: DB-level at-most-once claim
        6. Januar replay_id server-side dedup
        
        After payout success:
        - P0-A: Inline mark_paid retries (3 attempts, 2s backoff)
        - If mark_paid fails → mark_paid_pending for reconciliation
        """
        managed = self.state.get_order(order_id)
        if not managed:
            self._logger.error("Order %s not found", order_id)
            return False

        if not managed.payout_details:
            self._logger.error("No payout payload prepared for %s", order_id)
            return False

        # Guard: prevent duplicate payouts if already sent
        if managed.payout_sent_at:
            self._logger.warning("Payout already sent at %s for %s — skipping to prevent duplicate", managed.payout_sent_at, order_id)
            return False

        # P0-B: Enforce IBAN screening before ANY payout (manual or auto)
        from src.services.iban_screener import screen_iban
        iban = managed.payout_details.get("recipient_account", "")
        if iban:
            screening = screen_iban(iban)
            if screening.is_blocked:
                self._logger.critical(
                    "P0-B PAYOUT BLOCKED: IBAN %s*** is %s — refusing to send EUR",
                    iban[:4], screening.reason,
                )
                self.state.set_error(order_id, f"Payout blocked by screening: {screening.reason}")
                return False
        else:
            self._logger.error("P0-B: No IBAN in payout_details for %s", order_id)
            self.state.set_error(order_id, "No IBAN in payout payload")
            return False

        # FIX A5: Re-verify order is still active on Binance before sending EUR
        client = registry.get_exchange_api(managed.order.exchange.value)
        if client:
            try:
                verified_order = await client.get_order(managed.order.external_id)
                if verified_order:
                    abort_states = {OrderState.CANCELLED, OrderState.EXPIRED, OrderState.COMPLETED}
                    if verified_order.status in abort_states:
                        self._logger.warning("PAYOUT ABORTED: Order %s is %s on Binance — not sending EUR", managed.order.external_id[-8:], verified_order.status.value)
                        self.state.set_error(order_id, f"Payout aborted: order is {verified_order.status.value} on exchange")
                        return False
                    self._logger.info("Re-verified order %s is still active on Binance", managed.order.external_id[-8:])
                else:
                    self._logger.warning("PAYOUT ABORTED: Could not verify order %s — get_order returned None", managed.order.external_id[-8:])
                    self.state.set_error(order_id, "Payout aborted: exchange verification returned None")
                    return False
            except Exception as e:
                self._logger.warning("PAYOUT ABORTED: Exchange verification failed for %s: %s", managed.order.external_id[-8:], e)
                self.state.set_error(order_id, f"Payout aborted: exchange verification error: {e}")
                return False

        payload = managed.payout_details
        ext_id = managed.order.external_id

        # 1. Send EUR via Januar
        januar_client = registry.get_bank("januar")
        if not januar_client:
            self._logger.error("Januar client not available")
            self.state.set_error(order_id, "Januar client unavailable")
            return False

        # Generate deterministic replay_id for Januar idempotency
        replay_id = f"payout-{managed.order.internal_order_number}-{ext_id}"

        # P0-5: DB-level at-most-once payout guard
        from src.core.persistence import order_db
        if not order_db.try_claim_eur_payout(order_id, replay_id):
            self._logger.warning(
                "P0-5 GUARD: Payout already claimed for %s — blocking duplicate",
                order_id,
            )
            return False

        self._logger.info("Sending payout for %s: %s %s to %s (replay_id=%s)", ext_id[-8:], payload['amount'], payload['currency'], payload['recipient_name'], replay_id)

        # P1-D: Typed exception handling from Januar
        from src.fiat.eur.januar_sepa_client import (
            PayoutError, PayoutNetworkError, PayoutApiError, PayoutBlockedError,
        )
        try:
            payout_result = await januar_client.initiate_payout(
                amount=payload["amount"],
                currency=payload["currency"],
                recipient_name=payload["recipient_name"],
                recipient_account=payload["recipient_account"],
                reference=payload.get("reference"),
                internal_note=payload.get("internal_note"),
                replay_id=replay_id,
            )
        except PayoutBlockedError as e:
            order_db.mark_eur_payout_result(order_id, False)
            self._logger.critical("PAYOUT BLOCKED by compliance: %s", e)
            self.state.set_error(order_id, f"Payout blocked: {e}")
            return False
        except PayoutNetworkError as e:
            # Network error — replay_id makes retry safe
            order_db.mark_eur_payout_result(order_id, False)
            self._logger.error("PAYOUT NETWORK ERROR for %s: %s", ext_id[-8:], e)
            self.state.set_error(order_id, f"Network error: {e}")
            return False
        except PayoutApiError as e:
            error_msg = str(e)
            self._logger.error("PAYOUT API ERROR for %s: %s (status=%d)", ext_id[-8:], e, e.status_code)

            # Chat fallback: if name validation failed, try extracting Latin name from chat
            if "PROVIDER_VALIDATION" in error_msg and "character" in error_msg.lower():
                self._logger.info("Name validation failed — attempting chat fallback for %s", ext_id[-8:])
                # Try cleaning the original name first (faster than chat)
                from src.services.name_sanitizer import extract_clean_latin_parts
                clean_name = extract_clean_latin_parts(payload["recipient_name"])
                if clean_name:
                    self._logger.info("Name cleanup: '%s' -> '%s' (dropped non-Latin parts)", payload["recipient_name"], clean_name)
                    chat_name = clean_name
                else:
                    # Fall back to reading name from chat messages
                    chat_name = await self._extract_name_from_chat(managed)
                if chat_name:
                    old_name = payload["recipient_name"]
                    payload["recipient_name"] = chat_name
                    managed.payout_details = payload
                    self.state._persist(managed)
                    self._logger.info("Chat fallback: '%s' → '%s', retrying payout for %s", old_name, chat_name, ext_id[-8:])

                    # FIX: Skip DB re-claim — we already hold the per-order lock and
                    # the original claim row exists. Just use a new replay_id for
                    # Januar server-side idempotency and retry directly.
                    retry_replay_id = f"{replay_id}-retry" 

                    self._logger.info("Sending RETRY payout for %s: %s %s to %s (replay_id=%s)", ext_id[-8:], payload['amount'], payload['currency'], chat_name, retry_replay_id)
                    try:
                        payout_result = await januar_client.initiate_payout(
                            amount=payload["amount"],
                            currency=payload["currency"],
                            recipient_name=chat_name,
                            recipient_account=payload["recipient_account"],
                            reference=payload.get("reference"),
                            internal_note=payload.get("internal_note"),
                            replay_id=retry_replay_id,
                        )
                        # Retry succeeded — fall through to success handling below
                        self._logger.info("Chat fallback SUCCEEDED for %s", ext_id[-8:])
                    except (PayoutBlockedError, PayoutNetworkError, PayoutApiError, PayoutError) as retry_err:
                        order_db.mark_eur_payout_result(order_id, False)
                        self._logger.error("Chat fallback RETRY FAILED for %s: %s", ext_id[-8:], retry_err)
                        self.state.set_error(order_id, f"Chat fallback retry failed: {retry_err}")
                        return False
                else:
                    order_db.mark_eur_payout_result(order_id, False)
                    self._logger.warning("Chat fallback: no Latin name found in chat for %s", ext_id[-8:])
                    self.state.set_error(order_id, f"Name validation failed, no chat fallback available: {e}")
                    return False
            else:
                order_db.mark_eur_payout_result(order_id, False)
                self.state.set_error(order_id, f"Januar API error {e.status_code}: {e}")
                return False
        except PayoutError as e:
            order_db.mark_eur_payout_result(order_id, False)
            self._logger.error("PAYOUT ERROR for %s: %s", ext_id[-8:], e)
            self.state.set_error(order_id, f"Payout error: {e}")
            return False

        # P0-5: Record payout success
        order_db.mark_eur_payout_result(order_id, True)

        # Record payout sent time (persisted to DB via save_order)
        managed.payout_sent_at = datetime.now()
        managed.matched_payment = payout_result
        self.state._persist(managed)

        januar_tx_id = payout_result.id if payout_result else "unknown"
        self._logger.info("Payout sent for %s: txn=%s", ext_id[-8:], januar_tx_id)

        # P0-A: Durable payout record — persist BEFORE mark_paid attempt
        order_db.set_mark_paid_pending(order_id, januar_tx_id)

        # 2. Mark order as paid on Binance with inline retries
        client = registry.get_exchange_api(managed.order.exchange.value)
        if not client:
            self._logger.warning("Exchange client not available to mark paid — will retry via reconciliation")
            return True  # Payout succeeded, mark_paid_pending will handle retry

        mark_paid_success = False
        for attempt in range(1, 4):  # 3 inline retries
            try:
                mark_result = await client.mark_order_paid(ext_id)
                if mark_result:
                    mark_paid_success = True
                    break
                self._logger.warning("mark_paid attempt %d/3 failed for %s", attempt, ext_id[-8:])
            except Exception as e:
                self._logger.warning("mark_paid attempt %d/3 error for %s: %s", attempt, ext_id[-8:], e)
            if attempt < 3:
                await asyncio.sleep(2 * attempt)  # 2s, 4s backoff

        if mark_paid_success:
            # P0-A: Clear pending flag
            order_db.resolve_mark_paid(order_id)
            managed.paid_at = datetime.now()
            self.state.transition(order_id, OrderState.MARKED_AS_PAID, "buy_payout_sent_and_marked")
            self.state._persist(managed)

            # Send Trustpilot thank-you right after we pay the seller
            try:
                await self._send_completion_message(client, managed)
            except Exception as e:
                self._logger.warning("Failed to send BUY thank-you for %s: %s", ext_id[-8:], e)
            self._logger.info("Buy order %s: EUR sent + marked paid on Binance", ext_id[-8:])
            self._logger.info("   Waiting for seller to release crypto (30min timeout)")
        else:
            # P0-A: mark_paid_pending stays = 1 → reconciliation will retry
            self._logger.critical(
                "CRITICAL: EUR SENT for %s but mark_paid FAILED after 3 attempts — mark_paid_pending=1, reconciliation will retry",
                ext_id[-8:],
            )
            self.state.set_error(order_id, "EUR sent but mark_paid failed — pending reconciliation")

        return True

    # -------------------------------------------------------------------------
    # P0-A: MARK_PAID RECONCILIATION
    # -------------------------------------------------------------------------

    async def _reconcile_pending_mark_paids(self) -> None:
        """Retry mark_paid for orders where EUR was sent but Binance mark_paid failed.
        
        Called every poll cycle. Exponential backoff based on retry count.
        Max 10 retries before exporting to CANCELLED_ORDERS.csv and giving up.
        """
        from src.core.persistence import order_db
        pending = order_db.get_pending_mark_paids()
        if not pending:
            return

        self._logger.warning("P0-A RECONCILIATION: %d orders with pending mark_paid", len(pending))

        for row in pending:
            oid = row["order_id"]
            retries = row["mark_paid_retries"]
            managed = self.state.get_order(oid)

            if not managed:
                self._logger.error("Pending mark_paid order %s not found in state — skipping", oid)
                continue

            # Exponential backoff: skip if not enough time has passed
            # retry 1→10s, 2→20s, 3→40s, 4→80s, 5→160s, ...
            backoff_seconds = min(10 * (2 ** retries), 600)  # Max 10 min
            claimed_at = datetime.fromisoformat(row["claimed_at"])
            elapsed = (datetime.now() - claimed_at).total_seconds()
            if elapsed < backoff_seconds * retries:
                continue  # Too soon to retry

            if retries >= 10:
                # P0-A: Exhausted — export to CANCELLED_ORDERS.csv and give up
                self._logger.critical(
                    "MARK_PAID EXHAUSTED for %s after %d retries — exporting to CANCELLED_ORDERS.csv",
                    managed.order.external_id, retries,
                )
                order_db.export_cancelled_order_csv(managed)
                order_db.resolve_mark_paid(oid)  # Clear pending to stop retrying
                self.state.set_error(oid, f"mark_paid failed after {retries} retries — exported to CANCELLED_ORDERS.csv")
                continue

            # Attempt mark_paid
            ext_id = managed.order.external_id
            client = registry.get_exchange_api(managed.order.exchange.value)
            if not client:
                continue

            try:
                mark_result = await client.mark_order_paid(ext_id)
                retry_num = order_db.increment_mark_paid_retry(oid)

                if mark_result:
                    order_db.resolve_mark_paid(oid)
                    managed.paid_at = datetime.now()
                    self.state.transition(oid, OrderState.MARKED_AS_PAID, f"mark_paid_reconciled_retry_{retry_num}")
                    self.state._persist(managed)
                    self._logger.info(
                        "P0-A RECONCILED: mark_paid succeeded for %s on retry %d",
                        ext_id[-8:], retry_num,
                    )
                else:
                    self._logger.warning(
                        "P0-A: mark_paid retry %d/%d failed for %s",
                        retry_num, 10, ext_id[-8:],
                    )
            except Exception as e:
                order_db.increment_mark_paid_retry(oid)
                self._logger.warning("P0-A: mark_paid retry error for %s: %s", ext_id[-8:], e)

    # -------------------------------------------------------------------------
    # UTILITIES & BACKOFF
    # -------------------------------------------------------------------------

    def _get_exchange_poll_interval(self) -> float:
        active = self.state.get_active_orders()
        base = self._exchange_poll_config["active"] if active else self._exchange_poll_config["idle"]
        return self._add_jitter(base)
    
    def _add_jitter(self, interval: float) -> float:
        jitter = interval * self._jitter_factor * (random.random() * 2 - 1)
        return max(1.0, interval + jitter)
    
    def _get_backoff_delay(self, source: str) -> float:
        errors = self._error_counts.get(source, 0)
        if errors == 0: return 0
        delay = min(2 ** errors, self._max_backoff)
        return self._add_jitter(delay)
    
    def _record_success(self, source: str) -> None:
        if source in self._error_counts: del self._error_counts[source]
    
    def _record_error(self, source: str) -> None:
        self._error_counts[source] = self._error_counts.get(source, 0) + 1
        backoff = self._get_backoff_delay(source)
        self._logger.warning("%s error #%d, backoff: %.1fs", source, self._error_counts[source], backoff)

    def _check_payment_timeouts(self) -> None:
        """Check for paid orders timing out (both sell and buy sides)."""
        awaiting = self.state.get_orders_by_state(OrderState.MARKED_AS_PAID)
        for managed in awaiting:
            # SKIP if under agent review
            if managed.state in [OrderState.AGENT_REQUIRED, OrderState.AGENT_PROCESSING]:
                continue
            
            # Use the appropriate timestamp for timeout check
            # SELL: paid_at = when buyer marked paid (waiting for fiat to arrive)
            # BUY: paid_at = when we marked paid (waiting for seller to release crypto)
            timeout_ref = managed.paid_at
            if timeout_ref is None: continue
            
            elapsed = (datetime.now() - timeout_ref).total_seconds()
            timeout_seconds = self.delay_timeout_minutes * 60
            
            if managed.order.side == OrderSide.BUY:
                # BUY: seller hasn't released crypto in time
                if elapsed >= timeout_seconds:
                    self._logger.warning("BUY order %s → DELAYED (seller not released in %dm)", managed.order.external_id, self.delay_timeout_minutes)
                    self.state.transition(managed.id, OrderState.DELAYED, f"buy_seller_timeout_{self.delay_timeout_minutes}m")
            else:
                # SELL: buyer marked paid but fiat hasn't arrived
                if elapsed >= timeout_seconds and managed.matched_payment is None:
                    self._logger.warning("Order %s → DELAYED (timeout)", managed.order.external_id)
                    self.state.transition(managed.id, OrderState.DELAYED, f"timeout_{self.delay_timeout_minutes}m")

    # -------------------------------------------------------------------------
    # ACTIONS (BUY/SELL)
    # -------------------------------------------------------------------------
    
    async def release_crypto(self, order_id: str, verification_code: str | None = None) -> bool:
        """Release crypto with per-order locking and inline retries (3 attempts with exponential backoff)."""
        lock = self.state.get_lock(order_id)
        
        # Fail-fast if another release is already in progress for this order
        if lock.locked():
            self._logger.warning("Release already in progress for %s — skipping to prevent double-release", order_id)
            return False
        
        async with lock:
            managed = self.state.get_order(order_id)
            if not managed: return False
            
            # Guard: prevent re-release of already completed or in-progress orders
            if managed.state in (OrderState.COMPLETED, OrderState.RELEASING):
                self._logger.warning("Order %s is already %s — skipping release", order_id, managed.state.value)
                return False
            
            client = registry.get_exchange_api(managed.order.exchange.value)
            if not client: return False
            
            # FIX A4: Pre-check exchange status before attempting release
            # If order is already released/completed on Binance, skip the release call
            try:
                verified_order = await client.get_order(managed.order.external_id)
                if verified_order and verified_order.status == OrderState.COMPLETED:
                    self._logger.info("Order %s already COMPLETED on exchange — syncing locally", managed.order.external_id[-8:])
                    self.state.transition(order_id, OrderState.COMPLETED, "exchange_already_released")
                    return True
            except Exception as e:
                self._logger.warning("Pre-release exchange check failed: %s — proceeding with release attempt", e)
            
            self.state.transition(order_id, OrderState.RELEASING, "release_initiated")

            # P0-6: DB-level at-most-once release guard
            # Must claim BEFORE calling release_crypto. If claim fails, another
            # path (or a previous run before crash) already initiated this release.
            from src.core.persistence import order_db
            if not order_db.try_claim_eur_release(order_id):
                self._logger.warning(
                    "P0-6 GUARD: Release already claimed for %s — verifying exchange status",
                    order_id,
                )
                # Check exchange instead of re-releasing
                try:
                    check = await client.get_order(managed.order.external_id)
                    if check and check.status == OrderState.COMPLETED:
                        self.state.transition(order_id, OrderState.COMPLETED, "exchange_verified_after_guard")
                        return True
                except Exception:
                    pass
                # Cannot confirm — leave in RELEASING for manual review
                self.state.transition(order_id, OrderState.ERROR, "release_guard_blocked_unverified")
                return False

            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    # Send thank-you message BEFORE release so buyer sees it
                    await self._send_completion_message(client, managed)
                    
                    release_success = await client.release_crypto(managed.order.external_id, verification_code)

                    if release_success:
                        # P0-6: Record success in guard table
                        order_db.mark_eur_release_result(order_id, True)
                        self.state.transition(order_id, OrderState.COMPLETED, "crypto_released")
                        self.state._emit(OrderEvent.ORDER_RELEASED, managed)
                        self._logger.info("Crypto released: %s", managed.order.external_id)
                        return True
                    
                    # API returned failure
                    self.state.set_error(order_id, f"Release failed (attempt {attempt}/{max_retries})")
                    
                except Exception as e:
                    self.state.set_error(order_id, f"{e} (attempt {attempt}/{max_retries})")
                
                # Retry with backoff if not last attempt
                if attempt < max_retries:
                    backoff = 2 ** attempt
                    self._logger.warning("Release failed for %s. Retry %d/%d in %ds...", managed.order.external_id, attempt, max_retries, backoff)
                    await asyncio.sleep(backoff)
            
            # All retries exhausted — record failure in guard table
            order_db.mark_eur_release_result(order_id, False)
            self._logger.error("Release failed after %d attempts for %s. Moving to ERROR.", max_retries, managed.order.external_id)
            self.state.transition(order_id, OrderState.ERROR, "release_failed_max_retries")
            return False

    async def mark_as_paid(self, order_id: str, payment_method_id: int | None = None) -> bool:
        managed = self.state.get_order(order_id)
        if not managed: return False
        
        client = registry.get_exchange_api(managed.order.exchange.value)
        if not client: return False
        
        try:
            if await client.mark_order_paid(managed.order.external_id, payment_method_id):
                self.state.transition(order_id, OrderState.MARKED_AS_PAID, "marked_paid")
                return True
            self.state.set_error(order_id, "Mark paid failed")
            return False
        except Exception as e:
            self.state.set_error(order_id, str(e))
            return False

    def get_status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "active_orders": len(self.state.get_active_orders()),
            "last_poll": {k: v.isoformat() for k, v in self._last_poll.items()}
        }

# Singleton
orchestrator = OrderOrchestrator()