"""
Centralized Configuration
=========================
Validates all required environment variables at startup.
Fails fast with clear error messages if anything is missing.

This module replaces scattered os.getenv() calls across the codebase
with a single validated config object.
"""

import os
import shutil
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""

    # --- REQUIRED ---
    API_SECRET_KEY: str = ""
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""

    # --- REQUIRED for EUR path ---
    JANUAR_API_KEY: str = ""
    JANUAR_API_SECRET: str = ""

    # --- REQUIRED for COP path ---
    BINANCE_2FA_SECRET: str = ""
    FACILITAPAY_USERNAME: str = ""
    FACILITAPAY_PASSWORD: str = ""
    FACILITAPAY_CASH_IN_ACCOUNT_ID: str = ""
    FACILITAPAY_WEBHOOK_SECRET: str = ""
    GEMINI_API_KEY: str = ""

    # --- OPTIONAL for BRL path ---
    BINANCE_BRL_API_KEY: str = ""
    BINANCE_BRL_API_SECRET: str = ""
    BINANCE_BRL_2FA_SECRET: str = ""

    # --- OPTIONAL for MXN path ---
    BINANCE_MXN_API_KEY: str = ""
    BINANCE_MXN_API_SECRET: str = ""
    BINANCE_MXN_2FA_SECRET: str = ""
    FACILITAPAY_MXN_CASH_IN_ACCOUNT_ID: str = ""
    FACILITAPAY_MXN_CASHOUT_ACCOUNT_ID: str = ""

    # --- OPTIONAL ---
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    POLL_INTERVAL: float = 5.0
    COP_POLL_INTERVAL: float = 30.0
    MXN_POLL_INTERVAL: float = 30.0
    DB_PATH: str = "data/orders.db"
    COP_DB_PATH: str = "data/cop_orders.db"
    FP_DB_PATH: str = "data/facilitapay.db"
    BRL_DB_PATH: str = "data/brl_orders.db"
    LOG_LEVEL: str = "INFO"
    AUTO_SEND_COP_LINK: bool = False

    # --- COMPUTED ---
    data_dir: Path = field(default_factory=lambda: Path("data"))

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load config from environment variables."""
        config = cls(
            API_SECRET_KEY=os.getenv("API_SECRET_KEY", ""),
            BINANCE_API_KEY=os.getenv("BINANCE_API_KEY", ""),
            BINANCE_API_SECRET=os.getenv("BINANCE_API_SECRET", ""),
            JANUAR_API_KEY=os.getenv("JANUAR_API_KEY", ""),
            JANUAR_API_SECRET=os.getenv("JANUAR_API_SECRET", ""),
            BINANCE_2FA_SECRET=os.getenv("BINANCE_2FA_SECRET", ""),
            FACILITAPAY_USERNAME=os.getenv("FACILITAPAY_USERNAME", ""),
            FACILITAPAY_PASSWORD=os.getenv("FACILITAPAY_PASSWORD", ""),
            FACILITAPAY_CASH_IN_ACCOUNT_ID=os.getenv("FACILITAPAY_CASH_IN_ACCOUNT_ID", ""),
            FACILITAPAY_WEBHOOK_SECRET=os.getenv("FACILITAPAY_WEBHOOK_SECRET", ""),
            GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
            BINANCE_BRL_API_KEY=os.getenv("BINANCE_BRL_API_KEY", ""),
            BINANCE_BRL_API_SECRET=os.getenv("BINANCE_BRL_API_SECRET", ""),
            BINANCE_BRL_2FA_SECRET=os.getenv("BINANCE_BRL_2FA_SECRET", ""),
            BINANCE_MXN_API_KEY=os.getenv("BINANCE_MXN_API_KEY", ""),
            BINANCE_MXN_API_SECRET=os.getenv("BINANCE_MXN_API_SECRET", ""),
            BINANCE_MXN_2FA_SECRET=os.getenv("BINANCE_MXN_2FA_SECRET", ""),
            FACILITAPAY_MXN_CASH_IN_ACCOUNT_ID=os.getenv("FACILITAPAY_MXN_CASH_IN_ACCOUNT_ID", ""),
            FACILITAPAY_MXN_CASHOUT_ACCOUNT_ID=os.getenv("FACILITAPAY_MXN_CASHOUT_ACCOUNT_ID", ""),
            CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"),
            POLL_INTERVAL=float(os.getenv("POLL_INTERVAL", "5.0")),
            COP_POLL_INTERVAL=float(os.getenv("COP_POLL_INTERVAL", "30.0")),
            DB_PATH=os.getenv("DB_PATH", "data/orders.db"),
            COP_DB_PATH=os.getenv("COP_DB_PATH", "data/cop_orders.db"),
            FP_DB_PATH=os.getenv("FP_DB_PATH", "data/facilitapay.db"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            AUTO_SEND_COP_LINK=os.getenv("AUTO_SEND_COP_LINK", "false").lower() == "true",
        )
        return config

    def validate(self, eur_path: bool = True, cop_path: bool = True) -> list[str]:
        """
        Validate configuration. Returns list of errors.
        Empty list = all good.

        S5: Fails fast if critical config is missing — prevents silent runtime failures.
        """
        errors = []

        # Core (always required)
        if not self.API_SECRET_KEY:
            errors.append("API_SECRET_KEY is not set. Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        if not self.BINANCE_API_KEY:
            errors.append("BINANCE_API_KEY is not set")
        if not self.BINANCE_API_SECRET:
            errors.append("BINANCE_API_SECRET is not set")

        # EUR path
        if eur_path:
            if not self.JANUAR_API_KEY:
                errors.append("JANUAR_API_KEY is not set (required for EUR path)")
            if not self.JANUAR_API_SECRET:
                errors.append("JANUAR_API_SECRET is not set (required for EUR path)")

        # COP path
        if cop_path:
            if not self.BINANCE_2FA_SECRET:
                errors.append("BINANCE_2FA_SECRET is not set (required for COP path)")
            if not self.FACILITAPAY_USERNAME:
                errors.append("FACILITAPAY_USERNAME is not set (required for COP path)")
            if not self.FACILITAPAY_PASSWORD:
                errors.append("FACILITAPAY_PASSWORD is not set (required for COP path)")
            if not self.FACILITAPAY_CASH_IN_ACCOUNT_ID:
                errors.append("FACILITAPAY_CASH_IN_ACCOUNT_ID is not set (required for COP path)")

        return errors

    def check_disk_space(self, min_mb: int = 100) -> bool:
        """
        S5: Check that data directory has sufficient disk space.
        Returns True if OK, False if low.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        total, used, free = shutil.disk_usage(str(self.data_dir))
        free_mb = free // (1024 * 1024)
        if free_mb < min_mb:
            logger.critical(f"🚨 LOW DISK SPACE: {free_mb}MB free (minimum {min_mb}MB required)")
            return False
        logger.info(f"Disk space OK: {free_mb}MB free")
        return True

    def setup_logging(self):
        """Configure structured logging."""
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL.upper(), logging.INFO),
            format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Suppress noisy third-party loggers
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("websockets").setLevel(logging.WARNING)
