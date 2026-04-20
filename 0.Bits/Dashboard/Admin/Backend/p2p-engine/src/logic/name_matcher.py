"""
NAME MATCHER MODULE
===================
Matches Binance P2P buyer names against EUR payment sender names.

HARDCODED FUZZY MATCH ONLY - No AI, no external API calls.
- All words from Binance name must exist in payment name (order-independent)
- Max 1 letter spelling difference per word allowed (Levenshtein distance)
- Reverse check: all payment words found in Binance name (for shortened bank names)

Gemini AI fallback was REMOVED after forensic audit revealed it was hallucinating
matches between completely unrelated names, causing €10K+ in false auto-releases.
"""

import re
import hashlib
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field


@dataclass
class MatchResult:
    """Result of a name matching operation."""
    matched: bool
    confidence: float  # 0.0 - 1.0
    method: str  # "hardcoded" or "gemini"
    binance_name: str
    payment_name: str
    details: str = ""
    cached: bool = False


@dataclass 
class NameMatcherCache:
    """Cache for Gemini-screened payment names to avoid re-screening."""
    screened_payments: dict[str, MatchResult] = field(default_factory=dict)
    file_path: str = "data/name_match_cache.json"
    
    def __post_init__(self):
        self._load_from_disk()
    
    def get_cache_key(self, sender_name: str, binance_name: str) -> str:
        """Generate unique cache key for name pair (sender + buyer)."""
        return f"{sender_name.lower().strip()}:{binance_name.lower().strip()}"
    
    def is_cached(self, sender_name: str, binance_name: str) -> bool:
        key = self.get_cache_key(sender_name, binance_name)
        return key in self.screened_payments
    
    def get_cached(self, sender_name: str, binance_name: str) -> MatchResult | None:
        """Get cached result if exists."""
        key = self.get_cache_key(sender_name, binance_name)
        return self.screened_payments.get(key)
    
    
    def cache_result(self, sender_name: str, binance_name: str, result: MatchResult):
        """Cache a matching result and persist to disk."""
        key = self.get_cache_key(sender_name, binance_name)
        # Only cache if NOT a temporary API error
        if result.method != "gemini_failed":
            self.screened_payments[key] = result
            self._save_to_disk()

    def _load_from_disk(self):
        import json
        import os
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    # Convert dicts back to MatchResult objects
                    for k, v in data.items():
                        self.screened_payments[k] = MatchResult(**v)
            except Exception as e:
                print(f"Failed to load name cache: {e}")

    def _save_to_disk(self):
        import json
        import dataclasses
        import os
        try:
             # Convert MatchResult objects to dicts for JSON serialization
            data = {k: dataclasses.asdict(v) for k, v in self.screened_payments.items()}
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            with open(self.file_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save name cache: {e}")


class NameMatcher:
    """
    Matches buyer names from Binance orders against sender names from EUR payments.
    Uses hardcoded Levenshtein fuzzy matching ONLY. No AI.
    """
    
    def __init__(self, gemini_api_key: str | None = None):
        # gemini_api_key param kept for backward compatibility but ignored
        self.cache = NameMatcherCache()
    
    async def match(
        self,
        binance_name: str,
        payment_name: str,
    ) -> MatchResult:
        """
        Attempt to match a Binance order name to a payment sender name.
        
        Args:
            binance_name: The buyer's name from Binance order (e.g., "Adam Bart Goldman")
            payment_name: The sender's name from EUR payment (counterparty.name)
            
        Returns:
            MatchResult with matched status and confidence
        """
        # Hardcoded fuzzy match ONLY — no AI fallback
        return self._hardcoded_match(binance_name, payment_name)
    
    # =========================================================================
    # TIER 1: HARDCODED FUZZY MATCHING
    # =========================================================================
    
    def _hardcoded_match(self, binance_name: str, payment_name: str) -> MatchResult:
        """
        Hardcoded matching logic:
        - All words from binance_name must appear in payment_name
        - Order doesn't matter
        - Max 1 letter spelling difference per word allowed
        """
        binance_words = self._normalize_and_split(binance_name)
        payment_words = self._normalize_and_split(payment_name)
        
        if not binance_words or not payment_words:
            return MatchResult(
                matched=False,
                confidence=0.0,
                method="hardcoded",
                binance_name=binance_name,
                payment_name=payment_name,
                details="Empty name(s)"
            )
        
        # Check if all Binance words exist in payment (with fuzzy tolerance)
        matched_words = 0
        unmatched = []
        
        for b_word in binance_words:
            found = False
            for p_word in payment_words:
                if self._words_match(b_word, p_word):
                    found = True
                    break
            if found:
                matched_words += 1
            else:
                unmatched.append(b_word)
        
        # All words must match
        if matched_words == len(binance_words):
            confidence = 1.0
            return MatchResult(
                matched=True,
                confidence=confidence,
                method="hardcoded",
                binance_name=binance_name,
                payment_name=payment_name,
                details=f"All {matched_words} words matched"
            )

        # REVERSE CHECK: Does the payment name (shorter) exist fully in the Binance name (longer)?
        # Example: Payment="Larry Linares", Binance="LINARES CARRION LARRY JOSE"
        # This is common when banks send shortened names.
        
        matched_payment_words = 0
        for p_word in payment_words:
            found = False
            for b_word in binance_words:
                if self._words_match(b_word, p_word):
                    found = True
                    break
            if found:
                matched_payment_words += 1
        
        # If all payment words are found in Binance name, and we have enough words (avoid single first name match)
        if len(payment_words) >= 2 and matched_payment_words == len(payment_words):
             return MatchResult(
                matched=True,
                confidence=0.95, # High confidence for full subset match
                method="hardcoded_reverse",
                binance_name=binance_name,
                payment_name=payment_name,
                details=f"All {len(payment_words)} payment words found in Binance name"
            )
        
        # Fallback to Threshold Match (>= 75% overlap)
        threshold_result = self._threshold_match(binance_words, payment_words, binance_name, payment_name)
        if threshold_result.matched:
            return threshold_result

        # Partial match - calculate confidence for logging
        confidence = matched_words / len(binance_words)
        return MatchResult(
            matched=False,
            confidence=confidence,
            method="hardcoded",
            binance_name=binance_name,
            payment_name=payment_name,
            details=f"Missing words: {', '.join(unmatched)} (Threshold fallback failed)"
        )
    
    def _normalize_and_split(self, name: str) -> list[str]:
        """Normalize name and split into words."""
        # Lowercase and remove special characters
        normalized = name.lower().strip()
        # Split on whitespace and filter empty
        words = [w.strip() for w in re.split(r'\s+', normalized) if w.strip()]
        return words
    
    def _words_match(self, word1: str, word2: str) -> bool:
        """
        Check if two words match with max 1 letter difference.
        Uses Levenshtein distance.
        """
        if word1 == word2:
            return True
        
        distance = self._levenshtein_distance(word1, word2)
        if distance <= 1:
            return True
        # Initial abbreviation: single letter matches first letter of a word
        if len(word1) == 1 and len(word2) > 1 and word1[0] == word2[0]:
            return True
        if len(word2) == 1 and len(word1) > 1 and word2[0] == word1[0]:
            return True
        return False
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _threshold_match(
        self,
        binance_words: list[str],
        payment_words: list[str],
        binance_name: str,
        payment_name: str
    ) -> MatchResult:
        """
        Calculates intersection of words.
        If >= 75% of the shorter name's words are present in the longer name,
        and at least 2 words match, it is considered valid.
        """
        shorter = min(len(binance_words), len(payment_words))
        if shorter < 2:
            return MatchResult(
                matched=False,
                confidence=0.0,
                method="threshold_match",
                binance_name=binance_name,
                payment_name=payment_name,
                details="Names too short for threshold subset match"
            )
        
        # Count matching words using fuzzy matching without double counting
        shorter_list = binance_words if len(binance_words) <= len(payment_words) else payment_words
        longer_list = payment_words if len(payment_words) >= len(binance_words) else binance_words
        
        matched_words = 0
        used_indices = set()
        
        for s_word in shorter_list:
            for idx, l_word in enumerate(longer_list):
                if idx not in used_indices and self._words_match(s_word, l_word):
                    matched_words += 1
                    used_indices.add(idx)
                    break
                    
        ratio = matched_words / shorter
        
        if matched_words >= 2 and ratio >= 0.75:
            return MatchResult(
                matched=True,
                confidence=ratio,
                method="threshold_match",
                binance_name=binance_name,
                payment_name=payment_name,
                details=f"Threshold match: {matched_words}/{shorter} words matched ({ratio:.0%})"
            )
            
        return MatchResult(
            matched=False,
            confidence=ratio,
            method="threshold_match",
            binance_name=binance_name,
            payment_name=payment_name,
            details=f"Threshold match failed: {matched_words}/{shorter} words matched ({ratio:.0%})"
        )
    
    # Gemini AI fallback REMOVED — was hallucinating matches between unrelated names
    # causing €10K+ in false auto-releases. See forensic audit 2026-04-13.


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def create_name_matcher(gemini_api_key: str | None = None) -> NameMatcher:
    """Factory function to create a NameMatcher instance."""
    return NameMatcher(gemini_api_key=gemini_api_key)
