"""
TASK SUPERVISOR
===============
Production-grade background task lifecycle management.

Features:
- Logs task start/stop with structured logging
- Catches unhandled exceptions with full traceback
- Critical tasks terminate the process on failure
- Optional tasks log errors and continue
- Configurable auto-restart with backoff
- Heartbeat tracking for health reporting
"""

import asyncio
import logging
import os
import signal
import sys
import traceback
from datetime import datetime, timezone

from src.core.health import task_registry

logger = logging.getLogger("supervisor")


async def run_supervised(
    task_name: str,
    coro_factory,
    *,
    critical: bool = False,
    max_restarts: int = 0,
    restart_delay: float = 5.0,
    restart_backoff: float = 2.0,
    max_restart_delay: float = 300.0,
):
    """
    Run an async task with supervision.

    Args:
        task_name: Human-readable task identifier.
        coro_factory: Callable returning a coroutine (called on each restart).
        critical: If True, terminate process on unrecoverable failure.
        max_restarts: Maximum restart attempts (0 = no restarts).
        restart_delay: Initial delay between restarts in seconds.
        restart_backoff: Multiplier applied to delay after each restart.
        max_restart_delay: Cap on restart delay.
    """
    restarts = 0
    current_delay = restart_delay

    task_registry.register(task_name, critical=critical)

    while True:
        try:
            task_registry.mark_running(task_name)
            logger.info(
                "Task started",
                extra={"task": task_name, "critical": critical, "restart_count": restarts},
            )
            await coro_factory()

            # Clean exit (coroutine returned normally)
            logger.info("Task exited cleanly", extra={"task": task_name})
            task_registry.mark_stopped(task_name)
            return

        except asyncio.CancelledError:
            logger.info("Task cancelled", extra={"task": task_name})
            task_registry.mark_stopped(task_name)
            raise  # Propagate cancellation

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error(
                "Task crashed: %s",
                str(exc),
                extra={"task": task_name, "critical": critical, "traceback": tb},
            )
            task_registry.mark_error(task_name, str(exc))

            if critical:
                logger.critical(
                    "CRITICAL task failed — terminating process",
                    extra={"task": task_name, "error": str(exc)},
                )
                # Give other tasks a moment to flush logs
                await asyncio.sleep(0.5)
                os.kill(os.getpid(), signal.SIGTERM)
                return

            # Non-critical: attempt restart if allowed
            if restarts < max_restarts:
                restarts += 1
                logger.warning(
                    "Restarting task in %.1fs (attempt %d/%d)",
                    current_delay,
                    restarts,
                    max_restarts,
                    extra={"task": task_name},
                )
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * restart_backoff, max_restart_delay)
                continue
            else:
                logger.error(
                    "Task exhausted restart attempts — giving up",
                    extra={"task": task_name, "total_restarts": restarts},
                )
                task_registry.mark_stopped(task_name, permanent=True)
                return
