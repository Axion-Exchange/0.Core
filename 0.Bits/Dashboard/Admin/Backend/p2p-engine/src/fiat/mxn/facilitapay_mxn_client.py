"""
FacilitaPay MXN Client
======================
MXN-specific operations using the Attrus (FacilitaPay) API:
- Dynamic CLABE pay-in (SPEI)
- SPEI payout
- Mexican subject registration (CURP/RFC)

Uses the SAME authentication as the COP client (shared FP account).
Settlement currency: MXN (no FX conversion).
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from .facilitapay_mxn_persistence import FacilitaPayMXNDatabase

logger = logging.getLogger("fp_mxn")


class FacilitaPayMXNError(Exception):
    def __init__(self, message: str, status_code: int | None = None,
                 response_body: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FacilitaPayMXNDuplicateError(FacilitaPayMXNError):
    pass


@dataclass
class MXNTransaction:
    id: str
    status: str
    currency: str
    value: str
    dynamic_clabe: Optional[str] = None
    meta: Optional[dict] = None

    @classmethod
    def from_api(cls, data: dict) -> "MXNTransaction":
        """Parse transaction from API response."""
        # Extract dynamic_clabe from payment_info or from_spei
        dynamic_clabe = None
        payment_info = data.get("payment_info", {})
        if payment_info:
            dynamic_clabe = payment_info.get("dynamic_clabe")
        from_spei = data.get("from_spei", {})
        if from_spei and not dynamic_clabe:
            dynamic_clabe = from_spei.get("dynamic_clabe")

        return cls(
            id=data["id"],
            status=data.get("status", "pending"),
            currency=data.get("currency", "MXN"),
            value=str(data.get("value", "0")),
            dynamic_clabe=dynamic_clabe,
            meta=data.get("meta"),
        )


class FacilitaPayMXNClient:
    """FacilitaPay client for MXN (SPEI/Dynamic CLABE) operations."""

    SETTLEMENT_CURRENCY = "MXN"

    def __init__(
        self,
        username: str,
        password: str,
        cashin_account_id: str,
        cashout_account_id: str,
        webhook_secret: str = "",
        base_url: str = "https://api.facilitapay.com/api/v1",
        db_path: str = "data/facilitapay_mxn.db",
        max_payin_mxn: int = 500_000,
        max_payout_mxn: int = 500_000,
    ):
        self.username = username
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.cashin_account_id = cashin_account_id
        self.cashout_account_id = cashout_account_id
        self.webhook_secret = webhook_secret
        self.max_payin_mxn = max_payin_mxn
        self.max_payout_mxn = max_payout_mxn

        assert self.SETTLEMENT_CURRENCY == "MXN", (
            f"SETTLEMENT_CURRENCY must be MXN, got {self.SETTLEMENT_CURRENCY}"
        )

        if not webhook_secret:
            logger.critical(
                "🚨 FACILITAPAY_WEBHOOK_SECRET is NOT SET! "
                "All incoming webhooks will be REJECTED (fail-closed)."
            )
        if not cashin_account_id:
            logger.warning("⚠️ FACILITAPAY_MXN_CASH_IN_ACCOUNT_ID is not set")

        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

        # JWT state
        self._jwt: str | None = None
        self._jwt_expires_at: float = 0
        self._auth_lock = asyncio.Lock()

        # Persistence
        self.db = FacilitaPayMXNDatabase(db_path)

    async def close(self) -> None:
        await self._http.aclose()

    # ─── AUTHENTICATION ───────────────────────────────────────

    async def _authenticate(self) -> str:
        async with self._auth_lock:
            if self._jwt and time.time() < self._jwt_expires_at:
                return self._jwt

            logger.info("Authenticating with FacilitaPay (MXN)...")
            resp = await self._http.post(
                f"{self.base_url}/sign_in",
                json={"user": {"username": self.username, "password": self.password}},
            )

            if resp.status_code == 401:
                raise FacilitaPayMXNError(
                    "Authentication failed — check credentials",
                    status_code=401,
                )
            resp.raise_for_status()

            data = resp.json()
            self._jwt = data["jwt"]
            self._jwt_expires_at = time.time() + 23 * 3600
            logger.info("FacilitaPay MXN JWT obtained (expires in 23h)")
            return self._jwt

    async def _headers(self) -> dict[str, str]:
        jwt = await self._authenticate()
        return {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str,
                       json_body: dict | None = None,
                       params: dict | None = None,
                       retry_on_401: bool = True) -> dict:
        headers = await self._headers()
        url = f"{self.base_url}{path}"

        try:
            resp = await self._http.request(
                method, url, json=json_body, params=params, headers=headers,
            )
        except httpx.TimeoutException as e:
            raise FacilitaPayMXNError(f"Request timeout: {method} {path}") from e
        except httpx.ConnectError as e:
            raise FacilitaPayMXNError(f"Connection failed: {method} {path}") from e

        if resp.status_code == 401 and retry_on_401:
            logger.warning("JWT expired/invalid, re-authenticating...")
            self._jwt = None
            self._jwt_expires_at = 0
            headers = await self._headers()
            try:
                resp = await self._http.request(
                    method, url, json=json_body, params=params, headers=headers,
                )
            except httpx.TimeoutException as e:
                raise FacilitaPayMXNError(f"Timeout on retry: {method} {path}") from e

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
                f"FacilitaPay MXN {method} {path} → {resp.status_code}\n"
                f"  Request: {json_body}\n  Response: {body}"
            )
            raise FacilitaPayMXNError(
                f"API error {resp.status_code}: {error_msg}",
                status_code=resp.status_code,
                response_body=body if isinstance(body, dict) else {"raw": str(body)},
            )

        return resp.json()

    # ─── SUBJECT MANAGEMENT (CURP) ────────────────────────────

    async def upsert_mexican_subject(
        self,
        curp: str,
        social_name: str,
        email: str = "noreply@axion.exchange",
        rfc_pf: str | None = None,
        phone_area_code: str = "55",
        phone_number: str = "00000000",
        phone_country_code: str = "52",
        address_street: str = "No registrada",
        address_number: str = "0",
        address_city: str = "Ciudad de Mexico",
        address_country: str = "Mexico",
    ) -> str:
        """
        Register or retrieve a Mexican person subject via CURP.

        Returns subject_id.
        """
        # Check local cache first
        existing = self.db.get_subject_by_document(curp)
        if existing and existing.get("status") == "approved":
            logger.info(f"MXN subject {curp[:4]}*** found in local DB")
            return existing["id"]

        payload = {
            "person": {
                "document_number": curp,
                "document_type": "curp",
                "social_name": social_name,
                "email": email,
                "fiscal_country": "Mexico",
                "phone_country_code": phone_country_code,
                "phone_area_code": phone_area_code,
                "phone_number": phone_number,
                "address_street": address_street,
                "address_number": address_number,
                "address_city": address_city,
                "address_country": address_country,
            }
        }
        if rfc_pf:
            payload["person"]["rfc_pf"] = rfc_pf

        logger.info(f"Registering MXN subject: {curp[:4]}***")
        data = await self._request("POST", "/subject/people", json_body=payload)
        subject_data = data.get("data", data)
        subject_id = subject_data["id"]

        self.db.save_subject(
            subject_id=subject_id,
            document_number=curp,
            social_name=social_name,
            email=email,
            rfc=rfc_pf,
            status="approved",
            raw_json=json.dumps(subject_data),
        )

        logger.info(f"MXN subject registered: {subject_id[:8]}...")
        return subject_id

    # ─── DYNAMIC CLABE PAY-IN ─────────────────────────────────

    async def create_dynamic_clabe_payin(
        self,
        subject_id: str,
        value_mxn: str,
        pear_order_id: str,
        payment_description: str = "Payment",
    ) -> MXNTransaction:
        """
        Create a Dynamic CLABE pay-in transaction.

        Returns MXNTransaction with dynamic_clabe populated.
        The CLABE is unique per transaction and valid for 30 days.
        Customer sends SPEI to this CLABE and payment is auto-reconciled.

        Dedup: checks for existing non-canceled tx for this order.
        """
        # Amount guard
        try:
            if float(value_mxn) > self.max_payin_mxn:
                raise ValueError(f"MXN amount {value_mxn} exceeds limit {self.max_payin_mxn:,}")
        except (ValueError, TypeError):
            pass

        # Dedup check
        existing = self.db.get_transaction_by_order(pear_order_id, "payin")
        if existing and existing["status"] not in ("canceled",):
            raise FacilitaPayMXNDuplicateError(
                f"Active CLABE transaction {existing['id'][:8]}... already exists "
                f"for order {pear_order_id}",
            )

        # Format MXN amount (2 decimal places)
        mxn_formatted = f"{float(value_mxn):.2f}"

        payload = {
            "transaction": {
                "currency": "MXN",
                "exchange_currency": self.SETTLEMENT_CURRENCY,
                "value": mxn_formatted,
                "from_spei": {"dynamic_clabe": True},
                "to_bank_account_id": self.cashin_account_id,
                "subject_id": subject_id,
                "meta": {"pear_order_id": pear_order_id},
                "payment_description": payment_description,
            }
        }

        logger.info(
            f"Creating Dynamic CLABE pay-in: {value_mxn} MXN, order={pear_order_id}"
        )
        data = await self._request("POST", "/transactions", json_body=payload)
        tx = MXNTransaction.from_api(data.get("data", data))

        # Persist IMMEDIATELY
        self.db.save_transaction(
            tx_id=tx.id,
            pear_order_id=pear_order_id,
            direction="payin",
            status=tx.status,
            amount=tx.value,
            currency="MXN",
            subject_id=subject_id,
            dynamic_clabe=tx.dynamic_clabe,
            raw_json=json.dumps(data.get("data", data)),
        )

        logger.info(
            f"CLABE transaction created: {tx.id[:8]}... "
            f"clabe={'present' if tx.dynamic_clabe else 'MISSING'}"
        )
        return tx

    # ─── SPEI PAYOUT ──────────────────────────────────────────

    async def register_mexican_bank_account(
        self,
        subject_id: str,
        clabe: str,
        owner_name: str,
        owner_curp: str,
    ) -> str:
        """
        Register a Mexican CLABE for payout.
        CLABE encodes bank (1-3) + branch (4-6) + account (7-17) + check (18).

        Returns bank_account_id.
        """
        # Check local cache
        existing = self.db.get_bank_account_by_clabe(clabe)
        if existing:
            logger.info(f"Bank account for CLABE ***{clabe[-4:]} found in local DB")
            return existing["id"]

        bank_code = clabe[:3]
        branch_number = clabe[3:6]

        payload = {
            "bank_account": {
                "account_number": clabe,
                "bank_code": bank_code,
                "bank_name": f"Bank {bank_code}",
                "branch_number": branch_number,
                "account_type": "conta-corrente",
                "owner_name": owner_name,
                "owner_document_number": owner_curp,
            }
        }

        logger.info(f"Registering MXN bank account CLABE ***{clabe[-4:]} for subject {subject_id[:8]}...")
        data = await self._request(
            "POST", f"/subject/{subject_id}/bank_accounts", json_body=payload
        )
        bank_acct_data = data.get("data", data)
        bank_account_id = bank_acct_data["id"]

        self.db.save_bank_account(
            bank_account_id=bank_account_id,
            subject_id=subject_id,
            clabe=clabe,
            bank_code=bank_code,
            owner_name=owner_name,
            owner_document_number=owner_curp,
            raw_json=json.dumps(bank_acct_data),
        )

        logger.info(f"MXN bank account registered: {bank_account_id[:8]}...")
        return bank_account_id

    async def create_spei_payout(
        self,
        subject_id: str,
        bank_account_id: str,
        value_mxn: str,
        pear_order_id: str,
        payment_description: str = "Payout",
    ) -> MXNTransaction:
        """
        Create a SPEI payout transaction.

        Dedup: checks for existing non-canceled payout for this order.
        """
        # Amount guard
        try:
            if float(value_mxn) > self.max_payout_mxn:
                raise ValueError(f"MXN payout {value_mxn} exceeds limit {self.max_payout_mxn:,}")
        except (ValueError, TypeError):
            pass

        # Dedup check
        existing = self.db.get_transaction_by_order(pear_order_id, "payout")
        if existing and existing["status"] not in ("canceled",):
            raise FacilitaPayMXNDuplicateError(
                f"Active payout {existing['id'][:8]}... already exists for order {pear_order_id}",
            )

        mxn_formatted = f"{float(value_mxn):.2f}"

        payload = {
            "transaction": {
                "currency": "MXN",
                "exchange_currency": self.SETTLEMENT_CURRENCY,
                "value": mxn_formatted,
                "from_bank_account_id": self.cashout_account_id,
                "to_bank_account_id": bank_account_id,
                "subject_id": subject_id,
                "meta": {"pear_order_id": pear_order_id},
                "payment_description": payment_description,
            }
        }

        logger.info(f"Creating SPEI payout: {value_mxn} MXN, order={pear_order_id}")
        data = await self._request("POST", "/transactions", json_body=payload)
        tx = MXNTransaction.from_api(data.get("data", data))

        self.db.save_transaction(
            tx_id=tx.id,
            pear_order_id=pear_order_id,
            direction="payout",
            status=tx.status,
            amount=tx.value,
            currency="MXN",
            subject_id=subject_id,
            raw_json=json.dumps(data.get("data", data)),
        )

        logger.info(f"SPEI payout created: {tx.id[:8]}... status={tx.status}")
        return tx

    # ─── TRANSACTION QUERIES ──────────────────────────────────

    async def get_transaction(self, transaction_id: str) -> MXNTransaction:
        data = await self._request("GET", f"/transactions/{transaction_id}")
        return MXNTransaction.from_api(data.get("data", data))

    async def poll_transaction_status(self, transaction_id: str) -> str:
        tx = await self.get_transaction(transaction_id)
        self.db.update_transaction_status(transaction_id, tx.status)
        return tx.status

    # ─── WEBHOOK VERIFICATION ─────────────────────────────────

    def verify_webhook_secret(self, received_secret: str) -> bool:
        import hmac
        return hmac.compare_digest(str(received_secret), self.webhook_secret)
