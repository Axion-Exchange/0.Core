"""
JANUAR PAYMENT CLIENT
=========================
Handles EUR banking operations - incoming payments, payouts, and automated order matching.
"""

import base64
import hmac
import json
import time
import urllib.parse
import os
import random
import asyncio
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any, Optional
from uuid import uuid4

import httpx
import logging

# --- Core Imports ---
from src.core.clients import BankClient
from src.core.types import (
    BankProvider,
    Currency,
    PaymentDirection,
    PaymentStatus,
    UnifiedBalance,
    UnifiedPayment,
)

# --- Logic & Service Imports (Added for Poller Integration) ---
from src.core.state_manager import state_manager, ManagedOrder, OrderState
from src.logic.payment_matcher import PaymentMatcher, ReleaseVerdict
from src.services.iban_screener import screen_iban

logger = logging.getLogger("januar")


# =============================================================================
# P1-D: Typed payout exceptions (replaces bare except: return None)
# =============================================================================

class PayoutError(Exception):
    """Base exception for payout failures."""
    pass

class PayoutNetworkError(PayoutError):
    """Network/timeout error — safe to retry with same replay_id."""
    pass

class PayoutApiError(PayoutError):
    """4xx/5xx from Januar API — may need investigation."""
    def __init__(self, status_code: int, body: str, message: str = ""):
        self.status_code = status_code
        self.body = body
        super().__init__(message or f"Januar API {status_code}: {body[:200]}")

class PayoutBlockedError(PayoutError):
    """Payout blocked by compliance screening — permanent failure."""
    pass


class JanuarSepaClient(BankClient):
    """
    Januar EUR banking client.
    
    Capabilities:
    1. Low-level API: Authenticated requests, fetching transactions, initiating payouts.
    2. Smart Polling: Context-aware polling intervals (Idle/Active/Urgent).
    3. Order Matching: Automatically matches incoming EUR payments to pending orders.
    4. Auto-Refund: Detects and refunds third-party payments.
    """
    
    def __init__(self, api_key: str, api_secret: str, base_url: str, state=None):
        # --- API Configuration ---
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.account_id: str | None = None
        
        # --- Logic Components (Poller Integration) ---
        self.state = state or state_manager
        gemini_key = os.getenv("GEMINI_API_KEY")
        self.payment_matcher = PaymentMatcher(gemini_api_key=gemini_key)
        
        # --- Smart Polling State ---
        self._last_poll: Optional[datetime] = None
        self._error_count = 0
        
        # Polling Configuration (unified with Binance: 20s active, 40s idle)
        self._poll_config = {
            "idle": 40.0,    # No orders awaiting payment
            "active": 20.0,  # Orders awaiting payment verification
        }
        
        # Backoff Configuration
        self._max_backoff = 300.0  # 5 min max backoff
        self._jitter_factor = 0.2

    @property
    def provider_id(self) -> str:
        return "januar"
    
    @property
    def supported_currencies(self) -> list[str]:
        return ["EUR", "USDC"]
    
    # =========================================================================
    # AUTHENTICATION & LOW-LEVEL REQUESTS (EXISTING LOGIC)
    # =========================================================================
    
    def _generate_signature(self, method: str, path: str, body: str = "") -> tuple[str, int]:
        """Generate Januar API HMAC-SHA256 signature."""
        nonce = int(time.time() * 1000)
        encoded_path = urllib.parse.quote(path, safe='')
        message = f"{nonce}|{method.upper()}|{encoded_path}|{body}".encode('utf-8')
        signature = hmac.new(self.api_secret.encode('utf-8'), message, digestmod=sha256)
        return base64.b64encode(signature.digest()).decode(), nonce
    
    async def _request(self, method: str, endpoint: str, data: dict[str, Any] | None = None) -> dict:
        """Make authenticated API request with HMAC signature."""
        if method.upper() == "GET" and data:
            query_string = urllib.parse.urlencode(data)
            path = f"{endpoint}?{query_string}"
            body = ""
        else:
            path = endpoint
            body = json.dumps(data) if data else ""
        
        signature, nonce = self._generate_signature(method.upper(), path, body)
        
        auth_header = (
            f'JanuarAPI apikey="{self.api_key}", '
            f'nonce="{nonce}", '
            f'signature="{signature}"'
        )
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "JanuarSepaClient/1.0",
        }
        
        url = f"{self.base_url}{endpoint}"
        
        if method.upper() == "GET":
            response = await self.client.get(url, headers=headers, params=data)
        elif method.upper() == "PUT":
            response = await self.client.put(url, headers=headers, content=body)
        else:
            response = await self.client.post(url, headers=headers, content=body)
        
        response.raise_for_status()
        return response.json()

    async def is_ready(self) -> bool:
        """Test API connectivity by fetching accounts."""
        try:
            response = await self._request("GET", "/accounts")
            accounts = response.get("data", [])
            if accounts and len(accounts) > 0:
                self.account_id = accounts[0].get("id")
            return bool(accounts)
        except Exception:
            return False

    async def _fetch_account_id(self) -> None:
        """Fetch the primary account ID if not already set."""
        if self.account_id:
            return
        try:
            response = await self._request("GET", "/accounts")
            accounts = response.get("data", [])
            if accounts and len(accounts) > 0:
                self.account_id = accounts[0].get("id")
                print(f"📋 Januar account ID: {self.account_id}")
        except Exception as e:
            print(f"Error fetching Januar account: {e}")

    # =========================================================================
    # PUBLIC API: PAYMENTS & BALANCES (EXISTING LOGIC)
    # =========================================================================

    async def get_payment_by_id(self, transaction_id: str) -> UnifiedPayment | None:
        """Fetch a single incoming payment by its Januar transaction UUID."""
        payments = await self.get_incoming_payments(limit=200)
        for p in payments:
            if p.external_id == transaction_id:
                return p
        return None

    async def get_incoming_payments(
        self,
        currency: str | None = None,
        limit: int = 50,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[UnifiedPayment]:
        """Get incoming EUR payments (PAYIN)."""
        await self._fetch_account_id()
        if not self.account_id:
            return []
        
        # Use a larger default limit and request descending order if possible
        params: dict = {
            "pageSize": max(limit, 200),
            "types": "PAYIN"
        }
        if currency: params["currencies"] = currency
        if start_time: params["dateFrom"] = start_time[:10]
        if end_time: params["dateTo"] = end_time[:10]
            
        try:
            endpoint = f"/accounts/{self.account_id}/transactions"
            response = await self._request("GET", endpoint, params)
            transactions = response.get("data", []) if isinstance(response, dict) else []
            if not isinstance(transactions, list): transactions = []
            
            # Manual Sort (Newest First) to ensure we process recent payments if API ignores sort param
            transactions.sort(key=lambda t: t.get("createdAt", ""), reverse=True)
            
            return [self._transform_payment(t, "incoming") for t in transactions]
        except Exception as e:
            print(f"Error fetching incoming payments: {e}")
            return []

    async def get_outgoing_payments(
        self,
        currency: str | None = None,
        limit: int = 50,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[UnifiedPayment]:
        """Get outgoing payouts (PAYOUT)."""
        await self._fetch_account_id()
        if not self.account_id:
            return []
        
        params: dict = {"pageSize": limit, "types": "PAYOUT"}
        if currency: params["currencies"] = currency
        if start_time: params["dateFrom"] = start_time[:10]
        if end_time: params["dateTo"] = end_time[:10]

        try:
            endpoint = f"/accounts/{self.account_id}/transactions"
            response = await self._request("GET", endpoint, params)
            transactions = response.get("data", []) if isinstance(response, dict) else []
            if not isinstance(transactions, list): transactions = []
            return [self._transform_payment(t, "outgoing") for t in transactions]
        except Exception as e:
            print(f"Error fetching outgoing payments: {e}")
            return []

    async def initiate_payout(
        self,
        amount: str,
        currency: str,
        recipient_name: str,
        recipient_account: str,
        payment_method: str = "SEPA",
        reference: str | None = None,
        internal_note: str | None = None,
        replay_id: str | None = None,
        is_refund: bool = False,
        refund_reason: str | None = None,
    ) -> UnifiedPayment:
        """
        Initiate an outgoing payout.
        Includes compliance screening (sanctions) and dashboard alerting.
        
        Raises:
            PayoutBlockedError: IBAN is sanctioned/blocked
            PayoutNetworkError: Network timeout or connection failure
            PayoutApiError: Januar returned 4xx/5xx
            PayoutError: Other unexpected failure
        """
        await self._fetch_account_id()
        if not self.account_id:
            raise PayoutError("Januar account_id not available — check API credentials")
        
        # 1. Compliance Screening (Sanctions)
        # Check recipient IBAN against blocked countries
        if recipient_account:
            iban_check = screen_iban(recipient_account)
            if iban_check.is_blocked:
                logger.critical(
                    "Payout blocked: IBAN %s*** is from sanctioned country %s",
                    recipient_account[:4], iban_check.country_code,
                )
                
                # Alert dashboard about blocked payout
                if is_refund:
                    await self._alert_sanctioned_payout(
                        amount=amount,
                        currency=currency,
                        recipient_name=recipient_name,
                        recipient_account=recipient_account,
                        country_code=iban_check.country_code or "UNKNOWN",
                        reason=refund_reason or "Sanctioned Country",
                    )
                raise PayoutBlockedError(
                    f"IBAN {recipient_account[:4]}*** blocked: {iban_check.reason}"
                )
        
        country_code = recipient_account[:2] if len(recipient_account) >= 2 else None
        
        body = {
            "amount": amount,
            "currency": currency,
            "message": reference or f"Payment {datetime.now().strftime('%Y%m%d')}",
            "counterparty": {
                "type": "PRIVATE",
                "name": recipient_name,
                "accountNumber": recipient_account,
                "accountNumberType": "IBAN",
            }
        }
        if country_code:
            body["counterparty"]["accountNumberCountryCode"] = country_code
        if internal_note:
            body["internalNote"] = internal_note
        if replay_id:
            body["replayId"] = replay_id
        
        try:
            endpoint = f"/accounts/{self.account_id}/transactions/payout"
            response = await self._request("POST", endpoint, body)
            payout_data = response.get("data", response)
            logger.info("Payout initiated: %s", payout_data.get('id', 'unknown'))
            return self._transform_payment(payout_data, "outgoing")
        except httpx.TimeoutException as e:
            raise PayoutNetworkError(f"Januar timeout after 30s: {e}") from e
        except httpx.ConnectError as e:
            raise PayoutNetworkError(f"Januar connection failed: {e}") from e
        except httpx.HTTPStatusError as e:
            raise PayoutApiError(
                status_code=e.response.status_code,
                body=e.response.text,
                message=f"Januar {e.response.status_code}: {e.response.text[:200]}",
            ) from e
        except PayoutError:
            raise  # Re-raise our own exceptions
        except Exception as e:
            raise PayoutError(f"Unexpected payout error: {e}") from e
            
    async def verify_counterparty(self, name: str, iban: str) -> dict[str, Any]:
        """
        Verify a counterparty (Verification of Payee).
        Polls until completion or timeout.
        Returns: { "status": "COMPLETED", "result": { "code": "MATCH", ... } }
        """
        print(f"🔎 Verifying counterparty: {name} ({iban[:4]}...)")
        
        # Split name for private individuals
        parts = name.strip().split(" ", 1)
        first_name = parts[0]
        surname = parts[1] if len(parts) > 1 else ""

        payload = {
            "type": "PRIVATE",
            "name": first_name,
            "surname": surname,
            "accountNumber": iban,
            "accountNumberType": "IBAN",
        }
        
        try:
            # 1. Initiate
            resp = await self._request("POST", "/counterparty-verification", payload)
            data = resp.get("data", resp)
            verification_id = data.get("id")
            
            if not verification_id:
                return {"status": "FAILED", "error": "No ID returned"}
                
            # 2. Poll
            for _ in range(10): # 10 attempts * 1s = 10s max
                await asyncio.sleep(1.0)
                status_resp = await self._request("GET", f"/counterparty-verification/{verification_id}")
                status_data = status_resp.get("data", status_resp)
                
                status = status_data.get("status")
                if status in ["COMPLETED", "FAILED"]:
                    return status_data
            
            return {"status": "TIMEOUT", "error": "Verification timed out"}
            
        except Exception as e:
            print(f"⚠️ VOP Error: {e}")
            return {"status": "ERROR", "error": str(e)}

    async def refund_payment(
        self,
        payment: UnifiedPayment,
        reason_tag: str,
        custom_reference: str | None = None,
        order: ManagedOrder | None = None,
    ) -> UnifiedPayment | None:
        """
        Convenience method to refund a specific payment.
        Auto-generates reference and calls initiate_payout with refund flag.
        """
        if not payment.sender_account or not payment.sender_name:
            print(f"❌ Cannot refund: Missing sender details")
            return None

        # Build reference
        # Format: refund-[internal ID]-[3 character code]
        ref_msg = custom_reference
        if not ref_msg:
            internal_id = "NO_ORDER"
            if order:
                internal_id = order.order.internal_order_number if hasattr(order, 'order') else "UNKNOWN"
            
            code = self._get_refund_code(reason_tag)
            ref_msg = f"refund-{internal_id}-{code}"

        # Generate deterministic replay_id for refund idempotency
        refund_replay_id = f"refund-{payment.external_id}-{ref_msg}"

        return await self.initiate_payout(
            amount=payment.amount,
            currency="EUR", # Januar only supports EUR payouts for now
            recipient_name=payment.sender_name,
            recipient_account=payment.sender_account,
            payment_method="SEPA",
            reference=ref_msg,
            internal_note=f"Auto-refund for {payment.external_id}",
            replay_id=refund_replay_id,
            is_refund=True,
            refund_reason=reason_tag,
        )

    def _get_refund_code(self, reason: str) -> str:
        """Map text reason to 3-char code."""
        mapping = {
            "Third-party sender": "TPS",
            "Duplicate payment": "DUP",
            "Overpayment": "OVP",
            "Order cancelled": "CNL",
            "Sanctioned Country": "SNC",
            "Customer Request": "REQ",
        }
        # Default to first 3 chars upper if not found
        return mapping.get(reason, reason[:3].upper())

    async def _alert_sanctioned_payout(
        self,
        amount: str,
        currency: str,
        recipient_name: str,
        recipient_account: str,
        country_code: str,
        reason: str,
    ) -> None:
        """Send alert to dashboard when a payout is blocked."""
        dashboard_url = os.getenv("DASHBOARD_ALERT_URL", "http://localhost:8000/api/alerts")
        alert_payload = {
            "alert_type": "SANCTIONED_PAYOUT_BLOCKED",
            "severity": "HIGH",
            "timestamp": datetime.now().isoformat(),
            "payout": {
                "amount": amount,
                "currency": currency,
                "recipient_name": recipient_name,
                "recipient_iban": recipient_account,
            },
            "blocked_reason": {
                "country_code": country_code,
                "reason": reason,
            },
            "action_required": "Manual compliance review required.",
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    dashboard_url,
                    json=alert_payload,
                    headers={"Content-Type": "application/json"},
                )
        except Exception as e:
            print(f"⚠️ Could not send dashboard alert: {e}")

    async def get_balances(self) -> list[UnifiedBalance]:
        """Get account balances."""
        try:
            response = await self._request("GET", "/accounts")
            accounts = response.get("data", response) if isinstance(response, dict) else []
            if not isinstance(accounts, list): accounts = [accounts] if accounts else []
                 
            balances = []
            for acc in accounts:
                # Januar API returns nested format:
                #   {"balances": {"EUR": "461.16", "DKK": "0.00"}, ...}
                balances_dict = acc.get("balances", {})
                if isinstance(balances_dict, dict) and balances_dict:
                    for curr, bal_val in balances_dict.items():
                        bal = str(bal_val)
                        if float(bal) > 0:
                            balances.append(UnifiedBalance(
                                source="januar", asset=curr, available=bal,
                                locked="0", total=bal, updated_at=datetime.now()
                            ))
                else:
                    # Legacy flat format fallback
                    bal = str(acc.get("balance", acc.get("availableBalance", "0")))
                    curr = acc.get("currency", "EUR")
                    if float(bal) > 0:
                        balances.append(UnifiedBalance(
                            source="januar", asset=curr, available=bal,
                            locked="0", total=bal, updated_at=datetime.now()
                        ))
            return balances
        except Exception as e:
            print(f"Error fetching Januar balances: {e}")
            return []



    async def run_smart_poll(self) -> None:
        """
        Main entry point for the polling loop.
        Checks if polling is required based on intervals/backoff, 
        fetches payments, and triggers matching logic.
        Also monitors for RETURNED_PAYIN to detect reversed payments.
        """
        if not self._should_poll():
            return

        print("🏦 Januar: Polling for incoming payments...")
        try:
            # 1. Fetch
            payments = await self.get_incoming_payments(currency="EUR", limit=100)
            
            # 2. Filter completed
            completed_payments = [p for p in payments if p.status == PaymentStatus.COMPLETED]
            
            self._last_poll = datetime.now()
            
            print(f"🏦 Januar: Found {len(completed_payments)} completed EUR payments")
            
            # 3. Match
            if completed_payments:
                await self._match_payments_to_orders(completed_payments)
            
            # 4. Check for returned payments (reversed settlements)
            await self._check_for_returned_payments()
            
            self._record_success()
            
        except Exception as e:
            print(f"🏦 Januar: Poll error - {e}")
            self._record_error(e)


    async def _match_payments_to_orders(self, payments: list[UnifiedPayment]) -> None:
        """Core logic: match a list of payments to pending orders."""
        awaiting = self.state.get_orders_by_state(OrderState.MARKED_AS_PAID)
        delayed = self.state.get_orders_by_state(OrderState.DELAYED)
        appealed = self.state.get_orders_by_state(OrderState.APPEALED) 
        
        print(f"DEBUG CANDIDATES: Await={len(awaiting)} Delay={len(delayed)} Appeal={len(appealed)}")
        
        candidates = awaiting + delayed + appealed

        if not candidates:
            return

        # CRITICAL FIX: Filter out already-consumed payments BEFORE matching
        # This prevents the same Januar payment from being reused for multiple orders
        from src.core.persistence import order_db
        unconsumed_payments = []
        for p in payments:
            if order_db.is_payment_consumed(p.external_id):
                continue
            unconsumed_payments.append(p)
        
        filtered_count = len(payments) - len(unconsumed_payments)
        if filtered_count > 0:
            print(f"🛡️ DEDUP: Filtered out {filtered_count} already-consumed payments ({len(unconsumed_payments)} remaining)")
        
        if not unconsumed_payments:
            print(f"🛡️ DEDUP: All {len(payments)} payments already consumed — nothing to match")
            return

        # Convert to UnifiedOrder objects for the matcher
        unified_orders = [m.order for m in candidates]

        # Run matching algorithm
        matches = await self.payment_matcher.find_releasable_matches(unified_orders, unconsumed_payments)
        print(f"DEBUG: Found {len(matches)} potential matches")

        for verdict in matches:
            ext_id = verdict.order.external_id
            managed = self.state.get_by_external(ext_id)
            print(f"DEBUG: Processing match for {ext_id}. Managed found: {bool(managed)}")
            
            if not managed:
                print(f"❌ CRITICAL: Could not find managed order for {ext_id} in state manager!")
                continue

            if verdict.can_release:
                # FIX B2: Check for ambiguous matches before auto-releasing
                if verdict.ambiguous:
                    print(f"⚠️ AMBIGUOUS: Payment matches {len(verdict.ambiguous_order_ids)} orders: {verdict.ambiguous_order_ids}")
                    self.state.flag_for_review(managed.id, f"Ambiguous match: payment matches {len(verdict.ambiguous_order_ids)} orders — manual review required")
                else:
                    print(f"DEBUG: Verdict allows release for {ext_id}")
                    await self._apply_match(managed, verdict.payment, verdict)
            
            elif verdict.is_third_party:
                # Reference matched, but name mismatch -> Flag for manual review
                print(f"⚠️ Third-party payment detected: {managed.order.external_id}")
                self.state.match_payment(managed.id, verdict.payment)
                self.state.flag_as_third_party(managed.id, verdict.summary)
            
            else:
                # Ambiguous match -> Manual Review
                self.state.flag_for_review(managed.id, verdict.summary)

    async def _apply_match(self, managed: ManagedOrder, payment: UnifiedPayment, verdict: ReleaseVerdict = None) -> None:
        """Successfully link a payment and trigger IMMEDIATE release.
        Re-verifies payment settlement status before releasing."""
        
        # FIX A1: Re-verify payment is still settled before releasing
        # The poll data may be stale — confirm with a fresh API check
        fresh_payment = await self.get_payment_by_id(payment.external_id)
        if not fresh_payment or fresh_payment.status != PaymentStatus.COMPLETED:
            status_info = fresh_payment.status.value if fresh_payment else "NOT_FOUND"
            print(f"⚠️ Payment {payment.external_id} is no longer COMPLETED (status: {status_info}) — aborting release")
            self.state.flag_for_review(managed.id, f"Settlement re-check failed: payment status is {status_info}")
            return
        
        self.state.match_payment(managed.id, payment)
        
        # CRITICAL FIX: Mark this payment as consumed BEFORE releasing
        # This prevents the same payment from ever being reused for another order
        from src.core.persistence import order_db
        order_db.mark_payment_consumed(payment.external_id, managed.order.external_id)
        print(f"🛡️ DEDUP: Payment {payment.external_id[:12]}... consumed for order {managed.order.external_id[-8:]}")
        
        print(f"✅ Auto-release approved (settlement verified): {managed.order.external_id}")
        if verdict:
            print(f"   {verdict.summary}")
            
        managed.auto_release_approved = True
        self.state._persist(managed)  # FIX: Save approval to DB immediately
        
        # IMMEDIATELY RELEASE using Orchestrator (handles retries/errors state transitions)
        # This fixes "Head-of-Line Blocking" where failed releases loop forever
        from src.services.order_orchestrator import orchestrator
        
        print(f"🚀 RELEASING VIA ORCHESTRATOR: {managed.order.external_id}")
        # orchestrator.release_crypto handles:
        # 1. Per-order locking (prevents concurrent release)
        # 2. Calling Binance API
        # 3. Transitioning to COMPLETED on success
        # 4. Transitioning to ERROR after 3 failures (removing it from queue)
        await orchestrator.release_crypto(managed.id)

    async def _check_for_returned_payments(self) -> None:
        """FIX A1: Check for RETURNED_PAYIN transactions that reverse a matched payment.
        If a return is detected for an order we already released crypto on, flag it."""
        await self._fetch_account_id()
        if not self.account_id:
            return
        
        try:
            params = {"pageSize": 50, "types": "RETURNED_PAYIN"}
            endpoint = f"/accounts/{self.account_id}/transactions"
            response = await self._request("GET", endpoint, params)
            returns = response.get("data", []) if isinstance(response, dict) else []
            if not isinstance(returns, list):
                returns = []
            
            if not returns:
                return
            
            # Check if any returned payment affects a completed order
            completed_orders = self.state.get_orders_by_state(OrderState.COMPLETED)
            for ret in returns:
                original_payin_id = ret.get("payinId")
                if not original_payin_id:
                    continue
                
                for managed in completed_orders:
                    if managed.matched_payment and managed.matched_payment.external_id == original_payin_id:
                        ret_amount = ret.get("amount", "?")
                        print(f"🚨 RETURNED_PAYIN DETECTED for completed order {managed.order.external_id}!")
                        print(f"   Original payment {original_payin_id} was reversed. Amount: {ret_amount}")
                        self.state.set_error(
                            managed.id, 
                            f"CRITICAL: Payment {original_payin_id} returned after crypto release. Amount: {ret_amount}"
                        )
                        # TODO: Send dashboard alert, this requires manual recovery
        except Exception as e:
            print(f"Error checking returned payments: {e}")



    # =========================================================================
    # SCHEDULING UTILITIES (MERGED FROM POLLER)
    # =========================================================================

    def _should_poll(self) -> bool:
        """Determine if it's time to poll based on state and backoff."""
        # Check error backoff
        backoff = self._get_backoff_delay()
        if backoff > 0 and self._last_poll:
            elapsed = (datetime.now() - self._last_poll).total_seconds()
            if elapsed < backoff:
                return False

        if self._last_poll is None:
            return True

        elapsed = (datetime.now() - self._last_poll).total_seconds()
        target_interval = self._get_interval()
        interval_with_jitter = self._add_jitter(target_interval)
        
        return elapsed >= interval_with_jitter

    def _get_interval(self) -> float:
        """Calculate target interval based on order state (20s active, 40s idle)."""
        awaiting = self.state.get_orders_by_state(OrderState.MARKED_AS_PAID)
        delayed = self.state.get_orders_by_state(OrderState.DELAYED)

        if awaiting or delayed:
            return self._poll_config["active"]
        return self._poll_config["idle"]

    def _add_jitter(self, interval: float) -> float:
        """Add ±20% random jitter."""
        jitter = interval * self._jitter_factor * (random.random() * 2 - 1)
        return max(1.0, interval + jitter)

    def _get_backoff_delay(self) -> float:
        """Calculate exponential backoff: 2^errors."""
        if self._error_count == 0:
            return 0.0
        delay = min(2 ** self._error_count, self._max_backoff)
        return self._add_jitter(delay)

    def _record_success(self) -> None:
        self._error_count = 0

    def _record_error(self, e: Exception) -> None:
        self._error_count += 1
        backoff = self._get_backoff_delay()
        print(f"❌ Bank Poller Error #{self._error_count}: {e}")
        print(f"   Backing off for {backoff:.1f}s")

    # =========================================================================
    # DATA TRANSFORMATION
    # =========================================================================

    def _transform_payment(self, raw: dict[str, Any], direction: str) -> UnifiedPayment:
        """Transform Januar payment to unified format."""
        # FIX A1: Prefer explicit status field over completedTime inference
        status_raw = raw.get("status", "")
        if status_raw:
            status_obj = self._map_status(status_raw)
        elif raw.get("completedTime"):
            status_obj = PaymentStatus.COMPLETED
        else:
            status_obj = PaymentStatus.PENDING

        return UnifiedPayment(
            id=f"uni_{uuid4().hex[:12]}",
            external_id=str(raw.get("id", "")),
            provider=BankProvider.JANUAR,
            direction=PaymentDirection(direction),
            status=status_obj,
            amount=str(raw.get("amount", "0")),
            currency=Currency(raw.get("currency", "EUR")),
            sender_name=raw.get("senderName") or raw.get("counterparty", {}).get("name"),
            sender_account=raw.get("senderIban") or raw.get("counterparty", {}).get("accountNumber"),
            receiver_name=raw.get("receiverName") or raw.get("counterparty", {}).get("name"),
            receiver_account=raw.get("receiverIban") or raw.get("counterparty", {}).get("accountNumber"),
            reference=raw.get("message") or raw.get("reference"),
            payment_method=raw.get("paymentType", "SEPA"),
            created_at=datetime.fromisoformat(raw.get("created_at", datetime.now().isoformat())),
            completed_at=datetime.fromisoformat(raw["completedTime"].replace("Z", "+00:00")) if raw.get("completedTime") else None,
            raw=raw
        )
    
    def _map_status(self, status: str) -> PaymentStatus:
        mapping = {
            "pending": PaymentStatus.PENDING,
            "processing": PaymentStatus.PENDING,
            "completed": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
        }
        return mapping.get(status.lower(), PaymentStatus.PENDING)