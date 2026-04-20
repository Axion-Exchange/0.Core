"""
Sanitize counterparty names for SEPA/Januar payouts.

SEPA only accepts Latin characters (A-Z, a-z, 0-9, and a few punctuation marks).
This module transliterates Cyrillic and other non-Latin scripts to their closest
Latin equivalents, then strips any remaining unsupported characters.

Zero external dependencies — uses a built-in transliteration map.
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# Cyrillic → Latin transliteration map (Ukrainian + Russian)
# Based on ISO 9:1995 / Ukrainian passport transliteration standard
# ---------------------------------------------------------------------------
_CYRILLIC_TO_LATIN: dict[str, str] = {
    # Ukrainian
    "А": "A", "Б": "B", "В": "V", "Г": "H", "Ґ": "G",
    "Д": "D", "Е": "E", "Є": "Ye", "Ж": "Zh", "З": "Z",
    "И": "Y", "І": "I", "Ї": "Yi", "Й": "Y", "К": "K",
    "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P",
    "Р": "R", "С": "S", "Т": "T", "У": "U", "Ф": "F",
    "Х": "Kh", "Ц": "Ts", "Ч": "Ch", "Ш": "Sh", "Щ": "Shch",
    "Ь": "", "Ю": "Yu", "Я": "Ya",
    # Russian additions
    "Ё": "Yo", "Ы": "Y", "Э": "E", "Ъ": "",
    # Lowercase
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g",
    "д": "d", "е": "e", "є": "ye", "ж": "zh", "з": "z",
    "и": "y", "і": "i", "ї": "yi", "й": "y", "к": "k",
    "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
    "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ь": "", "ю": "yu", "я": "ya",
    "ё": "yo", "ы": "y", "э": "e", "ъ": "",
}

# SEPA allowed characters: Latin letters, digits, spaces, and basic punctuation
# Per EPC (European Payments Council) character set
_SEPA_ALLOWED = re.compile(r"[^A-Za-z0-9 /\-?:().,'+]")


def _transliterate_cyrillic(text: str) -> str:
    """Transliterate Cyrillic characters to Latin equivalents.

    Preserves case: uppercase input chars produce fully uppercase output
    (e.g. Ю → YU when uppercase, ю → yu when lowercase).
    """
    result: list[str] = []
    for char in text:
        if char in _CYRILLIC_TO_LATIN:
            mapped = _CYRILLIC_TO_LATIN[char]
            # If original char is uppercase, ensure entire mapping is uppercase
            if char.isupper() and len(mapped) > 1:
                mapped = mapped.upper()
            result.append(mapped)
        else:
            result.append(char)
    return "".join(result)


def _strip_accents(text: str) -> str:
    """Remove diacritical marks from Latin characters (e.g. é → e, ö → o)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def sanitize_sepa_name(name: str) -> str:
    """Sanitize a counterparty name for SEPA/Januar compliance.

    Steps:
        1. Transliterate Cyrillic → Latin
        2. Remove diacritical marks (é → e, ö → o)
        3. Strip any remaining non-SEPA characters
        4. Normalize whitespace

    Returns the sanitized name, or the original name if it was already valid.
    The returned name is guaranteed to contain only SEPA-allowed characters.
    """
    if not name:
        return name

    # Step 1: Cyrillic transliteration
    result = _transliterate_cyrillic(name)

    # Step 2: Remove accents from Latin chars
    result = _strip_accents(result)

    # Step 3: Strip any remaining non-SEPA characters
    result = _SEPA_ALLOWED.sub("", result)

    # Step 4: Normalize whitespace (collapse multiple spaces, strip edges)
    result = " ".join(result.split())

    return result


def has_non_latin(name: str) -> bool:
    """Check if name contains non-Latin characters that need transliteration."""
    if not name:
        return False
    stripped = _strip_accents(name)
    return bool(_SEPA_ALLOWED.search(stripped))


def extract_clean_latin_parts(name: str) -> str | None:
    """Extract only the clean Latin-character parts of a name.

    Unlike sanitize_sepa_name() which tries to transliterate everything,
    this function DROPS any word that still contains non-Latin characters
    after transliteration+accent-stripping. Useful when Januar rejects a
    partially-non-Latin name.

    Examples:
        "Joôann alex mikey"   → "Joann alex mikey"   (accent stripped)
        "محمد Alex Smith"      → "Alex Smith"          (Arabic dropped)
        "Алексей Петров"       → "Aleksey Petrov"      (Cyrillic transliterated)
        "Jean-Pierre Müller"  → "Jean-Pierre Muller"  (accent stripped)
        "🎉 Bob"              → None                   (only 1 word left)

    Returns the cleaned name if at least 2 valid words remain, else None.
    """
    if not name:
        return None

    # Step 1: Transliterate Cyrillic
    result = _transliterate_cyrillic(name)

    # Step 2: Strip accents
    result = _strip_accents(result)

    # Step 3: Split into words and keep only fully-clean ones
    words = result.split()
    clean_words = []
    for w in words:
        # Strip leading/trailing punctuation for the check
        stripped = w.strip(".,;:!?'\"()-/")
        if not stripped:
            continue
        # Keep only words where every char is Latin letter, hyphen, or apostrophe
        if all((c.isascii() and c.isalpha()) or c in "-'" for c in stripped) and len(stripped) >= 2:
            clean_words.append(w)  # preserve original punctuation like hyphens

    if len(clean_words) >= 2:
        return " ".join(clean_words)

    return None
