"""
COP Info Extractor
==================
AI-powered (Gemini) + regex fallback extraction of customer info from
Binance P2P chat messages. Also includes Colombian CC validation and
bank name matching.

Extracted from cop_standalone.py for PearV2.
"""

import os
import re
import json
import logging
from typing import Optional
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CustomerInfo:
    """Extracted customer information from chat messages."""
    name: Optional[str] = None
    cc: Optional[str] = None
    cc_type: Optional[str] = None  # "cc" or "ce"
    email: Optional[str] = None
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None
    # BUY-specific fields
    account_number: Optional[str] = None
    account_type: Optional[str] = None  # "savings" or "checking"

    def is_complete(self) -> bool:
        """Check if SELL flow info is complete."""
        return all([self.name, self.cc, self.email, self.bank_code])

    def is_complete_for_buy(self) -> bool:
        """Check if BUY flow info is complete (no email or account_type needed — account_type is hardcoded)."""
        return all([self.name, self.cc, self.bank_code, self.account_number])

    def missing_fields(self) -> list[str]:
        missing = []
        if not self.name: missing.append("nombre completo")
        if not self.cc: missing.append("cédula")
        if not self.email: missing.append("correo electrónico")
        if not self.bank_code: missing.append("banco")
        return missing

    def missing_buy_fields(self) -> list[str]:
        missing = []
        if not self.name: missing.append("nombre completo")
        if not self.cc: missing.append("cédula")
        if not self.bank_code: missing.append("banco")
        if not self.account_number: missing.append("número de cuenta")
        # account_type is hardcoded — not requested from customer
        return missing


# ============================================================================
# Colombian Bank Aliases → PSE codes
# ============================================================================

BANK_ALIASES: dict[str, str] = {
    "bancolombia": "1007", "banco colombia": "1007", "bancolmbia": "1007",
    "davivienda": "1051", "davivenda": "1051", "davi": "1051",
    "nequi": "1507", "nequy": "1507",
    "daviplata": "1551", "davi plata": "1551",
    "bbva": "1013", "bbva colombia": "1013",
    "banco de bogota": "1001", "banco bogota": "1001", "bogota": "1001",
    "banco de occidente": "1023", "occidente": "1023",
    "colpatria": "1019", "scotiabank": "1019",
    "av villas": "1052", "avvillas": "1052",
    "banco agrario": "1040", "agrario": "1040",
    "caja social": "1032", "bcsc": "1032",
    "pichincha": "1060",
    "popular": "1002", "banco popular": "1002",
    "nu": "1809", "nubank": "1809",
    "rappipay": "1811", "rappi": "1811",
    "itau": "1006",
    "gnb": "1012", "gnb sudameris": "1012",
    "falabella": "1062",
    "lulo": "1070", "lulo bank": "1070",
    "movii": "1801",
    "uala": "1804",
    "coink": "1812",
    "global66": "1814",
}


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_colombian_cc(raw_input: str) -> tuple[bool, str, str]:
    """
    Validate Colombian CC/CE document number.
    Returns (valid, normalized_number, document_type_or_error).
    """
    cleaned = re.sub(r'[^0-9]', '', str(raw_input))
    if not cleaned:
        return False, "", "No digits found"
    if len(cleaned) < 6:
        return False, cleaned, f"Too short ({len(cleaned)} digits, min 6)"
    if len(cleaned) > 10:
        return False, cleaned, f"Too long ({len(cleaned)} digits, max 10)"
    if cleaned[0] == '0':
        return False, cleaned, "Cannot start with 0"

    fake_patterns = [r'^(\d)\1{5,}$', r'^1234567890$', r'^0987654321$']
    for p in fake_patterns:
        if re.match(p, cleaned):
            return False, cleaned, "Invalid number"

    doc_type = "cc" if len(cleaned) >= 8 else "ce"
    return True, cleaned, doc_type


def match_bank_name(input_name: str) -> tuple[Optional[str], Optional[str]]:
    """Match user input to bank code. Returns (code, name) or (None, None)."""
    if not input_name:
        return None, None
    input_lower = input_name.strip().lower()
    if input_lower in BANK_ALIASES:
        code = BANK_ALIASES[input_lower]
        return code, input_lower.title()
    for alias, code in BANK_ALIASES.items():
        if alias in input_lower or input_lower in alias:
            return code, alias.title()
    return None, None


# ============================================================================
# Regex-First Extractor (AI optional)
# ============================================================================

class COPInfoExtractor:
    """Regex-first customer info extractor. AI (Gemini) only used when explicitly enabled."""

    def __init__(self, gemini_api_key: str = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        # AI is OFF by default — only enabled via USE_AI_EXTRACTION=true
        self.use_ai = os.getenv("USE_AI_EXTRACTION", "false").lower() == "true"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def extract(self, messages: list[str], previous: CustomerInfo = None,
                       force_regex: bool = False) -> CustomerInfo:
        """Extract customer info from chat messages, merging with previous if available.

        Args:
            force_regex: If True, always use regex (skip AI). Used by BUY flow
                         because AI prompt doesn't extract account_number/account_type.
        """
        combined = "\n".join(messages)
        # Regex is PRIMARY — AI only used when explicitly enabled AND not forced off
        if self.use_ai and self.api_key and not force_regex:
            info = await self._ai_extract(combined)
        else:
            info = self._regex_extract(combined)

        if previous:
            info = CustomerInfo(
                name=info.name or previous.name,
                cc=info.cc or previous.cc,
                cc_type=info.cc_type or previous.cc_type,
                email=info.email or previous.email,
                bank_code=info.bank_code or previous.bank_code,
                bank_name=info.bank_name or previous.bank_name,
                account_number=info.account_number or previous.account_number,
                account_type=info.account_type or previous.account_type,
            )

        # Validate CC
        if info.cc:
            valid, normalized, result = validate_colombian_cc(info.cc)
            if valid:
                info.cc = normalized
                info.cc_type = result
            else:
                info.cc = None

        # Validate email
        if info.email and not re.match(r'^[\w\.\-\+]+@[\w\.\-]+\.\w{2,}$', info.email):
            info.email = None

        # Match bank
        if info.bank_name and not info.bank_code:
            code, name = match_bank_name(info.bank_name)
            if code:
                info.bank_code = code
                info.bank_name = name

        return info

    async def _ai_extract(self, text: str) -> CustomerInfo:
        prompt = f"""Extract customer information from the following text. The customer may have sent this in any format, possibly with typos or across multiple messages.

TEXT:
{text}

Extract these fields:
1. name: Full name (e.g., "Juan Pablo Perez Garcia")
2. cc: Colombian Cedula - ONLY DIGITS, 6-10 digits. Remove any letters or dashes.
3. email: Email address - must contain @ and look like a valid email
4. bank: Bank name - recognize Colombian banks like Bancolombia, Davivienda, BBVA, Nequi, Daviplata, etc.

If a field is unclear or not found, return null for that field.
If there's a typo you can confidently fix (e.g., "Bancolmbia" -> "Bancolombia"), fix it.

Respond in JSON format only, no markdown:
{{"name": "...", "cc": "...", "email": "...", "bank": "..."}}"""

        try:
            response = await self.client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()
            text_response = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            text_response = text_response.strip()
            if text_response.startswith("```"):
                text_response = re.sub(r'^```\w*\n?', '', text_response)
                text_response = re.sub(r'\n?```$', '', text_response)

            data = json.loads(text_response)

            cc = data.get("cc")
            if cc:
                cc = re.sub(r'[^0-9]', '', str(cc))

            bank_name = data.get("bank")
            bank_code = None
            if bank_name:
                bank_code, bank_name = match_bank_name(bank_name)

            return CustomerInfo(
                name=data.get("name"),
                cc=cc,
                email=data.get("email"),
                bank_code=bank_code,
                bank_name=bank_name,
            )
        except Exception as e:
            logger.error(f"Gemini extraction error: {e}")
            return self._regex_extract(text)

    def _regex_extract(self, text: str) -> CustomerInfo:
        """Regex-based fallback extraction when Gemini API is unavailable."""
        info = CustomerInfo()

        # Pre-filter: remove system/bot messages before extraction
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip JSON system messages from Binance
            if stripped.startswith('{') and 'type' in stripped.lower():
                continue
            # Skip bot's own message templates
            if any(stripped.startswith(p) for p in ['¡Hola!', '[OK]', '[!]', '⚠️', 'Enlace',
                                                     'Operamos', 'Tu enlace']):
                continue
            # Skip common noise phrases
            if any(phrase in stripped.lower() for phrase in [
                'para procesar tu compra', 'nombre completo', 'correo electrónico',
                'nombre del banco', 'pago pse', 'enlace de pago'
            ]):
                continue
            if stripped:
                clean_lines.append(stripped)

        clean_text = ' '.join(clean_lines)
        if not clean_text:
            clean_text = text  # Fallback to original if filtering removed everything

        # Try explicit CC/CE label first (e.g., "C.C. 1090421192", "CC 12345678", "C.C. 94.062.630")
        # Supports digits with dots, dashes, or spaces as separators
        cc_labeled = re.search(
            r'(?:c\.?\s*c\.?|cedula|cédula)\s*[:\.\-]?\s*'
            r'(\d[\d\.\- ]{4,14}\d)',
            clean_text, re.IGNORECASE
        )
        if cc_labeled:
            info.cc = re.sub(r'[\.\- ]', '', cc_labeled.group(1))
        else:
            # Fallback 1: formatted number with dots/dashes (e.g., "94.062.630")
            cc_formatted = re.search(r'\b(\d{1,3}[\.\-]\d{3}[\.\-]\d{3})\b', clean_text)
            if cc_formatted:
                info.cc = re.sub(r'[\.\-]', '', cc_formatted.group(1))
            else:
                # Fallback 2: first standalone 6-10 digit number
                cc_match = re.search(r'\b(\d{6,10})\b', clean_text)
                if cc_match:
                    info.cc = cc_match.group(1)

        email_match = re.search(r'[\w\.\-]+@[\w\.\-]+\.\w+', clean_text)
        if email_match:
            info.email = email_match.group(0).lower()

        text_lower = clean_text.lower()
        for alias, code in BANK_ALIASES.items():
            if alias in text_lower:
                info.bank_code = code
                info.bank_name = alias.title()
                break

        # Name extraction: strip known fields and use only first meaningful words
        name_text = clean_text
        if info.cc: name_text = name_text.replace(info.cc, "")
        if info.email: name_text = name_text.replace(info.email, "")
        name_text = re.sub(r'[\d@\.\-_]+', ' ', name_text)
        name_text = re.sub(r'\b(cc|ce|cedula|email|correo|banco|bank|nequi|bancolombia|davivienda|bbva|ahorros|ahorro|corriente|savings|checking|cuenta)\b', '', name_text, flags=re.IGNORECASE)
        # Only take first 4 meaningful words as name
        words = [w for w in name_text.split() if len(w) > 1]
        name_candidate = ' '.join(words[:4]).strip()
        if len(name_candidate) >= 3:
            info.name = name_candidate.title()

        # Account type (BUY flow): "ahorros"/"ahorro" → savings, "corriente" → checking
        acct_type_match = re.search(
            r'\b(ahorro[s]?|savings?|corriente|checking|cuenta\s*de\s*ahorro|cuenta\s*corriente)\b',
            text_lower
        )
        if acct_type_match:
            matched = acct_type_match.group(0)
            if 'ahorro' in matched or 'saving' in matched:
                info.account_type = "savings"
            else:
                info.account_type = "checking"

        # Account number (BUY flow): a long digit sequence that isn't the CC
        # Colombian account numbers are typically 9-16 digits
        if info.cc:
            # Remove the CC digits from the clean text to avoid matching it again
            acct_search_text = clean_text.replace(info.cc, " ")
        else:
            acct_search_text = clean_text
        # Remove email to avoid matching numeric parts
        if info.email:
            acct_search_text = acct_search_text.replace(info.email, " ")

        # Look for explicit account number label first
        acct_labeled = re.search(
            r'(?:cuenta|account|n[uú]mero\s*(?:de\s*)?cuenta|no?\.?\s*cuenta)\s*[:\.\-]?\s*(\d[\d\-\s]{6,18}\d)',
            acct_search_text, re.IGNORECASE
        )
        if acct_labeled:
            info.account_number = re.sub(r'[\-\s]', '', acct_labeled.group(1))
        else:
            # Fallback: find digit sequences 9-16 digits long (after CC removal)
            acct_candidates = re.findall(r'\b(\d{9,16})\b', acct_search_text)
            if acct_candidates:
                info.account_number = acct_candidates[0]

        # ── F7-FIX: Nequi/Daviplata phone ↔ CC disambiguation ──
        # Digital wallets use 10-digit phone numbers as account numbers.
        # Colombian mobiles start with 3. CCs are 6-10 digits but rarely start with 3.
        # Risk: regex grabs the phone as CC first, leaving real CC as account_number.
        #
        # Strategy: if bank is a digital wallet AND cc looks like a phone AND
        # cc was NOT explicitly labeled (C.C./cédula), swap cc → account_number
        # and search for the real CC in the remaining text.
        DIGITAL_WALLET_CODES = {"1507", "1551", "1801"}  # Nequi, Daviplata, Movii
        if (info.bank_code in DIGITAL_WALLET_CODES
                and info.cc
                and len(info.cc) == 10
                and info.cc.startswith("3")
                and not cc_labeled):  # Skip if CC was explicitly labeled
            # The "CC" is actually the phone/account number
            phone_number = info.cc
            info.cc = None

            # If we already found an account_number that's 6-10 digits, that's likely the real CC
            if info.account_number and 6 <= len(info.account_number) <= 10:
                info.cc = info.account_number
                info.account_number = phone_number
            else:
                # Search remaining text for the real CC (a different 6-10 digit number)
                remaining = clean_text.replace(phone_number, " ")
                if info.email:
                    remaining = remaining.replace(info.email, " ")
                real_cc = re.search(r'\b(\d{6,10})\b', remaining)
                if real_cc and real_cc.group(1) != phone_number:
                    info.cc = real_cc.group(1)
                info.account_number = phone_number

            logger.info(
                f"F7: Digital wallet detected — phone={phone_number[:4]}*** "
                f"reassigned as account_number, cc={'***' + info.cc[-4:] if info.cc else 'NOT_FOUND'}"
            )

        return info

    async def close(self):
        await self.client.aclose()
