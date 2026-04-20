"""
TASK HEALTH REGISTRY
====================
In-memory registry tracking the state of all background tasks.

Provides:
- Task registration and lifecycle tracking
- Heartbeat mechanism for liveness detection
- Serializable status for /health endpoint
- Thread-safe via asyncio (single-threaded event loop)
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("health")


@dataclass
class TaskStatus:
    """State of a single supervised task."""

    name: str
    critical: bool = False
    running: bool = False
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    last_heartbeat: Optional[str] = None
    last_error: Optional[str] = None
    error_count: int = 0
    permanent_failure: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "critical": self.critical,
            "running": self.running,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "last_heartbeat": self.last_heartbeat,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "permanent_failure": self.permanent_failure,
        }



# P1-2: Tasks not heartbeating within this window are considered stale
STALE_THRESHOLD_SECONDS = 300  # 5 minutes


class TaskRegistry:
    """Global registry for background task health tracking."""

    def __init__(self):
        self._tasks: dict[str, TaskStatus] = {}
        self._disabled: list[dict] = []

    def register(self, name: str, *, critical: bool = False) -> None:
        self._tasks[name] = TaskStatus(name=name, critical=critical)
        logger.debug("Registered task: %s (critical=%s)", name, critical)

    def register_disabled(self, name: str, reason: str) -> None:
        """Record a task that was intentionally not started."""
        self._disabled.append({"name": name, "reason": reason})
        logger.info("Task disabled: %s — %s", name, reason)

    def mark_running(self, name: str) -> None:
        if name in self._tasks:
            now = _now()
            self._tasks[name].running = True
            self._tasks[name].started_at = now
            self._tasks[name].last_heartbeat = now

    def mark_stopped(self, name: str, *, permanent: bool = False) -> None:
        if name in self._tasks:
            self._tasks[name].running = False
            self._tasks[name].stopped_at = _now()
            self._tasks[name].permanent_failure = permanent

    def mark_error(self, name: str, error: str) -> None:
        if name in self._tasks:
            self._tasks[name].last_error = error
            self._tasks[name].error_count += 1
            self._tasks[name].running = False

    def heartbeat(self, name: str) -> None:
        if name in self._tasks:
            self._tasks[name].last_heartbeat = _now()

    def _is_stale(self, task: TaskStatus) -> bool:
        """P1-2: Check if a running task's heartbeat is older than threshold."""
        if not task.running or not task.last_heartbeat:
            return False
        try:
            last_hb = datetime.fromisoformat(task.last_heartbeat)
            age = (datetime.now(timezone.utc) - last_hb).total_seconds()
            return age > STALE_THRESHOLD_SECONDS
        except (ValueError, TypeError):
            return False

    def get_status(self) -> dict:
        """Full health report for /health endpoint."""
        now_str = _now()
        tasks = []
        stale_tasks = []
        for t in self._tasks.values():
            td = t.to_dict()
            td["stale"] = self._is_stale(t)
            if td["stale"]:
                stale_tasks.append(t.name)
            tasks.append(td)

        # P1-2: A critical task that is stale counts as not running
        critical_ok = all(
            t.running and not self._is_stale(t)
            for t in self._tasks.values() if t.critical
        )
        any_error = any(t.last_error for t in self._tasks.values())

        if critical_ok and not any_error and not stale_tasks:
            overall = "healthy"
        elif critical_ok and not stale_tasks:
            overall = "degraded"
        else:
            overall = "unhealthy"

        result = {
            "status": overall,
            "tasks": tasks,
            "disabled": self._disabled,
            "timestamp": now_str,
        }
        if stale_tasks:
            result["stale_tasks"] = stale_tasks
            logger.warning("Stale tasks detected: %s", stale_tasks)

        # P0-A: Alert if any mark_paid operations are stuck > 5 min
        try:
            from src.core.persistence import order_db
            pending = order_db.get_pending_mark_paids()
            if pending:
                stuck = []
                for row in pending:
                    claimed = datetime.fromisoformat(row["claimed_at"])
                    age_min = (datetime.now(timezone.utc) - claimed.replace(tzinfo=timezone.utc)).total_seconds() / 60
                    if age_min > 5:
                        stuck.append({
                            "order_id": row["order_id"],
                            "retries": row["mark_paid_retries"],
                            "stuck_minutes": round(age_min, 1),
                        })
                if stuck:
                    result["mark_paid_stuck"] = stuck
                    result["status"] = "unhealthy"
                    logger.critical("MARK_PAID STUCK: %d orders pending > 5min", len(stuck))
        except Exception:
            pass  # Health check must not crash

        return result


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Global singleton
task_registry = TaskRegistry()
