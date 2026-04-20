"""
P2P Automation Bot — Main Entry Point
======================================

Supervised runtime with explicit task lifecycle management.

Tasks:
  CRITICAL (abort if broken):
    - api_server: FastAPI on configurable port
    - orchestrator: EUR order matching + release
    - cop_handler: COP chat + FacilitaPay PSE (if ENABLE_COP=true)

  OPTIONAL (log warning if missing):
    - liquidity_monitor: EUR → USDC rebalancing
    - ad_topup: P2P ad quantity monitoring
    - conversion_monitor: Active conversion tracking

Usage:
    python main.py [--dry-run] [--api-only]

Environment:
    BINANCE_API_KEY, BINANCE_API_SECRET  (required)
    JANUAR_API_KEY, JANUAR_API_SECRET    (required)
    ENABLE_COP=true                      (enables COP handler)
    FACILITAPAY_USERNAME, etc.           (required if COP enabled)
    GEMINI_API_KEY                       (for name matching)
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ─── Logging Setup ───────────────────────────────────────────────────────────

def setup_logging():
    """Configure structured logging. No print() anywhere."""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger("main")


# ─── Configuration ───────────────────────────────────────────────────────────

class Config:
    """Runtime configuration from environment."""

    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))

    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    API_ONLY = os.getenv("API_ONLY", "false").lower() == "true"
    ENABLE_COP = os.getenv("ENABLE_COP", "false").lower() == "true"
    ENABLE_BRL = os.getenv("ENABLE_BRL", "false").lower() == "true"
    ENABLE_MXN = os.getenv("ENABLE_MXN", "false").lower() == "true"

    EXCHANGE_POLL_INTERVAL = float(os.getenv("EXCHANGE_POLL_INTERVAL", "5"))
    BANK_POLL_INTERVAL = float(os.getenv("BANK_POLL_INTERVAL", "30"))
    COP_POLL_INTERVAL = float(os.getenv("COP_POLL_INTERVAL", "30"))
    MXN_POLL_INTERVAL = float(os.getenv("MXN_POLL_INTERVAL", "30"))


# ─── API Registration ────────────────────────────────────────────────────────

def register_apis():
    """Register exchange and bank API clients."""
    from src.core.registry import registry
    from src.exchanges.binance.api_client import BinanceApiClient
    from src.fiat.eur.januar_sepa_client import JanuarSepaClient

    binance_key = os.getenv("BINANCE_API_KEY")
    binance_secret = os.getenv("BINANCE_API_SECRET")
    if binance_key and binance_secret:
        binance = BinanceApiClient(api_key=binance_key, api_secret=binance_secret)
        registry.register_exchange_api(binance)
        logger.info("Registered exchange API: Binance")
    else:
        logger.critical("BINANCE_API_KEY/SECRET not set — cannot start")
        sys.exit(1)

    januar_key = os.getenv("JANUAR_API_KEY")
    januar_secret = os.getenv("JANUAR_API_SECRET")
    januar_url = os.getenv("JANUAR_BASE_URL", "https://api.januar.com")
    if januar_key and januar_secret:
        januar = JanuarSepaClient(
            api_key=januar_key,
            api_secret=januar_secret,
            base_url=januar_url
        )
        registry.register_bank(januar)
        logger.info("Registered bank: Januar")
    else:
        logger.critical("JANUAR_API_KEY/SECRET not set — cannot start")
        sys.exit(1)

    # BRL Account (separate Binance credentials)
    if Config.ENABLE_BRL:
        brl_key = os.getenv("BINANCE_BRL_API_KEY")
        brl_secret = os.getenv("BINANCE_BRL_API_SECRET")
        if brl_key and brl_secret:
            from src.core.types import ExchangeId
            binance_brl = BinanceApiClient(
                api_key=brl_key,
                api_secret=brl_secret,
                exchange_id_override=ExchangeId.BINANCE_BRL,
                totp_secret=os.getenv("BINANCE_BRL_2FA_SECRET"),
            )
            registry.register_exchange_api(binance_brl)
            logger.info("Registered exchange API: Binance BRL")
        else:
            logger.warning("ENABLE_BRL=true but BINANCE_BRL_API_KEY/SECRET not set — BRL disabled")

    # MXN Account (separate Binance credentials)
    if Config.ENABLE_MXN:
        mxn_key = os.getenv("BINANCE_MXN_API_KEY")
        mxn_secret = os.getenv("BINANCE_MXN_API_SECRET")
        if mxn_key and mxn_secret:
            from src.core.types import ExchangeId
            binance_mxn = BinanceApiClient(
                api_key=mxn_key,
                api_secret=mxn_secret,
                exchange_id_override=ExchangeId.BINANCE_MXN,
                totp_secret=os.getenv("BINANCE_MXN_2FA_SECRET"),
            )
            registry.register_exchange_api(binance_mxn)
            logger.info("Registered exchange API: Binance MXN")
        else:
            logger.warning("ENABLE_MXN=true but BINANCE_MXN_API_KEY/SECRET not set — MXN disabled")


# ─── Critical Task Coroutines ────────────────────────────────────────────────

async def _run_api_server():
    """Run the FastAPI server."""
    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from src.api.main import app
    from src.core.health import task_registry

    # Fix 5: Heartbeat middleware — every successful HTTP request proves the server is alive
    class HeartbeatMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            task_registry.heartbeat("api_server")
            return response

    app.add_middleware(HeartbeatMiddleware)

    logger.info("Starting API Server on %s:%d", Config.API_HOST, Config.API_PORT)

    config = uvicorn.Config(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


async def _run_orchestrator():
    """Run the EUR order orchestrator polling loop."""
    from src.services.order_orchestrator import orchestrator

    logger.info("Starting Order Orchestrator")
    await orchestrator.start()


async def _run_cop_handler():
    """Run the COP chat handler polling loop."""
    from src.fiat.cop.cop_handler import COPChatHandler
    from src.fiat.cop.facilitapay_webhooks import create_webhook_router
    from src.api.main import app

    handler = COPChatHandler(
        binance_api_key=os.getenv("BINANCE_API_KEY", ""),
        binance_api_secret=os.getenv("BINANCE_API_SECRET", ""),
        binance_2fa_secret=os.getenv("BINANCE_2FA_SECRET", ""),
        facilitapay_username=os.getenv("FACILITAPAY_USERNAME", ""),
        facilitapay_password=os.getenv("FACILITAPAY_PASSWORD", ""),
        facilitapay_cash_in_account_id=os.getenv("FACILITAPAY_CASH_IN_ACCOUNT_ID", ""),
        facilitapay_cashout_account_id=os.getenv("FACILITAPAY_CASHOUT_ACCOUNT_ID", ""),
        facilitapay_webhook_secret=os.getenv("FACILITAPAY_WEBHOOK_SECRET", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        poll_interval=Config.COP_POLL_INTERVAL,
    )

    # P0-1: Mount FacilitaPay webhook router on the FastAPI app.
    # The webhook handler has its own secret verification (fail-closed).
    # No external auth middleware needed — FP sends webhook_secret in payload.
    if handler.facilitapay:
        webhook_router = create_webhook_router(handler.facilitapay)
        app.include_router(webhook_router)
        logger.info("Mounted FacilitaPay webhook router at /webhooks/facilitapay")
    else:
        logger.warning("FacilitaPay client unavailable — webhook router NOT mounted")

    logger.info("Starting COP Chat Handler (poll every %.0fs)", Config.COP_POLL_INTERVAL)
    await handler.start()



# ─── Optional Task Coroutines ────────────────────────────────────────────────

async def _run_liquidity_monitor():
    """Monitor liquidity and trigger EUR → USDC rebalancing."""
    from src.services.liquidity_manager import LiquidityManager

    from src.core.health import task_registry

    logger.info("Starting Liquidity Monitor")
    manager = LiquidityManager()
    while True:
        try:
            status = manager.get_status()
            snapshot = status.get("last_snapshot")
            if snapshot:
                fiat_ratio = snapshot.get("fiat_ratio", 0)
                threshold = float(os.getenv("FIAT_RATIO_THRESHOLD", "0.8"))
                if fiat_ratio > threshold:
                    logger.warning("Fiat ratio %.1f%% > %.0f%% threshold", fiat_ratio * 100, threshold * 100)
                    if not Config.DRY_RUN:
                        result = await manager.rebalance()
                        logger.info("Rebalance initiated: %s", result)
            task_registry.heartbeat("liquidity_monitor")
        except Exception as e:
            logger.error("Liquidity check error: %s", e)
        await asyncio.sleep(float(os.getenv("LIQUIDITY_CHECK_INTERVAL", "300")))


async def _run_ad_topup():
    """Rebalance BUY EUR ads based on Januar balance + SELL ad auto-topup."""
    from src.services.ad_rebalancer import AdRebalancer
    from src.core.persistence import order_db
    from src.core.registry import registry

    logger.info("Starting Ad Rebalancer (replaces legacy ad_topup)")
    rebalancer = AdRebalancer(registry=registry, persistence_db=order_db)

    # Share the rebalancer instance with the orchestrator
    # so it can trigger SELL ad topup on BUY order completion
    from src.services.order_orchestrator import orchestrator
    orchestrator._ad_rebalancer = rebalancer

    await rebalancer.run_loop()


async def _run_pricing_engine():
    """Dynamic pricing: set ad prices based on WAC cost basis."""
    from src.services.pricing_engine import PricingEngine
    from src.core.registry import registry

    db_path = os.getenv("DB_PATH", "data/orders.db")
    logger.info("Starting Pricing Engine (db=%s)", db_path)
    engine = PricingEngine(registry=registry, db_path=db_path)
    await engine.run_loop()


async def _run_conversion_monitor():
    """Monitor active conversions and auto-send USDC when complete."""
    from src.services.conversion_manager import ConversionManager

    from src.core.health import task_registry

    logger.info("Starting Conversion Monitor")
    manager = ConversionManager()
    while True:
        try:
            active = manager.get_active()
            for conv in active:
                logger.debug("Conversion %s: %s", conv.id, conv.status.value)
                await manager.poll_conversion(conv.id)
            task_registry.heartbeat("conversion_monitor")
        except Exception as e:
            logger.error("Conversion monitor error: %s", e)
        await asyncio.sleep(60)


# ─── Optional Module Loader ─────────────────────────────────────────────────

def _try_load_optional(task_name: str, coro_factory):
    """
    Try to import the module used by an optional task.
    Returns (coro_factory, True) if available, (None, False) if missing.
    """
    from src.core.health import task_registry

    try:
        # Attempt a dry-run call to trigger ImportError early
        # We'll test by checking if the module can be imported
        coro_factory.__module__  # noop, just verify it's callable
        return coro_factory, True
    except Exception:
        return None, False


# ─── Main ────────────────────────────────────────────────────────────────────


async def _run_institutional_tracker():
    """Run institutional buy matching every 5 minutes."""
    import asyncio
    from src.services.institutional_tracker import get_institutional_tracker
    tracker = get_institutional_tracker()
    logger.info("Institutional tracker started")
    while True:
        try:
            matched = await tracker.run_pipeline()
            if matched:
                logger.info("Institutional tracker: %d new matches", matched)
        except Exception as e:
            logger.error("Institutional tracker error: %s", e)
        await asyncio.sleep(300)  # 5 min

async def main():
    """Main entry point with supervised task lifecycle."""
    from src.core.supervisor import run_supervised
    from src.core.health import task_registry
    from src.core.env_validator import validate_env, print_startup_summary

    # ── Validate environment ──
    features = validate_env(enable_cop=Config.ENABLE_COP)
    print_startup_summary(enable_cop=Config.ENABLE_COP, features=features)

    # P0-4: Log git SHA at startup for deployment verification
    from src.api.routes import get_git_sha
    git_sha = get_git_sha()
    logger.info("PearV2 version: %s", git_sha)

    # ── Register API clients ──
    register_apis()

    # ── Register /health endpoint ──
    _register_health_endpoint()

    # ── Build task list ──
    tasks = []

    # Critical: API Server (always)
    tasks.append(asyncio.create_task(
        run_supervised("api_server", _run_api_server, critical=True),
        name="api_server",
    ))

    if not Config.API_ONLY:
        # Critical: EUR Order Orchestrator
        tasks.append(asyncio.create_task(
            run_supervised("orchestrator", _run_orchestrator, critical=True),
            name="orchestrator",
        ))

        # Critical (if enabled): COP Handler
        if Config.ENABLE_COP:
            tasks.append(asyncio.create_task(
                run_supervised("cop_handler", _run_cop_handler, critical=True),
                name="cop_handler",
            ))
        else:
            task_registry.register_disabled("cop_handler", "ENABLE_COP=false")

        # Critical (if enabled): MXN Handler
        if Config.ENABLE_MXN:
            tasks.append(asyncio.create_task(
                run_supervised("mxn_handler", _run_mxn_handler, critical=False),
                name="mxn_handler",
            ))
        else:
            task_registry.register_disabled("mxn_handler", "ENABLE_MXN=false")

        # Optional: Liquidity Monitor
        _add_optional_task(tasks, "liquidity_monitor", _run_liquidity_monitor)

        # Optional: Ad Top-up
        _add_optional_task(tasks, "ad_topup", _run_ad_topup)

        # Optional: Conversion Monitor
        _add_optional_task(tasks, "conversion_monitor", _run_conversion_monitor)

        # Optional: Dynamic Pricing Engine
        _add_optional_task(tasks, "pricing_engine", _run_pricing_engine)

        # ── Stuck Order Monitor (Telegram alerts) ──
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        if telegram_token and telegram_chat_id:
            from src.services.telegram_notifier import TelegramNotifier
            from src.services.stuck_monitor import StuckOrderMonitor
            _telegram = TelegramNotifier(telegram_token, telegram_chat_id)
            _stuck_monitor = StuckOrderMonitor(notifier=_telegram)
            tasks.append(asyncio.create_task(
                _stuck_monitor.start(),
                name='stuck_monitor',
            ))
            logger.info('Stuck order monitor enabled (Telegram alerts)')

            # Telegram command polling (handles /pnl, /inventory, /status)
            tasks.append(asyncio.create_task(
                _telegram.poll_commands(),
                name='telegram_commands',
            ))

            # Daily P&L report at 23:59 UTC
            tasks.append(asyncio.create_task(
                _telegram.daily_report_loop(),
                name='daily_report',
            ))

            # Weekly P&L report (Sunday 23:59 UTC)
            tasks.append(asyncio.create_task(
                _telegram.weekly_report_loop(),
                name='weekly_report',
            ))

            # Daily channel cleanup (midnight UTC: purge alerts, resend status)
            tasks.append(asyncio.create_task(
                _stuck_monitor.daily_cleanup_loop(),
                name='daily_cleanup',
            ))
            logger.info('Telegram command handler + daily/weekly reports + cleanup enabled')
        else:
            logger.info('Stuck order monitor disabled (no TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID)')


    else:
        task_registry.register_disabled("orchestrator", "API_ONLY=true")
        task_registry.register_disabled("cop_handler", "API_ONLY=true")
        task_registry.register_disabled("liquidity_monitor", "API_ONLY=true")
        task_registry.register_disabled("ad_topup", "API_ONLY=true")
        task_registry.register_disabled("conversion_monitor", "API_ONLY=true")

    logger.info("Started %d background tasks", len(tasks))

    # ── Graceful shutdown ──
    def shutdown_handler(sig, frame):
        logger.info("Received %s — shutting down", signal.Signals(sig).name)
        for task in tasks:
            task.cancel()

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # ── Institutional Tracker Task ──
    tasks.append(asyncio.create_task(
        _run_institutional_tracker(),
        name='institutional_tracker',
    ))

    # ── Wait for all tasks ──
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error("Error in main loop: %s", e)

    logger.info("Shutdown complete")


async def _run_mxn_handler():
    """Run the MXN P2P handler."""
    from src.fiat.mxn.mxn_handler import MXNHandler

    handler = MXNHandler(
        binance_api_key=os.getenv("BINANCE_MXN_API_KEY", ""),
        binance_api_secret=os.getenv("BINANCE_MXN_API_SECRET", ""),
        binance_2fa_secret=os.getenv("BINANCE_MXN_2FA_SECRET", ""),
        fp_username=os.getenv("FACILITAPAY_USERNAME", ""),
        fp_password=os.getenv("FACILITAPAY_PASSWORD", ""),
        fp_cashin_account_id=os.getenv("FACILITAPAY_MXN_CASH_IN_ACCOUNT_ID", ""),
        fp_cashout_account_id=os.getenv("FACILITAPAY_MXN_CASHOUT_ACCOUNT_ID", ""),
        fp_webhook_secret=os.getenv("FACILITAPAY_WEBHOOK_SECRET", ""),
        poll_interval=Config.MXN_POLL_INTERVAL,
    )
    try:
        await handler.start()
    finally:
        await handler.close()


def _add_optional_task(tasks: list, name: str, coro_factory):
    """Add an optional task, testing its imports first."""
    from src.core.supervisor import run_supervised
    from src.core.health import task_registry

    try:
        # Force-import the module to catch ImportError before scheduling
        import importlib
        if name == "liquidity_monitor":
            importlib.import_module("src.services.liquidity_manager")
        elif name == "ad_topup":
            importlib.import_module("src.services.ad_rebalancer")
        elif name == "conversion_monitor":
            importlib.import_module("src.services.conversion_manager")
        elif name == "pricing_engine":
            importlib.import_module("src.services.pricing_engine")

        tasks.append(asyncio.create_task(
            run_supervised(name, coro_factory, critical=False, max_restarts=3),
            name=name,
        ))
    except ImportError as e:
        task_registry.register_disabled(name, f"Module not found: {e}")
        logger.warning("Optional task '%s' disabled — module not found: %s", name, e)


def _register_health_endpoint():
    """Add /health endpoint to the FastAPI app."""
    from src.api.main import app
    from src.core.health import task_registry

    @app.get("/health")
    async def health():
        """Task health report (unauthenticated)."""
        return task_registry.get_status()

    # ── Volume Analytics Endpoints ──
    @app.get("/api/volume-heatmap")
    async def volume_heatmap(days: int = 30):
        """24×7 order volume heatmap (hour-of-day × day-of-week)."""
        from src.services.volume_analytics import VolumeAnalytics
        analytics = VolumeAnalytics()
        return analytics.get_heatmap(min(days, 365))

    @app.get("/api/volume-stats")
    async def volume_stats(days: int = 30):
        """Volume summary: peak hour, busiest window, weekday vs weekend."""
        from src.services.volume_analytics import VolumeAnalytics
        analytics = VolumeAnalytics()
        return analytics.get_stats(min(days, 365))


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Parse args
    if "--dry-run" in sys.argv:
        os.environ["DRY_RUN"] = "true"
    if "--api-only" in sys.argv:
        os.environ["API_ONLY"] = "true"

    # Load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded .env file")
    except ImportError:
        logger.debug("python-dotenv not installed, using system env")

    # Re-read config after .env load
    Config.API_HOST = os.getenv("API_HOST", "0.0.0.0")
    Config.API_PORT = int(os.getenv("API_PORT", "8000"))
    Config.DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    Config.API_ONLY = os.getenv("API_ONLY", "false").lower() == "true"
    Config.ENABLE_COP = os.getenv("ENABLE_COP", "false").lower() == "true"
    Config.ENABLE_BRL = os.getenv("ENABLE_BRL", "false").lower() == "true"
    Config.ENABLE_MXN = os.getenv("ENABLE_MXN", "false").lower() == "true"
    Config.EXCHANGE_POLL_INTERVAL = float(os.getenv("EXCHANGE_POLL_INTERVAL", "5"))
    Config.BANK_POLL_INTERVAL = float(os.getenv("BANK_POLL_INTERVAL", "30"))
    Config.COP_POLL_INTERVAL = float(os.getenv("COP_POLL_INTERVAL", "30"))
    Config.MXN_POLL_INTERVAL = float(os.getenv("MXN_POLL_INTERVAL", "30"))

    # Run
    asyncio.run(main())
