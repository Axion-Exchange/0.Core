"""
MXN Info Extractor
==================
Extract CURP, CLABE, RFC, and name from Binance chat messages.

Much simpler than COP — CURP and CLABE have unambiguous formats:
- CURP: 18 alphanumeric characters with specific structure
- CLABE: 18 digits with mod-10 weighted check digit
- RFC: 13 alphanumeric characters (optional)

No Gemini AI needed — regex handles these formats perfectly.
"""

import re
import logging
from .mxn_types import MXNCustomerInfo

logger = logging.getLogger("mxn_extractor")


# CURP pattern: 4 letters + 6 digits + H/M + 5 letters + 1 alphanum + 1 digit
# Example: SOMH031031HSRTRR04
CURP_PATTERN = re.compile(
    r'\b([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d)\b',
    re.IGNORECASE
)

# CLABE pattern: exactly 18 digits
CLABE_PATTERN = re.compile(r'\b(\d{18})\b')

# RFC pattern: 4 letters + 6 digits + 3 alphanum (persona física)
RFC_PATTERN = re.compile(
    r'\b([A-Z]{4}\d{6}[A-Z0-9]{3})\b',
    re.IGNORECASE
)

# Email pattern
EMAIL_PATTERN = re.compile(
    r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
)

# CLABE check digit weights (mod 10 weighted)
CLABE_WEIGHTS = [3, 7, 1] * 6


def validate_curp(curp: str) -> tuple[bool, str]:
    """
    Validate Mexican CURP format.

    CURP structure (18 chars):
    - Pos 1-4: First letters of surnames + first name initial
    - Pos 5-10: Birth date (YYMMDD)
    - Pos 11: Gender (H=Male, M=Female)
    - Pos 12-13: State code (2 letters)
    - Pos 14-16: First consonants of surnames + first name
    - Pos 17: Disambiguation character (0-9, A-Z)
    - Pos 18: Check digit (0-9)

    Returns (is_valid, normalized_curp_or_error).
    """
    if not curp:
        return False, "CURP vacío"

    curp = curp.strip().upper()

    if len(curp) != 18:
        return False, f"CURP debe tener 18 caracteres, tiene {len(curp)}"

    if not CURP_PATTERN.match(curp):
        return False, "Formato de CURP inválido"

    # Validate birth date portion (pos 5-10: YYMMDD)
    try:
        yy = int(curp[4:6])
        mm = int(curp[6:8])
        dd = int(curp[8:10])
        if not (1 <= mm <= 12 and 1 <= dd <= 31):
            return False, "Fecha de nacimiento inválida en CURP"
    except ValueError:
        return False, "Dígitos de fecha inválidos en CURP"

    # Validate gender (pos 11: H or M)
    if curp[10] not in ('H', 'M'):
        return False, "Género inválido en CURP (debe ser H o M)"

    # Valid Mexican state codes (pos 12-13)
    VALID_STATES = {
        'AS', 'BC', 'BS', 'CC', 'CL', 'CM', 'CS', 'CH', 'DF', 'DG',
        'GT', 'GR', 'HG', 'JC', 'MC', 'MN', 'MS', 'NT', 'NL', 'OC',
        'PL', 'QT', 'QR', 'SP', 'SL', 'SR', 'TC', 'TS', 'TL', 'VZ',
        'YN', 'ZS', 'NE',  # NE = Born abroad
    }
    state = curp[11:13]
    if state not in VALID_STATES:
        return False, f"Código de estado inválido: {state}"

    return True, curp


def validate_clabe(clabe: str) -> tuple[bool, str]:
    """
    Validate Mexican CLABE (18-digit interbank account number).

    CLABE structure:
    - Pos 1-3: Bank code
    - Pos 4-6: Branch code (plaza)
    - Pos 7-17: Account number
    - Pos 18: Check digit (mod 10 weighted)

    Returns (is_valid, normalized_clabe_or_error).
    """
    if not clabe:
        return False, "CLABE vacía"

    clabe = clabe.strip().replace(' ', '').replace('-', '')

    if len(clabe) != 18:
        return False, f"CLABE debe tener 18 dígitos, tiene {len(clabe)}"

    if not clabe.isdigit():
        return False, "CLABE debe contener solo dígitos"

    # Validate check digit (mod 10 weighted sum)
    total = 0
    for i in range(17):
        total += (int(clabe[i]) * CLABE_WEIGHTS[i]) % 10
    expected_check = (10 - (total % 10)) % 10
    actual_check = int(clabe[17])

    if expected_check != actual_check:
        return False, f"Dígito verificador inválido (esperado {expected_check}, tiene {actual_check})"

    return True, clabe


def extract_info(messages: list[str], previous: MXNCustomerInfo | None = None) -> MXNCustomerInfo:
    """
    Extract CURP, CLABE, RFC, and name from chat messages.

    Args:
        messages: List of chat message strings
        previous: Previously extracted info to merge with

    Returns:
        MXNCustomerInfo with extracted fields
    """
    info = MXNCustomerInfo(
        name=previous.name if previous else None,
        curp=previous.curp if previous else None,
        rfc=previous.rfc if previous else None,
        clabe=previous.clabe if previous else None,
        email=previous.email if previous else None,
    )

    # Join all messages for full-text search
    all_text = '\n'.join(messages)

    # Pre-filter: remove system/bot messages
    clean_lines = []
    for line in all_text.split('\n'):
        stripped = line.strip()
        # Skip JSON system messages
        if stripped.startswith('{') and 'type' in stripped.lower():
            continue
        # Skip bot's own templates
        if any(stripped.startswith(p) for p in ['¡Hola!', '[OK]', '[!]', '[...]',
                                                 'Realiza una', 'Enviamos al',
                                                 'Solo me falta', 'Monto exacto']):
            continue
        if stripped:
            clean_lines.append(stripped)

    clean_text = ' '.join(clean_lines)
    if not clean_text:
        clean_text = all_text

    # 1. Extract CURP (18 alphanum with specific structure)
    if not info.curp:
        curp_match = CURP_PATTERN.search(clean_text)
        if curp_match:
            candidate = curp_match.group(1).upper()
            valid, result = validate_curp(candidate)
            if valid:
                info.curp = result
                logger.info(f"Extracted CURP: {result[:4]}***{result[-2:]}" )
            else:
                logger.warning(f"CURP candidate rejected: {result}")

    # 2. Extract CLABE (18 digits — for BUY flow)
    if not info.clabe:
        # Remove any CURP from text to avoid matching it as CLABE
        search_text = clean_text
        if info.curp:
            search_text = search_text.replace(info.curp, ' ')

        clabe_match = CLABE_PATTERN.search(search_text)
        if clabe_match:
            candidate = clabe_match.group(1)
            valid, result = validate_clabe(candidate)
            if valid:
                info.clabe = result
                logger.info(f"Extracted CLABE: ***{result[-4:]}")
            else:
                logger.warning(f"CLABE candidate rejected: {result}")

    # 3. Extract email
    if not info.email:
        email_match = EMAIL_PATTERN.search(clean_text)
        if email_match:
            candidate = email_match.group(1).lower()
            # Filter out our own default/bot emails
            if candidate not in ('noreply@axion.exchange',):
                info.email = candidate
                logger.info(f"Extracted email: {candidate[:3]}***@{candidate.split('@')[1]}")

    # 4a. Extract RFC (optional, 13 chars)
    if not info.rfc:
        rfc_match = RFC_PATTERN.search(clean_text)
        if rfc_match:
            candidate = rfc_match.group(1).upper()
            # RFC's first 10 chars should match CURP's first 10 (if CURP known)
            if info.curp and candidate[:10] != info.curp[:10]:
                logger.debug(f"RFC candidate doesn't match CURP — skipping")
            elif len(candidate) == 13:
                info.rfc = candidate
                logger.info(f"Extracted RFC: {candidate[:4]}***")

    # 5. Extract name (remaining text after stripping known fields)
    if not info.name:
        name_text = clean_text
        if info.curp: name_text = name_text.replace(info.curp, '')
        if info.clabe: name_text = name_text.replace(info.clabe, '')
        if info.rfc: name_text = name_text.replace(info.rfc, '')
        if info.email: name_text = name_text.replace(info.email, '')
        # Remove digits, special chars
        name_text = re.sub(r'[\d@\.\-_]+', ' ', name_text)
        # Remove known keywords
        name_text = re.sub(
            r'\b(curp|rfc|clabe|banco|bank|nombre|name|spei|transferencia|cuenta|interbancaria)\b',
            '', name_text, flags=re.IGNORECASE
        )
        # Take first 4 meaningful words
        words = [w for w in name_text.split() if len(w) > 1 and w.isalpha()]
        name_candidate = ' '.join(words[:4]).strip()
        if len(name_candidate) >= 3:
            info.name = name_candidate.title()
            logger.info(f"Extracted name: {info.name}")

    return info
