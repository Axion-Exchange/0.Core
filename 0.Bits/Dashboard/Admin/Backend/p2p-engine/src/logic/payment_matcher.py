"""
PAYMENT MATCHER SERVICE
=======================
Matches incoming EUR payments (Januar) with pending Binance P2P orders.

RELEASE CRITERIA (tiered):

TIER 1 - REFERENCE MATCH (Primary)
   If payment reference (e.g., BI123456) matches order:
   - Name confidence reduced to 70%
   - Amount tolerance increased

TIER 2 - NAME + AMOUNT (Fallback)
   If no reference found:
   - Name confidence must be 95%+
   - Amount must be within strict tolerance
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.core.types import UnifiedOrder, UnifiedPayment
from src.logic.name_matcher import NameMatcher, MatchResult, create_name_matcher
from src.logic.amount_matcher import AmountMatcher, AmountMatchResult
from src.logic.reference_matcher import ReferenceMatcher, ReferenceMatchResult


# Thresholds
STRICT_NAME_CONFIDENCE = 0.80  # Without reference match (Lowered for AI fallback)
RELAXED_NAME_CONFIDENCE = 0.85  # With reference match (raised from 0.70 to prevent third-party bypass)


@dataclass
class ReleaseVerdict:
    """
    Combined result of reference + name + amount verification.
    
    Release logic:
    - Tier 1: Reference match -> relaxed name/amount
    - Tier 2: No reference -> strict name/amount
    """
    payment: UnifiedPayment
    order: UnifiedOrder
    
    # Individual results
    reference_result: ReferenceMatchResult
    name_result: MatchResult
    amount_result: AmountMatchResult
    
    # Ambiguity detection (B2)
    ambiguous: bool = False
    ambiguous_order_ids: list = None  # Other order IDs that also matched
    
    @property
    def reference_ok(self) -> bool:
        """Primary identifier matched."""
        return self.reference_result.matched
    
    @property
    def name_ok(self) -> bool:
        """Name matches with appropriate threshold."""
        if self.reference_ok:
            # Relaxed: 70% confidence with reference
            return self.name_result.confidence >= RELAXED_NAME_CONFIDENCE
        else:
            # Strict: 95% confidence without reference
            return self.name_result.matched and self.name_result.confidence >= STRICT_NAME_CONFIDENCE
    
    @property
    def amount_ok(self) -> bool:
        """Amount within tolerance."""
        return self.amount_result.matched
    
    @property
    def can_release(self) -> bool:
        """
        Determine if order can be released.
        
        Tier 1: Reference + (relaxed name) + amount
        Tier 2: Strict name + amount
        """
        if self.reference_ok:
            # With reference: need relaxed name + amount
            return self.name_ok and self.amount_ok
        else:
            # Without reference: need strict name + amount
            return self.name_ok and self.amount_ok
    
    @property
    def is_third_party(self) -> bool:
        """
        Detect likely third-party payment.
        
        Criteria: Reference matches + Amount matches + Name DOESN'T match
        This means someone used the correct reference but sent from
        a different bank account (not the buyer's).
        """
        return self.reference_ok and self.amount_ok and not self.name_ok
    
    @property
    def release_tier(self) -> str:
        """Which tier matched."""
        if self.can_release and self.reference_ok:
            return "TIER_1_REFERENCE"
        elif self.can_release:
            return "TIER_2_NAME_AMOUNT"
        elif self.is_third_party:
            return "THIRD_PARTY"
        else:
            return "BLOCKED"
    
    @property
    def summary(self) -> str:
        """Human-readable summary."""
        if self.can_release:
            status = f"✅ RELEASE OK ({self.release_tier})"
        else:
            status = "❌ BLOCKED"
        
        ref_icon = "✓" if self.reference_ok else "✗"
        name_icon = "✓" if self.name_ok else "✗"
        amount_icon = "✓" if self.amount_ok else "✗"
        
        threshold = f"{RELAXED_NAME_CONFIDENCE:.0%}" if self.reference_ok else f"{STRICT_NAME_CONFIDENCE:.0%}"
        
        return (
            f"{status}\n"
            f"  Ref:    {ref_icon} {self.reference_result.reason}\n"
            f"  Name:   {name_icon} {self.name_result.confidence:.0%} (threshold: {threshold})\n"
            f"  Amount: {amount_icon} {self.amount_result.reason}"
        )


class PaymentMatcher:
    """
    Matches Januar EUR payments to Binance P2P orders.
    
    Both NAME and AMOUNT must match for release approval.
    
    Flow:
    1. Get pending orders from Binance (status: PENDING / BUYER_PAID)
    2. Get incoming payments from Januar (type: PAYIN)
    3. For each payment, try to match to an order using NameMatcher
    4. For name matches, verify amount with AmountMatcher
    5. Return ReleaseVerdicts for all potential matches
    """
    
    def __init__(self, gemini_api_key: str | None = None, exchange: str = "binance"):
        self.name_matcher = create_name_matcher(gemini_api_key)
        self.amount_matcher = AmountMatcher()
        self.reference_matcher = ReferenceMatcher()
        self.exchange = exchange
    
    async def verify_release(
        self,
        order: UnifiedOrder,
        payment: UnifiedPayment,
    ) -> ReleaseVerdict:
        """
        Verify if a payment can release an order.
        
        Checks (in order):
        1. Reference match (primary identifier)
        2. Name match (buyer vs sender)
        3. Amount match (payment >= order)
        
        Tier 1: Reference match -> relaxed name (70%)
        Tier 2: No reference -> strict name (95%)
        """
        buyer_name = self._extract_buyer_name(order) or ""
        sender_name = self._extract_sender_name(payment) or ""
        
        # 1. OPTIMIZATION: Check Amount FIRST (Cheapest & Best Filter)
        amount_result = self.amount_matcher.match(order, payment)
        if not amount_result.matched:
            # Failure fast! Don't waste AI tokens on name matching
            # We can return a dummy/failed name result
            return ReleaseVerdict(
                payment=payment,
                order=order,
                reference_result=ReferenceMatchResult(
                    matched=False, 
                    reason="Skipped", 
                    reference_found=None,
                    expected_reference=None,
                    exchange=None,
                    order_suffix=None
                ),
                name_result=MatchResult(matched=False, confidence=0.0, method="skipped", binance_name="", payment_name="", details="Skipped - Amount Mismatch"),
                amount_result=amount_result
            )

        # 2. Check Reference (Fast String Match)
        reference_result = self.reference_matcher.match(order, payment, self.exchange)
        
        # 3. Check Name (Expensive AI - Only if amount matched)
        # OPTIMIZATION: Heuristic filter for obvious mismatches to save API tokens
        # Only run if we don't have a reference match (which loosens name requirements)
        should_run_ai = True
        
        from difflib import SequenceMatcher
        
        if not reference_result.matched:
            # Normalize for simple comparison
            n1 = buyer_name.lower().strip()
            n2 = sender_name.lower().strip()
            
            # Quick ratio check
            similarity = SequenceMatcher(None, n1, n2).ratio()
            
            # OPTIMIZATION REMOVED: User requested full Gemini fallback for disparate names (e.g. Cyrillic)
            # if similarity < 0.25:
            #     should_run_ai = False
            pass
                
        if should_run_ai:
            name_result = await self.name_matcher.match(
                binance_name=buyer_name,
                payment_name=sender_name,
            )
        else:
            name_result = MatchResult(
                matched=False, 
                confidence=similarity, 
                method="heuristic_skip", 
                binance_name=buyer_name, 
                payment_name=sender_name, 
                details=f"Skipped - Low similarity ({similarity:.2f})"
            )
        
        return ReleaseVerdict(
            payment=payment,
            order=order,
            reference_result=reference_result,
            name_result=name_result,
            amount_result=amount_result
        )
    
    async def find_releasable_matches(
        self,
        pending_orders: list[UnifiedOrder],
        incoming_payments: list[UnifiedPayment],
    ) -> list[ReleaseVerdict]:
        """
        Find payment-order pairs that pass BOTH name and amount checks.
        
        FIX B2: If a single payment matches 2+ orders, marks the verdict
        as ambiguous and does NOT auto-release. Returns for manual review.
        """
        releasable: list[ReleaseVerdict] = []
        matched_order_ids: set[str] = set()
        
        for payment in incoming_payments:
            sender_name = self._extract_sender_name(payment)
            
            if not sender_name:
                print(f"⚠ Payment {payment.id} has no sender name, skipping")
                continue
            
            # Collect ALL matching orders for this payment
            matching_verdicts: list[ReleaseVerdict] = []
            
            for order in pending_orders:
                if order.id in matched_order_ids:
                    continue
                
                verdict = await self.verify_release(order, payment)
                
                # DEBUG LOGGING (Unconditional)
                print(f"🔎 COMPARE: Pay({payment.amount}) vs Ord({order.fiat_amount})")
                
                if float(payment.amount) == float(order.fiat_amount):
                    buyer_name = self._extract_buyer_name(order)
                    sender_name = self._extract_sender_name(payment)
                    print(f"🔎 DEBUG MATCH: {payment.id[:6]} vs {order.external_id}")
                    print(f"   Names: '{buyer_name}' vs '{sender_name}'")
                    print(f"   Ref Match: {verdict.reference_ok} ({verdict.reference_result.reason})")
                    print(f"   Name Match: {verdict.name_result.matched} ({verdict.name_result.confidence})")
                    print(f"   Amount Match: {verdict.amount_ok} ({verdict.amount_result.reason})")
                    print(f"   Can Release: {verdict.can_release}")

                if verdict.can_release:
                    matching_verdicts.append(verdict)
            
            # FIX B2: Check for ambiguity
            if len(matching_verdicts) == 1:
                # Unambiguous — one payment, one order
                verdict = matching_verdicts[0]
                releasable.append(verdict)
                matched_order_ids.add(verdict.order.id)
                
                print(f"✅ RELEASABLE: Payment {payment.id[:8]}... -> Order {verdict.order.id}")
                print(f"   Name: {verdict.name_result.confidence:.0%}")
                print(f"   Amount: {verdict.amount_result.payment_amount} >= {verdict.amount_result.order_amount}")
                
                return releasable
            
            elif len(matching_verdicts) > 1:
                # AMBIGUOUS — same payment matches multiple orders
                order_ids = [v.order.external_id for v in matching_verdicts]
                print(f"⚠️ AMBIGUOUS MATCH: Payment {payment.id[:8]}... matches {len(matching_verdicts)} orders: {order_ids}")
                print(f"   Flagging for manual review instead of auto-releasing")
                
                # Mark the first verdict as ambiguous so caller can flag for review
                first = matching_verdicts[0]
                first.ambiguous = True
                first.ambiguous_order_ids = order_ids
                releasable.append(first)
                return releasable
        
        return releasable
    
    async def find_all_matches(
        self,
        pending_orders: list[UnifiedOrder],
        incoming_payments: list[UnifiedPayment],
    ) -> list[ReleaseVerdict]:
        """
        Find all name-matched pairs (regardless of amount).
        Useful for debugging and reviewing blocked payments.
        """
        matches: list[ReleaseVerdict] = []
        matched_order_ids: set[str] = set()
        
        for payment in incoming_payments:
            for order in pending_orders:
                if order.id in matched_order_ids:
                    continue
                
                verdict = await self.verify_release(order, payment)
                
                # Include if name matches (even if amount fails)
                if verdict.name_ok:
                    matches.append(verdict)
                    matched_order_ids.add(order.id)
                    break
        
        return matches
    
    def _extract_sender_name(self, payment: UnifiedPayment) -> str | None:
        """Extract sender name from Januar payment."""
        if hasattr(payment, 'sender_name') and payment.sender_name:
            return payment.sender_name
        
        if hasattr(payment, 'raw') and payment.raw:
            counterparty = payment.raw.get('counterparty', {})
            return counterparty.get('name')
        
        return None
    
    def _extract_buyer_name(self, order: UnifiedOrder) -> str | None:
        """Extract buyer name from Binance order."""
        # 1. Try real_name (updated from chat)
        if hasattr(order, 'counterparty') and order.counterparty:
            if order.counterparty.real_name:
                return order.counterparty.real_name
        
        # 2. Try raw buyerRealName (Binance specific)
        if hasattr(order, 'raw') and order.raw and order.raw.get('buyerRealName'):
            return order.raw.get('buyerRealName')
            
        # 3. Fallback to counterparty name (nickname/partial)
        if hasattr(order, 'counterparty') and order.counterparty and order.counterparty.name:
             return order.counterparty.name
        
        # 4. Old attribute fallback
        if hasattr(order, 'buyer_name') and order.buyer_name:
            return order.buyer_name
            
        return None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_payment_matcher(gemini_api_key: str | None = None) -> PaymentMatcher:
    """Factory function to create PaymentMatcher."""
    return PaymentMatcher(gemini_api_key=gemini_api_key)


async def verify_release(
    order: UnifiedOrder, 
    payment: UnifiedPayment,
    gemini_api_key: str | None = None
) -> ReleaseVerdict:
    """Quick helper to verify if a payment can release an order."""
    matcher = create_payment_matcher(gemini_api_key)
    return await matcher.verify_release(order, payment)
