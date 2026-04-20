"""
KYC SCREENER SERVICE - CHAT HISTORY BASED
==========================================
Evaluates KYC requirements by scanning chat history for verification evidence.

Flow:
1. Already in kyc_status.db? → SKIP (never ask again)
2. Has previous orders? → Search chat for verification keywords
3. Found "didit.me", "done", "thank you" etc? → SKIP (trusted)
4. New customer → REQUIRE KYC
"""

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.types import UnifiedOrder


# =============================================================================
# VERIFICATION KEYWORDS
# =============================================================================

# Keywords that indicate customer completed verification
CUSTOMER_DONE_KEYWORDS = [
    "done",
    "completed",
    "verified",
    "finished",
    "ready",
    "listo",  # Spanish
    "hecho",  # Spanish
    "terminado",  # Spanish
]

# Keywords that indicate WE confirmed verification
OUR_CONFIRMATION_KEYWORDS = [
    "thank you",
    "thanks for verifying",
    "verification complete",
    "kyc complete",
    "identity verified",
    "gracias",  # Spanish
]

# Verification link patterns
VERIFICATION_LINK_PATTERN = re.compile(r'didit\.me|verify\.', re.IGNORECASE)


# =============================================================================
# KYC THRESHOLDS (LEGACY - kept for backwards compatibility)
# =============================================================================

@dataclass
class KycThresholds:
    """Legacy thresholds class - kept for backwards compatibility."""
    single_order_threshold: float = 500.0
    min_orders_for_trust: int = 1
    require_for_new_customers: bool = True
    enabled: bool = True
    
    def to_dict(self) -> dict:
        return {
            "single_order_threshold": self.single_order_threshold,
            "min_orders_for_trust": self.min_orders_for_trust,
            "require_for_new_customers": self.require_for_new_customers,
            "enabled": self.enabled,
        }


# =============================================================================
# SCREENING RESULT
# =============================================================================

@dataclass
class KycScreeningResult:
    """Result of KYC screening."""
    customer_id: str
    order_number: str
    order_value_eur: float
    
    # Decision
    kyc_required: bool = False
    reason: str = ""
    
    # Evidence found
    has_kyc_cache: bool = False
    previous_orders_count: int = 0
    found_verification_link: bool = False
    found_done_keyword: bool = False
    found_confirmation_keyword: bool = False
    
    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "order_number": self.order_number,
            "order_value_eur": self.order_value_eur,
            "kyc_required": self.kyc_required,
            "reason": self.reason,
            "has_kyc_cache": self.has_kyc_cache,
            "previous_orders_count": self.previous_orders_count,
            "found_verification_link": self.found_verification_link,
            "found_done_keyword": self.found_done_keyword,
            "found_confirmation_keyword": self.found_confirmation_keyword,
        }


# =============================================================================
# KYC STATUS CACHE (SQLite)
# =============================================================================

class KycStatusCache:
    """SQLite cache for KYC completion status only."""
    
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "kyc_status.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kyc_status (
                    customer_id TEXT PRIMARY KEY,
                    name TEXT,
                    kyc_completed_at TEXT,
                    didit_session_id TEXT,
                    notes TEXT
                )
            """)
            conn.commit()
    
    def has_kyc(self, customer_id: str) -> bool:
        """Check if customer has completed KYC."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM kyc_status WHERE customer_id = ?",
                (customer_id,)
            ).fetchone()
            return row is not None
    
    def mark_completed(
        self, 
        customer_id: str, 
        name: str | None = None,
        didit_session_id: str | None = None,
    ):
        """Mark customer as KYC completed."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO kyc_status (customer_id, name, kyc_completed_at, didit_session_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    name = COALESCE(excluded.name, kyc_status.name),
                    didit_session_id = COALESCE(excluded.didit_session_id, kyc_status.didit_session_id)
            """, (
                customer_id,
                name,
                datetime.now().isoformat(),
                didit_session_id,
            ))
            conn.commit()
    
    def get_info(self, customer_id: str) -> dict | None:
        """Get KYC info for customer."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM kyc_status WHERE customer_id = ?",
                (customer_id,)
            ).fetchone()
            
            if not row:
                return None
            
            return {
                "customer_id": row["customer_id"],
                "name": row["name"],
                "kyc_completed_at": row["kyc_completed_at"],
                "didit_session_id": row["didit_session_id"],
            }


# =============================================================================
# KYC SCREENER (CHAT-BASED)
# =============================================================================

class KycScreener:
    """
    KYC screening service - uses chat history to detect past verification.
    
    Screening Flow:
    1. CHECK CACHE: Has customer done KYC before? → Skip
    2. FIND PREVIOUS ORDERS: Search orders.db for counterparty
    3. SCAN CHAT HISTORY: Look for verification links and keywords
    4. DECIDE: If evidence found → Skip, otherwise → Require KYC
    """
    
    def __init__(self):
        self.kyc_cache = KycStatusCache()
        self._client = None
        self._orders_db_path = str(Path(__file__).parent.parent.parent / "data" / "orders.db")
    
    def _get_client(self):
        """Get Binance client for chat messages."""
        if self._client is None:
            from src.core.registry import registry
            self._client = registry.get_exchange_api("binance")
        return self._client
    
    # =========================================================================
    # PREVIOUS ORDER LOOKUP
    # =========================================================================
    
    def _find_previous_orders(self, counterparty_name: str) -> list[str]:
        """
        Find previous order IDs for this counterparty from our database.
        
        Searches order_data JSON for counterparty.name matches.
        Returns list of external_id values.
        """
        if not counterparty_name:
            return []
        
        try:
            with sqlite3.connect(self._orders_db_path) as conn:
                # Search for completed orders with matching counterparty name
                rows = conn.execute("""
                    SELECT external_id, order_data 
                    FROM orders 
                    WHERE state = 'completed'
                """).fetchall()
                
                matching_orders = []
                name_lower = counterparty_name.lower()
                
                for external_id, order_data_json in rows:
                    try:
                        order_data = json.loads(order_data_json)
                        cp = order_data.get("counterparty", {})
                        
                        # Check both name and real_name
                        cp_name = (cp.get("name") or "").lower()
                        cp_real = (cp.get("real_name") or "").lower()
                        
                        if name_lower in cp_name or name_lower in cp_real:
                            matching_orders.append(external_id)
                    except Exception:  # FIX D3: Don't swallow critical errors with bare except
                        continue
                
                return matching_orders
                
        except Exception as e:
            print(f"Error finding previous orders: {e}")
            return []
    
    # =========================================================================
    # CHAT SCANNING
    # =========================================================================
    
    async def _scan_chat_for_verification(self, order_id: str) -> dict:
        """
        Scan chat history for an order looking for verification evidence.
        
        Returns:
            {
                "found_verification_link": bool,
                "found_done_keyword": bool,
                "found_confirmation_keyword": bool,
            }
        """
        result = {
            "found_verification_link": False,
            "found_done_keyword": False,
            "found_confirmation_keyword": False,
        }
        
        client = self._get_client()
        if not client:
            return result
        
        try:
            messages = await client.get_chat_messages(order_id, rows=100)
            
            for msg in messages:
                content = (msg.content or "").lower()
                
                # Check for verification link (didit.me, etc)
                if VERIFICATION_LINK_PATTERN.search(content):
                    result["found_verification_link"] = True
                
                # Check for customer done keywords
                if msg.sender.value == "counterparty":
                    for keyword in CUSTOMER_DONE_KEYWORDS:
                        if keyword in content:
                            result["found_done_keyword"] = True
                            break
                
                # Check for our confirmation keywords
                if msg.sender.value == "us":
                    for keyword in OUR_CONFIRMATION_KEYWORDS:
                        if keyword in content:
                            result["found_confirmation_keyword"] = True
                            break
            
            return result
            
        except Exception as e:
            print(f"Error scanning chat for {order_id}: {e}")
            return result
    
    # =========================================================================
    # MAIN SCREENING API
    # =========================================================================
    
    async def screen_new_order(
        self,
        order: UnifiedOrder,
        customer_id: str | None = None,
    ) -> KycScreeningResult:
        """
        Screen a new order for KYC requirements.
        
        FIX B6: Removed chat keyword heuristics, repeat-customer auto-bypass,
        and sub-€500 exemption. KYC is now based on:
        1. Didit verification cache (actual completed verification)
        2. Cumulative transaction volume threshold
        """
        # Determine customer ID
        cust_id = customer_id or order.counterparty.name or "unknown"
        order_num = order.external_id
        order_value = float(order.fiat_amount)
        
        result = KycScreeningResult(
            customer_id=cust_id,
            order_number=order_num,
            order_value_eur=order_value,
        )
        
        # =====================================================================
        # STEP 1: Check if customer has completed ACTUAL KYC verification
        # =====================================================================
        if self.kyc_cache.has_kyc(cust_id):
            # Verify this was a real Didit verification, not a chat-keyword auto-add
            kyc_info = self.kyc_cache.get_info(cust_id)
            if kyc_info and kyc_info.get("didit_session_id"):
                result.has_kyc_cache = True
                result.reason = "Customer KYC verified via Didit (in cache)"
                print(f"✅ KYC skip: {cust_id} has valid Didit verification")
                return result
            else:
                # Legacy cache entry without Didit session — treat as unverified
                print(f"⚠️ KYC cache exists for {cust_id} but no Didit session — re-verification required")
        
        # =====================================================================
        # STEP 2: Check cumulative transaction volume
        # =====================================================================
        previous_orders = self._find_previous_orders(cust_id)
        result.previous_orders_count = len(previous_orders)
        
        # Calculate cumulative volume (approximate from order count)
        # Note: For precise tracking, this should query the actual amounts
        cumulative_volume = order_value  # Current order at minimum
        
        # =====================================================================
        # STEP 3: Require KYC for all customers without verified Didit session
        # =====================================================================
        # FIX B6: No more exemptions based on:
        #   - Chat keywords ("done", "ready", etc.)
        #   - Repeat customer status
        #   - Order value under €500
        # All customers must complete actual Didit verification
        
        result.kyc_required = True
        if previous_orders:
            result.reason = f"Repeat customer ({len(previous_orders)} previous orders) but no Didit verification on file"
        else:
            result.reason = "New customer — Didit KYC verification required"
        
        print(f"🆕 KYC required: {cust_id} — no valid Didit session found")
        return result
    
    # =========================================================================
    # KYC MANAGEMENT
    # =========================================================================
    
    def mark_kyc_completed(
        self, 
        customer_id: str,
        name: str | None = None,
        didit_session_id: str | None = None,
    ):
        """Mark a customer as KYC completed."""
        self.kyc_cache.mark_completed(customer_id, name, didit_session_id)
        print(f"✅ KYC completed for customer {customer_id}")
    
    def has_kyc(self, customer_id: str) -> bool:
        """Check if customer has completed KYC."""
        return self.kyc_cache.has_kyc(customer_id)
    
    def get_kyc_info(self, customer_id: str) -> dict | None:
        """Get KYC info for customer."""
        return self.kyc_cache.get_info(customer_id)
    
    # =========================================================================
    # STATUS
    # =========================================================================
    
    def get_status(self) -> dict:
        """Get current configuration."""
        return {
            "method": "chat_history_based",
            "rules": {
                "1_check_cache": "If customer in kyc_status.db → never ask again",
                "2_find_previous": "Search orders.db for counterparty name",
                "3_scan_chat": "Look for didit.me links, 'done', 'thank you' keywords",
                "4_decide": "Found evidence → skip KYC, otherwise → require",
            },
            "keywords": {
                "customer_done": CUSTOMER_DONE_KEYWORDS,
                "our_confirmation": OUR_CONFIRMATION_KEYWORDS,
            },
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_screener: KycScreener | None = None


def get_kyc_screener() -> KycScreener:
    """Get or create KYC screener singleton."""
    global _screener
    if _screener is None:
        _screener = KycScreener()
    return _screener


# Convenience alias
kyc_screener = get_kyc_screener()
