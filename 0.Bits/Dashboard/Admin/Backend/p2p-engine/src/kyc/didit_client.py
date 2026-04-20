"""
DIDIT KYC CLIENT
====================
Integration with Didit for KYC/AML verification.

Uses internal order number (e.g., BIN-12345678) as vendor_data to link
KYC sessions back to P2P orders. This ID is visible in Didit dashboard.

API: https://verification.didit.me
Auth: X-Api-Key header
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx

from src.core.types import (
    KycSession, 
    KycStatus, 
    ExchangeId, 
    UnifiedOrder,
    make_internal_order_number,
)


class DiditClient:
    """
    Didit KYC/AML service client.
    
    Creates verification sessions with internal order number as vendor_data,
    allowing sessions to be matched back to orders.
    
    Usage:
        client = didit_client()
        
        # Create session for an order
        session = await client.create_kyc_session_for_order(order)
        print(session.link)  # "https://verify.didit.me/..."
        print(session.order_id)  # "BIN-12345678"
    """
    
    # Production API
    BASE_URL = "https://verification.didit.me"
    
    # Default workflow (KYC + AML)
    DEFAULT_WORKFLOW_ID = "43c2ff63-a867-4692-b025-b922e7209a9c"
    
    def __init__(
        self,
        api_key: str,
        app_id: str | None = None,
        workflow_id: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize Didit client.
        
        Args:
            api_key: Didit API key (X-Api-Key header)
            app_id: Optional app ID for reference
            workflow_id: Verification workflow ID (defaults to KYC+AML)
            base_url: Optional base URL override
        """
        self.api_key = api_key
        self.app_id = app_id or "4f16900b-270b-48e8-b7d6-9ca34bfec14b"
        self.workflow_id = workflow_id or self.DEFAULT_WORKFLOW_ID
        self.base_url = base_url or self.BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Cache of sessions by internal order number
        self._sessions_by_order: dict[str, KycSession] = {}
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict:
        """Make Didit API request."""
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = await self.client.get(
                    url,
                    headers=headers,
                    params=params
                )
            else:
                response = await self.client.post(
                    url,
                    headers=headers,
                    json=data
                )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            print(f"Didit API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Didit request failed: {e}")
            raise
    
    # =========================================================================
    # SESSION CREATION - PRIMARY API
    # =========================================================================
    
    async def create_kyc_session_for_order(
        self,
        order: UnifiedOrder,
        callback_url: str | None = None,
    ) -> KycSession:
        """
        Create a KYC session for an order.
        
        Uses the internal order number (e.g., BIN-12345678) as Didit vendor_data.
        
        Args:
            order: The P2P order requiring KYC
            callback_url: URL to redirect after verification
            
        Returns:
            KycSession with .link ready for use
        """
        internal_order_number = order.internal_order_number
        
        return await self.create_kyc_session(
            exchange=order.exchange,
            order_id=order.external_id,
            callback_url=callback_url,
        )
    
    async def create_kyc_session(
        self,
        exchange: ExchangeId | str,
        order_id: str,
        callback_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KycSession:
        """
        Create a new KYC verification session.
        
        Args:
            exchange: Exchange identifier (binance, bybit, etc.)
            order_id: External order ID from exchange
            callback_url: URL to redirect after verification
            metadata: Additional metadata to store
            
        Returns:
            KycSession with verification link
        """
        # Generate internal order number (e.g., BIN-12345678)
        internal_order_number = make_internal_order_number(exchange, order_id)
        
        # Build request body
        body: dict[str, Any] = {
            "workflow_id": self.workflow_id,
            "vendor_data": internal_order_number,  # Visible in Didit dashboard
        }
        
        if callback_url:
            body["callback"] = callback_url
            body["callback_method"] = "both"
        
        if metadata:
            body["metadata"] = str(metadata)
        
        try:
            response = await self._request("POST", "/v2/session/", data=body)
            
            # Parse response
            session_id = response.get("session_id", response.get("id", ""))
            verification_url = response.get("url", response.get("verification_url", ""))
            
            # Determine exchange enum
            if isinstance(exchange, str):
                try:
                    exchange_enum = ExchangeId(exchange.lower())
                except ValueError:
                    exchange_enum = None
            else:
                exchange_enum = exchange
            
            session = KycSession(
                id=f"kyc_{uuid4().hex[:12]}",
                external_id=session_id,
                status=KycStatus.PENDING,
                link=verification_url,
                order_id=internal_order_number,  # Store internal order number
                exchange=exchange_enum,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24),
                raw=response,
            )
            
            # Cache by internal order number
            self._sessions_by_order[internal_order_number] = session
            
            print(f"✅ Created KYC session for {internal_order_number}")
            print(f"   Link: {verification_url}")
            return session
            
        except Exception as e:
            print(f"❌ Failed to create KYC session: {e}")
            raise
    
    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    async def generate_kyc_link(
        self,
        exchange: ExchangeId | str,
        order_id: str,
    ) -> str | None:
        """
        Generate just the KYC link URL for an order.
        
        Returns:
            Verification URL string, or None on failure
        """
        try:
            session = await self.create_kyc_session(exchange, order_id)
            return session.link
        except Exception:
            return None
    
    def get_cached_session(self, internal_order_number: str) -> KycSession | None:
        """
        Get a cached session by internal order number.
        
        Args:
            internal_order_number: e.g., "BIN-12345678"
            
        Returns:
            KycSession if cached, None otherwise
        """
        return self._sessions_by_order.get(internal_order_number)
    
    # =========================================================================
    # SESSION STATUS
    # =========================================================================
    
    async def get_session_status(self, session_id: str) -> KycSession | None:
        """
        Check the status of a KYC session.
        
        Args:
            session_id: Didit session ID (external_id)
            
        Returns:
            Updated KycSession or None if not found
        """
        try:
            response = await self._request("GET", f"/v2/session/{session_id}/")
            
            status_str = response.get("status", "pending").lower()
            status = self._map_status(status_str)
            
            # Find in cache by session_id
            session = None
            for order_num, cached in self._sessions_by_order.items():
                if cached.external_id == session_id:
                    session = cached
                    session.status = status
                    break
            
            if not session:
                # Create minimal session from response
                session = KycSession(
                    id=f"kyc_{uuid4().hex[:12]}",
                    external_id=session_id,
                    status=status,
                    link=response.get("url", ""),
                    order_id=response.get("vendor_data", ""),  # Internal order number
                    exchange=None,
                    created_at=datetime.now(),
                    raw=response,
                )
            
            return session
            
        except Exception as e:
            print(f"Error getting session status: {e}")
            return None
    
    async def refresh_session(self, internal_order_number: str) -> KycSession | None:
        """
        Refresh session status by internal order number.
        
        Args:
            internal_order_number: e.g., "BIN-12345678"
            
        Returns:
            Updated KycSession or None
        """
        session = self._sessions_by_order.get(internal_order_number)
        if not session:
            return None
        
        return await self.get_session_status(session.external_id)
    
    # =========================================================================
    # VERIFICATION RESULT
    # =========================================================================
    
    async def get_verification_result(self, session_id: str) -> dict[str, Any] | None:
        """
        Get full verification result including extracted data.
        
        Args:
            session_id: Didit session ID
            
        Returns:
            Dict with verification data (name, document, etc.)
        """
        try:
            response = await self._request("GET", f"/v2/session/{session_id}/decision/")
            return response
        except Exception as e:
            print(f"Error getting verification result: {e}")
            return None
    
    async def get_verified_name(self, session_id: str) -> str | None:
        """
        Extract the verified real name from a completed session.
        
        Args:
            session_id: Didit session ID
            
        Returns:
            Verified name or None
        """
        result = await self.get_verification_result(session_id)
        if not result:
            return None
        
        # Try different paths for name extraction
        person = result.get("person", {})
        name = person.get("full_name") or person.get("name")
        
        if not name:
            # Try document data
            document = result.get("document", {})
            first = document.get("first_name", "")
            last = document.get("last_name", "")
            name = f"{first} {last}".strip()
        
        return name if name else None
    
    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================
    
    async def check_pending_sessions(self) -> list[KycSession]:
        """
        Check all pending sessions and return those with status changes.
        
        Returns:
            List of sessions with updated status
        """
        updated = []
        
        for order_num, session in list(self._sessions_by_order.items()):
            if session.status == KycStatus.PENDING:
                refreshed = await self.get_session_status(session.external_id)
                if refreshed and refreshed.status != KycStatus.PENDING:
                    updated.append(refreshed)
                    self._sessions_by_order[order_num] = refreshed
        
        return updated
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _map_status(self, didit_status: str) -> KycStatus:
        """Map Didit status string to KycStatus enum."""
        mapping = {
            "pending": KycStatus.PENDING,
            "in_review": KycStatus.PENDING,
            "approved": KycStatus.APPROVED,
            "declined": KycStatus.REJECTED,
            "rejected": KycStatus.REJECTED,
            "expired": KycStatus.EXPIRED,
        }
        return mapping.get(didit_status.lower(), KycStatus.PENDING)
    
    def is_approved(self, session: KycSession) -> bool:
        """Check if session is approved."""
        return session.status == KycStatus.APPROVED


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

def get_didit_client() -> DiditClient | None:
    """Get DiDit client from environment."""
    api_key = os.getenv("DIDIT_API_KEY")
    if not api_key:
        return None
    
    return DiditClient(
        api_key=api_key,
        app_id=os.getenv("DIDIT_APP_ID"),
        workflow_id=os.getenv("DIDIT_WORKFLOW_ID"),
        base_url=os.getenv("DIDIT_BASE_URL"),
    )


# Lazy singleton
_didit_instance: DiditClient | None = None

def didit_client() -> DiditClient | None:
    """Get or create DiDit client singleton."""
    global _didit_instance
    if _didit_instance is None:
        _didit_instance = get_didit_client()
    return _didit_instance


# =============================================================================
# KYC THRESHOLD MANAGER (LEGACY EXPORTS)
# =============================================================================
# These classes have been moved to src/services/kyc_screener.py
# Re-exported here for backward compatibility

from src.services.kyc_screener import (
    KycThresholds,
    KycScreeningResult,
    KycStatusCache,
    KycScreener as KycThresholdManager,
    get_kyc_screener as kyc_manager,
    get_kyc_screener as get_kyc_manager,
)
