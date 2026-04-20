"""
ENVIRONMENT VALIDATOR
=====================
Startup validation for required environment variables.

Features:
- Validates required vars per feature flag
- Produces safe redacted startup summary
- Fails fast with clear error messages
"""

import logging
import os
import sys

logger = logging.getLogger("env_validator")


# ─── Variable Groups ─────────────────────────────────────────────────────────

CORE_REQUIRED = [
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "JANUAR_API_KEY",
    "JANUAR_API_SECRET",
    "API_SECRET_KEY",  # P1-5: fail-closed auth — abort if missing
]

COP_REQUIRED = [
    "FACILITAPAY_USERNAME",
    "FACILITAPAY_PASSWORD",
    "FACILITAPAY_CASH_IN_ACCOUNT_ID",
    "FACILITAPAY_CASHOUT_ACCOUNT_ID",  # P1-4: required for COP payouts
]

OPTIONAL_VARS = [
    "BINANCE_2FA_SECRET",
    "GEMINI_API_KEY",
    "DIDIT_APP_ID",
    "DIDIT_API_KEY",
    "FACILITAPAY_WEBHOOK_SECRET",
    "CORS_ORIGINS",
]


# ─── Validation ──────────────────────────────────────────────────────────────

def validate_env(*, enable_cop: bool = False) -> dict[str, bool]:
    """
    Validate environment variables. Exits if critical vars missing.

    Returns:
        Dict of feature flags and their status.
    """
    result = {
        "core": True,
        "cop": False,
    }

    # ── Core (always required) ──
    missing_core = [v for v in CORE_REQUIRED if not os.getenv(v)]
    if missing_core:
        logger.critical(
            "Missing REQUIRED environment variables: %s — cannot start",
            missing_core,
        )
        sys.exit(1)

    # ── COP (required if enabled) ──
    if enable_cop:
        missing_cop = [v for v in COP_REQUIRED if not os.getenv(v)]
        if missing_cop:
            logger.critical(
                "ENABLE_COP=true but missing FacilitaPay vars: %s — cannot start",
                missing_cop,
            )
            sys.exit(1)
        result["cop"] = True
        # Warn if webhook secret is not configured (bot will use polling fallback)
        if not os.getenv("FACILITAPAY_WEBHOOK_SECRET"):
            logger.warning(
                "FACILITAPAY_WEBHOOK_SECRET not set — using polling fallback for payment confirmation"
            )

    return result


def print_startup_summary(*, enable_cop: bool, features: dict) -> None:
    """Log a safe redacted summary of the startup configuration."""
    lines = [
        "",
        "═" * 60,
        "  P2P AUTOMATION BOT — STARTUP SUMMARY",
        "═" * 60,
        "",
        "  Features:",
    ]

    lines.append(f"    Core (EUR)  : ✅ enabled")
    lines.append(f"    COP Handler : {'✅ enabled' if enable_cop else '⬚  disabled'}")

    lines.append("")
    lines.append("  Environment:")

    for var in CORE_REQUIRED + (COP_REQUIRED if enable_cop else []):
        val = os.getenv(var, "")
        redacted = _redact(val)
        lines.append(f"    {var:40s} = {redacted}")

    for var in OPTIONAL_VARS:
        val = os.getenv(var, "")
        if val:
            lines.append(f"    {var:40s} = {_redact(val)}")
        else:
            lines.append(f"    {var:40s} = (not set)")

    lines.append("")
    lines.append("═" * 60)
    lines.append("")

    logger.info("\n".join(lines))


def _redact(value: str) -> str:
    """Show first 4 and last 4 chars, mask the rest."""
    if not value:
        return "(empty)"
    if len(value) <= 10:
        return value[:2] + "***"
    return value[:4] + "****" + value[-4:]
