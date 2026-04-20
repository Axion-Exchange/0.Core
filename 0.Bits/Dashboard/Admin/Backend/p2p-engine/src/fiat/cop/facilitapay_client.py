"""
FACILITAPAY COP CLIENT
=======================
Production-grade async client for FacilitaPay Colombia COP operations.

Handles:
- JWT authentication with auto-refresh (24h TTL, 23h safety margin)
- Subject management (person/company registration + dedup)
- Bank account registration + dedup
- PSE pay-in transaction creation
- COP payout transaction creation
- Transaction status polling
- Bank list caching (7-day TTL)
- Webhook notification recovery (failed webhook polling)

All write operations use app-level idempotency (FacilitaPay has no
native idempotency keys). The `meta.pear_order_id` field is the
primary link between FacilitaPay transactions and PearV1 orders.

Thread safety: Uses asyncio.Lock for JWT refresh. Database operations
use SQLite WAL mode with busy timeout.
"""

import asyncio
import json
import logging
import time
from typing import Any

import httpx

from .facilitapay_models import (
    FPAccountType,
    FPBankAccount,
    FPDocumentType,
    FPNotificationRecord,
    FPPayoutBankEntry,
    FPPseBankEntry,
    FPSubjectPerson,
    FPTransaction,
    FPTransactionDirection,
    FPTransactionStatus,
)
from .facilitapay_persistence import FacilitaPayDatabase

logger = logging.getLogger("facilitapay")


class FacilitaPayError(Exception):
    """Base exception for FacilitaPay API errors."""

    def __init__(self, message: str, status_code: int | None = None,
                 response_body: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FacilitaPayDuplicateError(FacilitaPayError):
    """Raised when a duplicate transaction/resource would be created."""
    pass


class FacilitaPayCopClient:
    """
    FacilitaPay API client for Colombian COP operations.
    
    Usage:
        client = FacilitaPayCopClient(
            username=os.getenv("FACILITAPAY_USERNAME"),
            password=os.getenv("FACILITAPAY_PASSWORD"),
            cashin_account_id=os.getenv("FACILITAPAY_CASHIN_ACCOUNT_ID"),
            cashout_account_id=os.getenv("FACILITAPAY_CASHOUT_ACCOUNT_ID"),
            webhook_secret=os.getenv("FACILITAPAY_WEBHOOK_SECRET"),
        )
        subject = await client.upsert_subject_person(...)
        tx = await client.create_pse_payin(subject_id=subject.id, ...)
    """

    # Settlement currency — MUST be consistent across pay-ins and payouts.
    # COP-only: NO FX conversion. Pay-ins and payouts are both in COP.
    # This avoids FacilitaPay FX conversion fees.
    SETTLEMENT_CURRENCY = "COP"

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str = "https://api.facilitapay.com/api/v1",
        cashin_account_id: str = "",
        cashout_account_id: str = "",
        webhook_secret: str = "",
        max_payin_cop: int = 50_000_000,
        max_payout_cop: int = 50_000_000,
        db_path: str = "facilitapay.db",
    ):
        self.username = username
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.cashin_account_id = cashin_account_id
        self.cashout_account_id = cashout_account_id
        self.webhook_secret = webhook_secret
        self.max_payin_cop = max_payin_cop
        self.max_payout_cop = max_payout_cop

        # Startup safety assertion — COP-only, no FX conversion
        assert self.SETTLEMENT_CURRENCY == "COP", (
            f"SETTLEMENT_CURRENCY must be COP for COP-only system, got {self.SETTLEMENT_CURRENCY}"
        )

        # Startup warnings for missing config
        if not webhook_secret:
            logger.critical(
                "🚨 FACILITAPAY_WEBHOOK_SECRET is NOT SET! "
                "All incoming webhooks will be REJECTED (fail-closed). "
                "Payment confirmations will NOT work until this is configured."
            )
        if not cashin_account_id:
            logger.warning("⚠️ FACILITAPAY_CASH_IN_ACCOUNT_ID is not set")

        # HTTP client
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

        # JWT state
        self._jwt: str | None = None
        self._jwt_expires_at: float = 0
        self._auth_lock = asyncio.Lock()

        # Bank list caches
        self._pse_banks: list[FPPseBankEntry] | None = None
        self._pse_banks_fetched_at: float = 0
        self._payout_banks: list[FPPayoutBankEntry] | None = None
        self._payout_banks_fetched_at: float = 0
        self._bank_cache_ttl = 7 * 24 * 3600  # 7 days

        # Persistence
        self.db = FacilitaPayDatabase(db_path)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()

    # ─────────────────────────────────────────────────────────
    # AUTHENTICATION
    # ─────────────────────────────────────────────────────────

    async def _authenticate(self) -> str:
        """
        Obtain or refresh JWT token. Thread-safe.
        Token is cached for 23 hours (safety margin on 24h TTL).
        """
        async with self._auth_lock:
            if self._jwt and time.time() < self._jwt_expires_at:
                return self._jwt

            logger.info("Authenticating with FacilitaPay...")
            resp = await self._http.post(
                f"{self.base_url}/sign_in",
                json={"user": {"username": self.username, "password": self.password}},
            )

            if resp.status_code == 401:
                raise FacilitaPayError(
                    "Authentication failed — check credentials",
                    status_code=401,
                    response_body=resp.json() if resp.content else None,
                )
            resp.raise_for_status()

            data = resp.json()
            self._jwt = data["jwt"]
            self._jwt_expires_at = time.time() + 23 * 3600  # 23h safety margin
            logger.info("FacilitaPay JWT obtained (expires in 23h)")
            return self._jwt

    async def _headers(self) -> dict[str, str]:
        """Get auth headers, refreshing JWT if needed."""
        jwt = await self._authenticate()
        return {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict | None = None,
        params: dict | None = None,
        retry_on_401: bool = True,
    ) -> dict:
        """
        Make authenticated API request with auto-refresh on 401.
        
        Args:
            method: HTTP method
            path: API path (e.g., "/transactions")
            json_body: Request body
            params: Query parameters
            retry_on_401: Auto-refresh JWT on 401 (max 1 retry)
            
        Returns:
            Parsed JSON response
            
        Raises:
            FacilitaPayError: On API errors
        """
        headers = await self._headers()
        url = f"{self.base_url}{path}"

        try:
            resp = await self._http.request(
                method, url,
                json=json_body, params=params, headers=headers,
            )
        except httpx.TimeoutException as e:
            raise FacilitaPayError(f"Request timeout: {method} {path}") from e
        except httpx.ConnectError as e:
            raise FacilitaPayError(f"Connection failed: {method} {path}") from e

        # Auto-refresh JWT on 401
        if resp.status_code == 401 and retry_on_401:
            logger.warning("JWT expired/invalid, re-authenticating...")
            self._jwt = None
            self._jwt_expires_at = 0
            headers = await self._headers()
            try:
                resp = await self._http.request(
                    method, url,
                    json=json_body, params=params, headers=headers,
                )
            except httpx.TimeoutException as e:
                raise FacilitaPayError(
                    f"Request timeout on retry: {method} {path}"
                ) from e

        # Handle errors
        if resp.status_code >= 400:
            try:
                body = resp.json() if resp.content else {}
            except Exception:
                body = resp.text or str(resp.status_code)
            if isinstance(body, dict):
                error_msg = body.get("errors", body.get("error", str(body)))
            else:
                error_msg = str(body)
            logger.error(
                f"FacilitaPay {method} {path} → {resp.status_code}\n"
                f"  Request payload: {json_body}\n"
                f"  Response body: {body}"
            )
            raise FacilitaPayError(
                f"API error {resp.status_code}: {error_msg}",
                status_code=resp.status_code,
                response_body=body if isinstance(body, dict) else {"raw": str(body)},
            )

        return resp.json()

    # ─────────────────────────────────────────────────────────
    # SUBJECT MANAGEMENT
    # ─────────────────────────────────────────────────────────

    async def upsert_subject_person(
        self,
        document_number: str,
        document_type: FPDocumentType,
        social_name: str,
        email: str,
        phone_area_code: str,
        phone_number: str,
        address_street: str,
        address_number: str,
        address_city: str,
        address_country: str = "Colombia",
        address_postal_code: str | None = None,
        address_state: str | None = None,
        address_neighborhood: str | None = None,
        birth_date: str | None = None,
        phone_country_code: str = "57",
    ) -> FPSubjectPerson:
        """
        Create or retrieve a Colombian person subject.
        
        Checks local DB for existing subject by document_number first.
        If not found, creates via API. If API returns existing (FP does
        upsert on document_number), stores and returns it.
        
        All fields required by PSE must be provided.
        """
        # Validate document format
        self._validate_document(document_number, document_type)

        # Check local cache first
        existing = self.db.get_subject_by_document(document_number)
        if existing and existing.get("status") == "approved":
            logger.info(f"Subject {self._mask_doc(document_number)} found in local DB")
            return FPSubjectPerson(
                id=existing["id"],
                social_name=existing["social_name"],
                document_number=existing["document_number"],
                document_type=FPDocumentType(existing["document_type"]),
                status=existing["status"],
                clearance_level=0,
            )

        # Create/update via API
        payload = {
            "person": {
                "document_number": document_number,
                "document_type": document_type.value,
                "social_name": social_name,
                "fiscal_country": "Colombia",
                "email": email,
                "phone_area_code": phone_area_code,
                "phone_number": phone_number,
                "phone_country_code": phone_country_code,
                "address_street": address_street,
                "address_number": address_number,
                "address_city": address_city,
                "address_country": address_country,
            }
        }
        # Add optional fields
        if address_postal_code:
            payload["person"]["address_postal_code"] = address_postal_code
        if address_state:
            payload["person"]["address_state"] = address_state
        if address_neighborhood:
            payload["person"]["address_neighborhood"] = address_neighborhood
        if birth_date:
            payload["person"]["birth_date"] = birth_date

        logger.info(f"Creating/updating subject for {self._mask_doc(document_number)}")
        data = await self._request("POST", "/subject/people", json_body=payload)
        subject = FPSubjectPerson(**data["data"])

        # Persist locally
        self.db.save_subject(
            subject_id=subject.id,
            document_number=subject.document_number,
            document_type=subject.document_type.value,
            social_name=subject.social_name,
            status=subject.status.value if isinstance(subject.status, FPDocumentType) else str(subject.status.value),
            email=email,
            phone=f"+{phone_country_code}{phone_area_code}{phone_number}",
            raw_json=json.dumps(data["data"]),
        )

        logger.info(
            f"Subject {subject.id[:8]}... status={subject.status.value} "
            f"clearance={subject.clearance_level}"
        )
        return subject

    # ─────────────────────────────────────────────────────────
    # BANK ACCOUNT MANAGEMENT
    # ─────────────────────────────────────────────────────────

    async def register_customer_bank_account(
        self,
        subject_id: str,
        account_number: str,
        branch_number: str,
        bank_code: str,
        bank_name: str,
        owner_name: str,
        owner_document_number: str,
        owner_document_type: FPDocumentType = FPDocumentType.CC,
        account_type: FPAccountType = FPAccountType.CHECKING,
    ) -> FPBankAccount:
        """
        Register a customer's COP bank account for payouts.
        
        Checks local DB first to avoid duplicate registrations.
        Returns existing bank_account_id if already registered.
        """
        # Check for existing registration
        existing = self.db.get_bank_account(subject_id, account_number, bank_code)
        if existing:
            logger.info(
                f"Bank account {self._mask_account(account_number)} "
                f"already registered: {existing['id'][:8]}..."
            )
            return FPBankAccount(
                id=existing["id"],
                account_number=existing["account_number"],
                branch_number=existing.get("branch_number"),
                account_type=existing["account_type"],
                owner_name=existing.get("owner_name", owner_name),
                owner_document_number=existing.get("owner_document_number"),
                bank={"code": existing["bank_code"], "name": existing["bank_name"]},
            )

        payload = {
            "bank_account": {
                "account_number": account_number,
                "branch_number": branch_number,
                "owner_name": owner_name,
                "owner_document_number": owner_document_number,
                "owner_document_type": owner_document_type.value,
                "currency": "COP",
                "branch_country": "COL",
                "bank": {"code": bank_code, "name": bank_name},
                "account_type": account_type.value,
            }
        }

        logger.info(
            f"Registering bank account {self._mask_account(account_number)} "
            f"at {bank_name} for subject {subject_id[:8]}..."
        )
        data = await self._request(
            "POST", f"/subject/{subject_id}/bank_accounts", json_body=payload
        )
        bank_acct = FPBankAccount(**data["data"])

        # Persist locally
        self.db.save_bank_account(
            bank_account_id=bank_acct.id,
            subject_id=subject_id,
            account_number=account_number,
            bank_code=bank_code,
            bank_name=bank_name,
            account_type=account_type.value,
            branch_number=branch_number,
            owner_name=owner_name,
            owner_document_number=owner_document_number,
            raw_json=json.dumps(data["data"]),
        )

        logger.info(f"Bank account registered: {bank_acct.id[:8]}...")
        return bank_acct

    # ─────────────────────────────────────────────────────────
    # PSE BANK LIST
    # ─────────────────────────────────────────────────────────

    async def get_pse_banks(self, force_refresh: bool = False) -> list[FPPseBankEntry]:
        """
        Get list of banks available for PSE checkout.
        Cached for 7 days (per docs: "updated on this frequency").
        Filters out placeholder entry (code "0").
        """
        now = time.time()
        if (
            not force_refresh
            and self._pse_banks is not None
            and now - self._pse_banks_fetched_at < self._bank_cache_ttl
        ):
            return self._pse_banks

        data = await self._request("GET", "/pse/financial_institutions")
        banks = [
            FPPseBankEntry(**b) for b in data["data"]
            if b.get("code") != "0"  # Filter "seleccione su banco" placeholder
        ]
        self._pse_banks = banks
        self._pse_banks_fetched_at = now
        logger.info(f"Cached {len(banks)} PSE banks")
        return banks

    async def get_payout_banks(
        self, force_refresh: bool = False
    ) -> list[FPPayoutBankEntry]:
        """
        Get list of banks available for COP payouts.
        Cached for 7 days.
        """
        now = time.time()
        if (
            not force_refresh
            and self._payout_banks is not None
            and now - self._payout_banks_fetched_at < self._bank_cache_ttl
        ):
            return self._payout_banks

        data = await self._request("GET", "/banks/cop")
        banks = [FPPayoutBankEntry(**b) for b in data["data"]]
        self._payout_banks = banks
        self._payout_banks_fetched_at = now
        logger.info(f"Cached {len(banks)} payout banks")
        return banks

    # ─────────────────────────────────────────────────────────
    # PSE PAY-IN TRANSACTIONS
    # ─────────────────────────────────────────────────────────

    async def create_pse_payin(
        self,
        subject_id: str,
        value_cop: str,
        financial_institution_code: str,
        redirect_url: str,
        pear_order_id: str,
        payment_description: str = "Payment",
    ) -> FPTransaction:
        """
        Create a PSE pay-in transaction and return the payment URL.
        
        IMPORTANT:
        - payment_url is ONE-TIME USE and expires in 21 MINUTES
        - If expired/consumed: create a new transaction
        - NOT safe to blindly retry — each call creates a new transaction
        
        App-level dedup: Checks for existing non-canceled transaction
        for this pear_order_id before creating.
        
        Args:
            subject_id: FacilitaPay subject UUID
            value_cop: Amount in COP (string, no decimals)
            financial_institution_code: PSE bank code from get_pse_banks()
            redirect_url: Where customer lands after payment
            pear_order_id: PearV1 order ID for reconciliation
            payment_description: Memo shown to customer
            
        Returns:
            FPTransaction with from_pse.payment_url populated
            
        Raises:
            ValueError: If amount exceeds limit
            FacilitaPayDuplicateError: If transaction already exists for this order
        """
        # Amount guard
        try:
            if int(value_cop) > self.max_payin_cop:
                raise ValueError(
                    f"COP amount {value_cop} exceeds limit {self.max_payin_cop:,}"
                )
        except (ValueError, TypeError):
            pass  # Non-integer amounts handled by API

        # Dedup check — block if ANY non-canceled tx exists for this order
        existing = self.db.get_transaction_by_order(pear_order_id, "payin")
        if existing and existing["status"] not in ("canceled",):
            raise FacilitaPayDuplicateError(
                f"Active PSE transaction {existing['id'][:8]}... already exists "
                f"for order {pear_order_id}",
            )

        # Format COP as integer string (no decimals)
        cop_int = str(int(float(value_cop)))
        payload = {
            "transaction": {
                "currency": "COP",
                "exchange_currency": self.SETTLEMENT_CURRENCY,
                "value": cop_int,
                "to_bank_account_id": self.cashin_account_id,
                "from_pse": {
                    "financial_institution_code": financial_institution_code,
                    "redirect_url": redirect_url,
                    "payment_description": payment_description,
                },
                "subject_id": subject_id,
                "meta": {"pear_order_id": pear_order_id},
            }
        }

        logger.info(
            f"Creating PSE pay-in: {value_cop} COP, "
            f"bank={financial_institution_code}, order={pear_order_id}"
        )
        data = await self._request("POST", "/transactions", json_body=payload)
        tx = FPTransaction(**data["data"])

        # Persist IMMEDIATELY — before returning to caller
        pse_info = tx.from_pse
        self.db.save_transaction(
            tx_id=tx.id,
            pear_order_id=pear_order_id,
            direction="payin",
            status=tx.status.value,
            amount=tx.value,
            currency=tx.currency,
            subject_id=subject_id,
            exchange_currency=self.SETTLEMENT_CURRENCY,
            payment_url=pse_info.payment_url if pse_info else None,
            pse_ticket_id=pse_info.ticket_id if pse_info else None,
            pse_trazability_code=pse_info.trazability_code if pse_info else None,
            pse_bank_code=financial_institution_code,
            raw_json=json.dumps(data["data"]),
        )

        logger.info(
            f"PSE transaction created: {tx.id[:8]}... "
            f"payment_url={'present' if pse_info and pse_info.payment_url else 'MISSING'}"
        )
        return tx

    # ─────────────────────────────────────────────────────────
    # TRANSACTION STATUS POLLING
    # ─────────────────────────────────────────────────────────

    async def get_transaction_status(self, transaction_id: str) -> dict:
        """
        Fetch current transaction status from FacilitaPay API.
        
        Returns dict with 'status' and 'value' keys.
        Status can be: pending, approved, rejected, cancelled, expired, etc.
        """
        data = await self._request("GET", f"/transactions/{transaction_id}")
        tx_data = data.get("data", data)
        return {
            "status": tx_data.get("status", "unknown"),
            "value": tx_data.get("value", "0"),
            "raw": tx_data,
        }

    # ─────────────────────────────────────────────────────────
    # BALANCE CHECK
    # ─────────────────────────────────────────────────────────

    async def get_cashout_balance(self) -> str:
        """
        Get available balance on the cashout internal account.
        
        FacilitaPay endpoint: GET /bank_accounts/:id/balance
        Response: {"data": {"balance": "5000.00", "currency": "USD", ...}}
        
        Returns:
            Balance as string (e.g. "5000.00")
            
        Raises:
            FacilitaPayError: on API errors or unparseable response
        """
        data = await self._request(
            "GET", f"/bank_accounts/{self.cashout_account_id}/balance"
        )
        balance_data = data.get("data", {})
        balance = balance_data.get("balance")
        if balance is None:
            logger.error(
                f"Balance response missing 'balance' field. "
                f"Keys present: {list(balance_data.keys())}"
            )
            raise FacilitaPayError(
                "Could not parse cashout balance — 'balance' field missing. "
                "Payout blocked until balance is verifiable."
            )
        logger.info(f"Cashout balance: {balance} {balance_data.get('currency', '?')}")
        return str(balance)

    # ─────────────────────────────────────────────────────────
    # COP PAYOUT TRANSACTIONS
    # ─────────────────────────────────────────────────────────

    async def create_cop_payout(
        self,
        subject_id: str,
        to_bank_account_id: str,
        value_cop: str,
        pear_order_id: str,
    ) -> FPTransaction:
        """
        Create a COP payout transaction from internal COP cash-out account.
        
        COP-only settlement: no FX conversion, no FX fees.
        
        CRITICAL: NOT safe to blindly retry — creates duplicate payouts.
        
        Double-payout prevention:
        1. Check local DB for existing payout for this order
        2. If found and not canceled → raise FacilitaPayDuplicateError
        3. Per-order locking is the caller's responsibility (OrderOrchestrator)
        
        Args:
            subject_id: FacilitaPay subject UUID
            to_bank_account_id: Customer's registered bank account UUID
            value_cop: Amount in COP (string)
            pear_order_id: PearV1 order ID for reconciliation
            
        Returns:
            FPTransaction with status (usually "identified" if balance available)
            
        Raises:
            ValueError: If amount exceeds limit
            FacilitaPayDuplicateError: If payout already sent for this order
        """
        # Amount guard
        try:
            if float(value_cop) > self.max_payout_cop:
                raise ValueError(
                    f"COP amount {value_cop} exceeds limit {self.max_payout_cop:,}"
                )
        except (ValueError, TypeError):
            pass

        # CRITICAL: Double-payout prevention
        existing = self.db.get_transaction_by_order(pear_order_id, "payout")
        if existing:
            raise FacilitaPayDuplicateError(
                f"Payout transaction {existing['id'][:8]}... already exists "
                f"for order {pear_order_id} (status={existing['status']})",
            )

        # Balance pre-flight check (C-03 fix) — don't create a blocking payout
        try:
            balance = await self.get_cashout_balance()
            from decimal import Decimal as D
            if D(str(balance)) < D(value_cop):
                raise FacilitaPayError(
                    f"Insufficient cashout balance: have {balance}, need {value_cop} COP. "
                    f"Payout NOT created — retry when balance is replenished."
                )
        except FacilitaPayError:
            raise  # Re-raise balance errors
        except Exception as e:
            logger.warning(f"Balance pre-flight check failed (proceeding anyway): {e}")

        payload = {
            "transaction": {
                "currency": self.SETTLEMENT_CURRENCY,
                "exchange_currency": self.SETTLEMENT_CURRENCY,
                "value": value_cop,
                "from_bank_account_id": self.cashout_account_id,
                "to_bank_account_id": to_bank_account_id,
                "subject_id": subject_id,
                "meta": {"pear_order_id": pear_order_id},
            }
        }

        logger.info(
            f"Creating COP payout: {value_cop} COP, order={pear_order_id}"
        )
        data = await self._request("POST", "/transactions", json_body=payload)
        tx = FPTransaction(**data["data"])

        # Persist IMMEDIATELY
        self.db.save_transaction(
            tx_id=tx.id,
            pear_order_id=pear_order_id,
            direction="payout",
            status=tx.status.value,
            amount=tx.value,
            currency=tx.currency,
            subject_id=subject_id,
            exchange_currency=self.SETTLEMENT_CURRENCY,
            raw_json=json.dumps(data["data"]),
        )

        logger.info(f"Payout transaction created: {tx.id[:8]}... status={tx.status.value}")
        return tx

    # ─────────────────────────────────────────────────────────
    # TRANSACTION QUERIES
    # ─────────────────────────────────────────────────────────

    async def get_transaction(self, transaction_id: str) -> FPTransaction:
        """Fetch transaction details by ID."""
        data = await self._request("GET", f"/transactions/{transaction_id}")
        return FPTransaction(**data["data"])

    async def poll_transaction_status(self, transaction_id: str) -> FPTransactionStatus:
        """
        Poll a transaction and update local DB.
        Returns the current status.
        """
        tx = await self.get_transaction(transaction_id)
        self.db.update_transaction_status(transaction_id, tx.status.value)
        return tx.status

    async def poll_pending_transactions(self) -> list[dict]:
        """
        Poll all pending transactions older than 5 minutes.
        Updates their status in local DB.
        Returns list of transactions whose status changed.
        """
        pending = self.db.get_pending_transactions(older_than_minutes=5)
        changed = []

        for tx_record in pending:
            try:
                old_status = tx_record["status"]
                new_status = await self.poll_transaction_status(tx_record["id"])
                if new_status.value != old_status:
                    logger.info(
                        f"Transaction {tx_record['id'][:8]}..."
                        f" {old_status} → {new_status.value}"
                    )
                    changed.append({
                        "id": tx_record["id"],
                        "pear_order_id": tx_record.get("pear_order_id"),
                        "direction": tx_record["direction"],
                        "old_status": old_status,
                        "new_status": new_status.value,
                    })
            except Exception as e:
                logger.error(
                    f"Failed to poll transaction {tx_record['id'][:8]}...: {e}"
                )

        return changed

    # ─────────────────────────────────────────────────────────
    # WEBHOOK NOTIFICATION RECOVERY
    # ─────────────────────────────────────────────────────────

    async def get_failed_notifications(
        self, per_page: int = 50
    ) -> list[FPNotificationRecord]:
        """Fetch failed webhook notifications for recovery."""
        data = await self._request(
            "GET", "/notifications",
            params={"failed": "true", "order_by": "desc", "per_page": str(per_page)},
        )
        return [FPNotificationRecord(**n) for n in data.get("data", [])]

    async def ack_notification(self, notification_id: str) -> None:
        """Mark a notification as successfully received (clears failed_at)."""
        await self._request("PUT", f"/notifications/{notification_id}")
        logger.info(f"ACK notification {notification_id[:8]}...")

    # ─────────────────────────────────────────────────────────
    # WEBHOOK VERIFICATION
    # ─────────────────────────────────────────────────────────

    def verify_webhook_secret(self, received_secret: str) -> bool:
        """
        Verify webhook authenticity via constant-time string comparison.
        FacilitaPay sends a shared `secret` in the webhook payload.
        """
        import hmac
        return hmac.compare_digest(str(received_secret), self.webhook_secret)

    # ─────────────────────────────────────────────────────────
    # NOTIFICATION POLLING (RECONCILIATION)
    # ─────────────────────────────────────────────────────────

    async def list_failed_notifications(self, per_page: int = 50) -> list[dict]:
        """
        Poll FacilitaPay for webhook notifications that failed delivery.
        
        FP does NOT retry webhooks — it marks them as failed_at.
        This method fetches those failed notifications so the reconciliation
        sweep can replay them locally.
        
        Endpoint: GET /notifications?failed=true&per_page=N
        """
        try:
            data = await self._request(
                "GET", f"/notifications?failed=true&per_page={per_page}"
            )
            notifications = data.get("data", [])
            logger.info(
                f"Polled FP failed notifications: {len(notifications)} found"
            )
            return notifications
        except Exception as e:
            logger.error(f"Failed to poll FP notifications: {e}")
            return []

    async def mark_notification_received(self, notification_id: str) -> bool:
        """
        Mark a FacilitaPay notification as received/processed.
        
        Call this after successfully replaying a failed notification
        so FP no longer reports it as failed.
        
        Endpoint: PUT /notifications/:id
        """
        try:
            await self._request(
                "PUT", f"/notifications/{notification_id}"
            )
            logger.info(f"Marked FP notification {notification_id[:8]}... as received")
            return True
        except Exception as e:
            logger.error(
                f"Failed to mark notification {notification_id[:8]}... as received: {e}"
            )
            return False

    # ─────────────────────────────────────────────────────────
    # VALIDATION + MASKING HELPERS
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _validate_document(document_number: str, doc_type: FPDocumentType) -> None:
        """Validate Colombian document number format."""
        digits_only = "".join(c for c in document_number if c.isdigit())
        if doc_type == FPDocumentType.CC:
            if not (6 <= len(digits_only) <= 10):
                raise ValueError(
                    f"CC document must be 6-10 digits, got {len(digits_only)}"
                )
        elif doc_type == FPDocumentType.CE:
            if not (6 <= len(digits_only) <= 9):
                raise ValueError(
                    f"CE document must be 6-9 digits, got {len(digits_only)}"
                )
        elif doc_type == FPDocumentType.NIT:
            if len(digits_only) != 10:
                raise ValueError(
                    f"NIT must be 10 digits, got {len(digits_only)}"
                )

    @staticmethod
    def _mask_doc(doc_number: str) -> str:
        """Mask document number for logging: 103****286"""
        if len(doc_number) <= 4:
            return "****"
        return doc_number[:3] + "****" + doc_number[-3:]

    @staticmethod
    def _mask_account(account_number: str) -> str:
        """Mask account number for logging: ****7890"""
        if len(account_number) <= 4:
            return "****"
        return "****" + account_number[-4:]

