"""
IBAN SCREENER SERVICE
=====================
Validates IBANs and screens for sanctioned countries.

Usage:
    from src.services.iban_screener import screen_iban, IbanScreenResult
    
    result = screen_iban("DE89370400440532013000")
    if result.is_blocked:
        print(f"Blocked: {result.reason}")
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    """Country risk classification."""
    ALLOWED = "allowed"
    COMPREHENSIVELY_SANCTIONED = "comprehensively_sanctioned"
    HIGH_RISK = "high_risk"
    OPERATIONAL_RISK = "operational_risk"
    SPECIFIC_EXCLUSION = "specific_exclusion"
    BANNED_BANK = "banned_bank"


# All valid IBAN country codes
# All valid IBAN country codes & key lengths
IBAN_LENGTHS = {
    "AL": 28, "AD": 24, "AT": 20, "AZ": 28, "BH": 22, "BY": 28, "BE": 16,
    "BA": 20, "BR": 29, "BG": 22, "BI": 16, "CR": 22, "HR": 21, "CY": 28,
    "CZ": 24, "DK": 18, "DJ": 27, "DO": 28, "EG": 29, "SV": 28, "EE": 20,
    "ES": 24, "FK": 18, "FO": 18, "FI": 18, "FR": 27, "GE": 22, "DE": 22, "GI": 23,
    "GR": 27, "GL": 18, "GT": 28, "VA": 22, "HN": 28, "HU": 28, "IS": 26,
    "IQ": 23, "IE": 22, "IL": 23, "IT": 27, "JO": 30, "KZ": 20, "XK": 20,
    "KW": 30, "LB": 28, "LY": 25, "LT": 20, "LU": 20, "LV": 21, "MC": 27,
    "MD": 24, "ME": 22, "MK": 19, "MN": 20, "MR": 27, "MT": 31, "MU": 30,
    "NI": 32, "NL": 18, "NO": 15, "OM": 23, "PK": 24, "PL": 28, "PS": 29,
    "PT": 25, "QA": 29, "RO": 24, "RS": 22, "RU": 33, "SA": 24, "SC": 31,
    "SD": 29, "SE": 24, "SI": 19, "SK": 24, "SM": 27, "SO": 23, "ST": 25,
    "CH": 21, "TL": 23, "TN": 24, "TR": 26, "UA": 29, "AE": 23, "GB": 22,
    "VG": 24, "YE": 30, "LC": 32, "LI": 21,
}

VALID_IBAN_COUNTRIES = set(IBAN_LENGTHS.keys())

# ── SEPA Zone Countries (whitelist) ──
# Januar only supports SEPA transfers. IBANs from non-SEPA countries will fail.
# Source: European Payments Council (EPC) SEPA scheme participants
SEPA_COUNTRIES = {
    # EU Member States
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    # EEA (non-EU)
    "IS", "LI", "NO",
    # Other SEPA participants
    "GB", "CH", "MC", "SM", "AD", "VA", "GI",
    # French overseas (use FR IBAN prefix mostly, but just in case)
    "PM",
}

# Comprehensively Sanctioned - BLOCKED (international sanctions)
SANCTIONED_COUNTRIES = {"BY", "RU", "SD", "SY"}

# High-Risk / Grey List - BLOCKED
# Cleared: All SEPA countries unblocked per operator policy
HIGH_RISK_COUNTRIES: set[str] = set()

# Operational Risk - BLOCKED (only Ukraine per operator policy)
OPERATIONAL_RISK_COUNTRIES = {"UA"}

# Specific Exclusions - BLOCKED
# Cleared per operator policy
SPECIFIC_EXCLUSIONS: set[str] = set()


def _all_blocked() -> set[str]:
    """Compute combined blocked set (always fresh)."""
    return SANCTIONED_COUNTRIES | HIGH_RISK_COUNTRIES | OPERATIONAL_RISK_COUNTRIES | SPECIFIC_EXCLUSIONS

# Banned banks (name patterns to match, case-insensitive)
BANNED_BANKS = {
    "myfin",
    "myfin bank",
    "my fin",
}


@dataclass
class IbanScreenResult:
    """Result of IBAN screening."""
    iban: str
    country_code: str
    country_name: str | None
    is_valid_iban: bool
    is_blocked: bool
    risk_level: RiskLevel
    reason: str | None
    bank_name: str | None = None  # Optional bank name if provided
    
    def to_dict(self) -> dict:
        return {
            "iban": self.iban,
            "country_code": self.country_code,
            "country_name": self.country_name,
            "is_valid_iban": self.is_valid_iban,
            "is_blocked": self.is_blocked,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "bank_name": self.bank_name,
        }


# Country code to name mapping
COUNTRY_NAMES = {
    "AL": "Albania", "AD": "Andorra", "AT": "Austria", "AZ": "Azerbaijan",
    "BH": "Bahrain", "BY": "Belarus", "BE": "Belgium", "BA": "Bosnia and Herzegovina",
    "BR": "Brazil", "BG": "Bulgaria", "BI": "Burundi", "CR": "Costa Rica",
    "HR": "Croatia", "CY": "Cyprus", "CZ": "Czechia", "DK": "Denmark",
    "DJ": "Djibouti", "DO": "Dominican Republic", "EG": "Egypt", "SV": "El Salvador",
    "EE": "Estonia", "ES": "Spain", "FK": "Falkland Islands", "FO": "Faroe Islands", "FI": "Finland",
    "FR": "France", "GE": "Georgia", "DE": "Germany", "GI": "Gibraltar",
    "GR": "Greece", "GL": "Greenland", "GT": "Guatemala", "VA": "Holy See",
    "HN": "Honduras", "HU": "Hungary", "IS": "Iceland", "IQ": "Iraq",
    "IE": "Ireland", "IL": "Israel", "IT": "Italy", "JO": "Jordan",
    "KZ": "Kazakhstan", "XK": "Kosovo", "KW": "Kuwait", "LB": "Lebanon",
    "LY": "Libya", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia",
    "MC": "Monaco", "MD": "Moldova", "ME": "Montenegro", "MK": "North Macedonia",
    "MN": "Mongolia", "MR": "Mauritania", "MT": "Malta", "MU": "Mauritius",
    "NI": "Nicaragua", "NL": "Netherlands", "NO": "Norway", "OM": "Oman",
    "PK": "Pakistan", "PL": "Poland", "PS": "Palestine", "PT": "Portugal",
    "QA": "Qatar", "RO": "Romania", "RS": "Serbia", "RU": "Russia",
    "SA": "Saudi Arabia", "SC": "Seychelles", "SD": "Sudan", "SE": "Sweden",
    "SI": "Slovenia", "SK": "Slovakia", "SM": "San Marino", "SO": "Somalia",
    "ST": "Sao Tome and Principe", "CH": "Switzerland", "TL": "Timor-Leste",
    "TN": "Tunisia", "TR": "Turkiye", "UA": "Ukraine", "AE": "United Arab Emirates",
    "GB": "United Kingdom", "VG": "British Virgin Islands", "YE": "Yemen",
    "LC": "Saint Lucia", "LI": "Liechtenstein",
    # Non-IBAN but may appear
    "HT": "Haiti", "VN": "Vietnam", "AO": "Angola", "BO": "Bolivia",
    "DZ": "Algeria", "KE": "Kenya", "NA": "Namibia", "NP": "Nepal", "SY": "Syria",
}


def screen_iban(iban: str) -> IbanScreenResult:
    """
    Screen an IBAN for validity and sanctions.
    
    Args:
        iban: The IBAN to screen (spaces allowed, will be normalized)
        
    Returns:
        IbanScreenResult with screening details
    """
    # Normalize: remove spaces and uppercase
    iban = iban.replace(" ", "").upper()
    
    # Extract country code (first 2 characters)
    if len(iban) < 2:
        return IbanScreenResult(
            iban=iban,
            country_code="",
            country_name=None,
            is_valid_iban=False,
            is_blocked=True,
            risk_level=RiskLevel.ALLOWED,
            reason="Invalid IBAN: too short",
        )
    
    country_code = iban[:2]
    country_name = COUNTRY_NAMES.get(country_code)
    
    # Check IBAN checksum and length
    checksum_valid, checksum_err = validate_iban_structure(iban)
    if not checksum_valid:
        return IbanScreenResult(
            iban=iban,
            country_code=country_code,
            country_name=country_name,
            is_valid_iban=False,
            is_blocked=True,
            risk_level=RiskLevel.ALLOWED,
            reason=checksum_err,
        )
    
    # Check sanctions
    # ── SEPA whitelist check (must come first) ──
    if country_code not in SEPA_COUNTRIES:
        return IbanScreenResult(
            iban=iban,
            country_code=country_code,
            country_name=country_code,
            is_valid_iban=True,
            is_blocked=True,
            reason=f"Non-SEPA country: {country_code} - only SEPA transfers supported",
            risk_level=RiskLevel.OPERATIONAL_RISK,
        )

    if country_code in SANCTIONED_COUNTRIES:
        return IbanScreenResult(
            iban=iban,
            country_code=country_code,
            country_name=country_name,
            is_valid_iban=True,
            is_blocked=True,
            risk_level=RiskLevel.COMPREHENSIVELY_SANCTIONED,
            reason=f"Comprehensively sanctioned country: {country_name or country_code}",
        )
    
    if country_code in HIGH_RISK_COUNTRIES:
        return IbanScreenResult(
            iban=iban,
            country_code=country_code,
            country_name=country_name,
            is_valid_iban=True,
            is_blocked=True,
            risk_level=RiskLevel.HIGH_RISK,
            reason=f"High-risk country: {country_name or country_code}",
        )
    
    if country_code in OPERATIONAL_RISK_COUNTRIES:
        return IbanScreenResult(
            iban=iban,
            country_code=country_code,
            country_name=country_name,
            is_valid_iban=True,
            is_blocked=True,
            risk_level=RiskLevel.OPERATIONAL_RISK,
            reason=f"Operational risk country: {country_name or country_code}",
        )
    
    if country_code in SPECIFIC_EXCLUSIONS:
        return IbanScreenResult(
            iban=iban,
            country_code=country_code,
            country_name=country_name,
            is_valid_iban=True,
            is_blocked=True,
            risk_level=RiskLevel.SPECIFIC_EXCLUSION,
            reason=f"Specifically excluded country: {country_name or country_code}",
        )
    
    # Allowed
    return IbanScreenResult(
        iban=iban,
        country_code=country_code,
        country_name=country_name,
        is_valid_iban=True,
        is_blocked=False,
        risk_level=RiskLevel.ALLOWED,
        reason=None,
    )


def is_iban_blocked(iban: str) -> bool:
    """Quick check if IBAN is blocked."""
    return screen_iban(iban).is_blocked


def get_blocked_reason(iban: str) -> str | None:
    """Get the reason an IBAN is blocked, or None if allowed."""
    result = screen_iban(iban)
    return result.reason if result.is_blocked else None


def is_bank_banned(bank_name: str) -> bool:
    """Check if a bank name is banned."""
    if not bank_name:
        return False
    normalized = bank_name.lower().strip()
    return any(banned in normalized or normalized in banned for banned in BANNED_BANKS)


def screen_iban_with_bank(iban: str, bank_name: str | None = None) -> IbanScreenResult:
    """
    Screen an IBAN with optional bank name check.
    
    Args:
        iban: The IBAN to screen
        bank_name: Optional bank name to check against banned list
        
    Returns:
        IbanScreenResult with screening details
    """
    result = screen_iban(iban)
    result.bank_name = bank_name
    
    # If already blocked by country, return as-is
    if result.is_blocked:
        return result
    
    # Check bank name if provided
    if bank_name and is_bank_banned(bank_name):
        result.is_blocked = True
        result.risk_level = RiskLevel.BANNED_BANK
        result.reason = f"Banned bank: {bank_name}"
    
    return result


# =========================================================================
# RUNTIME BLOCKLIST MANAGEMENT (for dashboard API)
# =========================================================================

def get_blocklists() -> dict:
    """Return current blocklists for the dashboard."""
    return {
        "sanctioned": sorted(SANCTIONED_COUNTRIES),
        "high_risk": sorted(HIGH_RISK_COUNTRIES),
        "operational_risk": sorted(OPERATIONAL_RISK_COUNTRIES),
        "specific_exclusions": sorted(SPECIFIC_EXCLUSIONS),
        "banned_banks": sorted(BANNED_BANKS),
    }


def update_blocklists(
    sanctioned: list[str] | None = None,
    high_risk: list[str] | None = None,
    operational_risk: list[str] | None = None,
    specific_exclusions: list[str] | None = None,
    banned_banks: list[str] | None = None,
) -> dict:
    """Update blocklists at runtime. Only provided lists are replaced."""
    global SANCTIONED_COUNTRIES, HIGH_RISK_COUNTRIES, OPERATIONAL_RISK_COUNTRIES
    global SPECIFIC_EXCLUSIONS, BANNED_BANKS
    if sanctioned is not None:
        SANCTIONED_COUNTRIES = {c.upper().strip() for c in sanctioned if c.strip()}
    if high_risk is not None:
        HIGH_RISK_COUNTRIES = {c.upper().strip() for c in high_risk if c.strip()}
    if operational_risk is not None:
        OPERATIONAL_RISK_COUNTRIES = {c.upper().strip() for c in operational_risk if c.strip()}
    if specific_exclusions is not None:
        SPECIFIC_EXCLUSIONS = {c.upper().strip() for c in specific_exclusions if c.strip()}
    if banned_banks is not None:
        BANNED_BANKS = {b.lower().strip() for b in banned_banks if b.strip()}
    return get_blocklists()


def validate_iban_structure(iban: str) -> tuple[bool, str | None]:
    """
    Validate IBAN structure (Length + ISO 7064 Mod 97-10 checksum).
    
    Returns:
        (is_valid, error_reason)
    """
    cleaned = iban.replace(" ", "").upper()
    
    if len(cleaned) < 5:
        return False, "Too short"
        
    country_code = cleaned[:2]
    if country_code not in IBAN_LENGTHS:
        return False, f"Unknown country code: {country_code}"
        
    expected_len = IBAN_LENGTHS[country_code]
    if len(cleaned) != expected_len:
        return False, f"Invalid length for {country_code} (Expected {expected_len})"
        
    # Checksum (Move first 4 chars to end)
    rearranged = cleaned[4:] + cleaned[:4]
    
    # Convert letters to numbers (A=10, B=11...)
    numeric_str = ""
    for char in rearranged:
        if char.isdigit():
            numeric_str += char
        else:
            numeric_str += str(ord(char) - 55)
            
    # Modulo 97 check
    try:
        if int(numeric_str) % 97 != 1:
            return False, "Invalid checksum"
    except ValueError:
        return False, "Invalid characters"
        
    return True, None
