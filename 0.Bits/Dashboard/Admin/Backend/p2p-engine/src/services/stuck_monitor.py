"""
StuckOrderMonitor — scans active orders and sends Telegram alerts when stuck.
Read-only: never modifies order state. Runs as a separate background coroutine.
"""

import asyncio
import logging
import time
import unicodedata
from datetime import datetime, timedelta
from typing import Any

from src.core.state_manager import StateManager, ManagedOrder, state_manager
from src.core.types import OrderSide, OrderState
from src.services.telegram_notifier import TelegramNotifier

logger = logging.getLogger("stuck_monitor")


class StuckOrderMonitor:
    """Monitors orders and sends Telegram alerts when stuck >1 min."""

    ALERT_THRESHOLD = 60       # 1 minute — first alert
    ESCALATION_THRESHOLD = 300 # 5 minutes — second (final) alert
    MAX_ALERTS_PER_ORDER = 2
    SCAN_INTERVAL = 30         # check every 30s

    def __init__(
        self,
        state: StateManager | None = None,
        notifier: TelegramNotifier | None = None,
    ):
        self._state = state or state_manager
        self._notifier = notifier or TelegramNotifier()
        self._alert_count: dict[str, int] = {}
        self._last_alert_time: dict[str, float] = {}
        self._alert_msg_ids: dict[str, list[int]] = {}
        self._startup_time = datetime.now()
        self._logger = logger

    async def start(self) -> None:
        """Run monitor loop. Safe to run as asyncio.create_task()."""
        self._logger.info("StuckOrderMonitor started (threshold=%ds, scan=%ds)",
                          self.ALERT_THRESHOLD, self.SCAN_INTERVAL)
        await asyncio.sleep(5)
        self._suppress_existing()

        while True:
            try:
                await self._scan()
            except Exception as e:
                self._logger.warning("StuckOrderMonitor scan error: %s", e)
            await asyncio.sleep(self.SCAN_INTERVAL)

    def _suppress_existing(self) -> None:
        """Mark all currently-stuck orders as already alerted (suppress on boot)."""
        try:
            active = self._state.get_active_orders()
            suppressed = 0
            for m in active:
                diag = self._diagnose(m)
                if diag and diag["elapsed"] >= self.ALERT_THRESHOLD:
                    self._alert_count[m.id] = self.MAX_ALERTS_PER_ORDER
                    suppressed += 1
            if suppressed:
                self._logger.info("Suppressed %d pre-existing stuck orders", suppressed)
        except Exception as e:
            self._logger.warning("Suppress existing error: %s", e)

    async def daily_cleanup_loop(self) -> None:
        """Every 24h at midnight UTC: purge all non-protected messages, resend status."""
        self._logger.info("Daily cleanup loop started")
        while True:
            try:
                now = datetime.utcnow()
                target = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                wait_seconds = (target - now).total_seconds()
                self._logger.debug("Next daily cleanup in %.0f seconds", wait_seconds)
                await asyncio.sleep(wait_seconds)

                deleted = await self._notifier.purge_all_sent_messages()
                self._logger.info("Daily cleanup: deleted %d messages", deleted)

                self._alert_count.clear()
                self._last_alert_time.clear()
                self._alert_msg_ids.clear()

                await self._send_status_summary()

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._logger.warning("Daily cleanup error: %s", e)
                await asyncio.sleep(60)

    async def _send_status_summary(self) -> None:
        """Send a summary of all current problems (stuck, appeals, errors)."""
        active = self._state.get_active_orders()
        if not active:
            await self._notifier.send_message(
                "\U0001f4cb <b>Daily Status:</b> No active orders \u2014 all clear! \u2705"
            )
            return

        problems = []
        normal = []
        for m in active:
            o = m.order
            state_val = m.state.value if m.state else "?"
            side = o.side.value.upper() if o.side else "?"
            amt = str(o.fiat_amount or "?")
            cur = o.fiat_currency.value if o.fiat_currency else "?"
            cp = ""
            if o.counterparty:
                cp = o.counterparty.real_name or o.counterparty.name or ""
            cp = cp[:25]

            if state_val in ("appealed", "error", "agent_required", "delayed"):
                problems.append(
                    "\U0001f534 " + side + " " + amt + " " + cur
                    + " \u2014 <code>" + state_val + "</code> \u2014 " + cp
                )
            elif state_val == "marked_as_paid":
                elapsed_str = ""
                if o.created_at:
                    mins = int((datetime.now() - o.created_at).total_seconds() / 60)
                    elapsed_str = " (" + str(mins) + "min)"
                emoji = "\u26a0\ufe0f" if side == "SELL" else "\U0001f7e1"
                problems.append(
                    emoji + " " + side + " " + amt + " " + cur
                    + " \u2014 <code>" + state_val + "</code>" + elapsed_str + " \u2014 " + cp
                )
            else:
                normal.append(
                    "\U0001f7e2 " + side + " " + amt + " " + cur
                    + " \u2014 <code>" + state_val + "</code> \u2014 " + cp
                )

        parts = ["\U0001f4cb <b>Daily Status Update</b>", ""]
        if problems:
            parts.append("\u26a0\ufe0f <b>Needs Attention (" + str(len(problems)) + "):</b>")
            parts.extend(problems)
        if normal:
            parts.append("")
            parts.append("\u2705 <b>Normal (" + str(len(normal)) + "):</b>")
            parts.extend(normal)

        msg = "\n".join(parts)
        await self._notifier.send_message(msg)

    async def _scan(self) -> None:
        """Scan all active orders for stuck conditions."""
        active = self._state.get_active_orders()
        now = time.time()

        active_ids = {m.id for m in active}
        for oid in list(self._alert_count.keys()):
            if oid not in active_ids:
                await self._resolve_alerts(oid)
                del self._alert_count[oid]
                self._last_alert_time.pop(oid, None)
                self._alert_msg_ids.pop(oid, None)

        for managed in active:
            count = self._alert_count.get(managed.id, 0)
            if count >= self.MAX_ALERTS_PER_ORDER:
                continue

            diagnosis = self._diagnose(managed)
            if not diagnosis:
                continue

            elapsed = diagnosis["elapsed"]

            should_alert = False
            if count == 0 and elapsed >= self.ALERT_THRESHOLD:
                should_alert = True
            elif count == 1 and elapsed >= self.ESCALATION_THRESHOLD:
                last = self._last_alert_time.get(managed.id, 0)
                if (now - last) >= 120:
                    should_alert = True

            if should_alert:
                order = managed.order
                cp_name = ""
                if order.counterparty:
                    cp_name = order.counterparty.real_name or order.counterparty.name or ""

                msg_id = await self._notifier.send_stuck_alert(
                    order_id=order.external_id,
                    side=order.side.value,
                    amount=str(order.fiat_amount),
                    currency=order.fiat_currency.value if order.fiat_currency else "?",
                    elapsed_seconds=elapsed,
                    reason=diagnosis["reason"],
                    counterparty=cp_name,
                )
                if msg_id:
                    self._alert_count[managed.id] = count + 1
                    self._last_alert_time[managed.id] = now
                    self._alert_msg_ids.setdefault(managed.id, []).append(msg_id)
                    self._logger.info(
                        "Stuck alert %d/%d sent for %s: %s",
                        count + 1, self.MAX_ALERTS_PER_ORDER,
                        order.external_id[-8:], diagnosis["reason"][:80],
                    )

    async def _resolve_alerts(self, order_id: str) -> None:
        """Reply to alert messages that order is resolved, then delete them."""
        msg_ids = self._alert_msg_ids.get(order_id, [])
        if not msg_ids:
            return

        await self._notifier.reply_to_message(
            msg_ids[0],
            "\u2705 Resolved \u2014 order completed or cancelled."
        )

        await asyncio.sleep(3)
        for mid in msg_ids:
            await self._notifier.delete_message(mid)

        self._logger.info(
            "Resolved alerts for order %s (%d messages deleted)",
            order_id[-8:] if len(order_id) >= 8 else order_id, len(msg_ids)
        )

    # ─── NAME ANALYSIS HELPERS ────────────────────────────────────────────

    def _has_non_latin(self, name: str) -> bool:
        """Check if name contains non-Latin script characters."""
        for ch in name:
            if unicodedata.category(ch).startswith("L"):
                try:
                    char_name = unicodedata.name(ch, "")
                    if char_name and not char_name.startswith("LATIN"):
                        return True
                except ValueError:
                    pass
        return False

    def _detect_script(self, name: str) -> str:
        """Detect the primary non-Latin script in a name."""
        scripts = set()
        for ch in name:
            if unicodedata.category(ch).startswith("L"):
                try:
                    char_name = unicodedata.name(ch, "")
                    if char_name:
                        script = char_name.split()[0]
                        if script != "LATIN":
                            scripts.add(script)
                except ValueError:
                    pass
        if "ARABIC" in scripts:
            return "Arabic"
        if "CYRILLIC" in scripts:
            return "Cyrillic"
        if any(s in scripts for s in ("CJK", "HANGUL", "HIRAGANA", "KATAKANA")):
            return "Asian"
        if scripts:
            return next(iter(scripts)).title()
        return "Latin"

    def _diagnose_sell_stuck(self, managed: ManagedOrder, elapsed: float) -> str:
        """Detailed diagnosis of why a sell order hasn't released."""
        order = managed.order
        cp_name = ""
        if order.counterparty:
            cp_name = order.counterparty.real_name or order.counterparty.name or ""

        checklist = []

        # Check 1: Non-Latin name
        if cp_name and self._has_non_latin(cp_name):
            script = self._detect_script(cp_name)
            checklist.append("\u274c " + script + " name \u2014 can't match SEPA sender")
            checklist.append("   " + cp_name[:35])
        elif cp_name:
            checklist.append("\u2705 Latin name: " + cp_name[:30])
        else:
            checklist.append("\u274c No counterparty name")

        # Check 2: Payment received?
        if managed.matched_payment:
            checklist.append("\u2705 EUR payment matched")
        else:
            checklist.append("\u274c No matching EUR payment yet")

        # Check 3: Human review / third-party
        if managed.needs_human_review:
            checklist.append("\u274c Flagged: possible third-party payment")

        # Check 4: KYC
        if hasattr(managed, 'needs_kyc') and managed.needs_kyc:
            checklist.append("\u274c KYC verification required")

        # Check 5: Last error
        if managed.last_error:
            checklist.append("\u274c " + managed.last_error[:60])

        # Check 6: Auto-release
        if managed.auto_release_approved:
            checklist.append("\u2705 Auto-release approved")

        mins = int(elapsed / 60)
        header = "\U0001f50d SELL stuck " + str(mins) + "min:"
        return header + "\n" + "\n".join(checklist)

    # ─── MAIN DIAGNOSTIC ─────────────────────────────────────────────────

    def _diagnose(self, managed: ManagedOrder) -> dict | None:
        """Determine WHY an order is stuck. Returns {reason, elapsed} or None."""
        order = managed.order
        now = datetime.now()

        if managed.paid_at:
            elapsed = (now - managed.paid_at).total_seconds()
        elif order.created_at:
            elapsed = (now - order.created_at).total_seconds()
        elif managed.created_at:
            elapsed = (now - managed.created_at).total_seconds()
        else:
            elapsed = 0

        if elapsed < self.ALERT_THRESHOLD:
            return None

        # BUY ORDERS
        if order.side == OrderSide.BUY:
            if managed.state == OrderState.AWAITING_PAYMENT:
                err = managed.last_error or ""
                if "no IBAN" in err.lower() or "no_iban" in err.lower():
                    return {"reason": "No IBAN in seller profile \u2014 polling chat for IBAN", "elapsed": elapsed}
                if "Non-SEPA" in err:
                    return {"reason": "IBAN blocked: non-SEPA country", "elapsed": elapsed}
                if "blocked" in err.lower():
                    return {"reason": "Payout blocked: " + err, "elapsed": elapsed}
                if err:
                    return {"reason": "Error: " + err, "elapsed": elapsed}
                if not managed.payout_details:
                    return {"reason": "Payout not prepared \u2014 fetching payment details", "elapsed": elapsed}
                return {"reason": "Payout prepared but not yet executed", "elapsed": elapsed}

            if managed.state == OrderState.ERROR:
                err = managed.last_error or "unknown"
                return {"reason": "ERROR: " + err, "elapsed": elapsed}

            if managed.state == OrderState.MARKED_AS_PAID:
                if elapsed > 300:
                    return {"reason": "EUR sent, waiting for seller to release crypto (" + str(int(elapsed/60)) + "m)", "elapsed": elapsed}
                return None

        # SELL ORDERS
        if order.side == OrderSide.SELL:
            return None
        if order.side == OrderSide.SELL:
            if managed.state == OrderState.MARKED_AS_PAID:
                if managed.matched_payment:
                    return {"reason": "\u2705 Payment matched but release not triggered yet", "elapsed": elapsed}
                return {"reason": self._diagnose_sell_stuck(managed, elapsed), "elapsed": elapsed}

            if managed.state == OrderState.ERROR:
                err = managed.last_error or "unknown"
                return {"reason": "\U0001f6a8 ERROR: " + err, "elapsed": elapsed}

            if managed.state == OrderState.RELEASING:
                err = managed.last_error or "API call pending"
                return {"reason": "\u23f3 Release in progress: " + err, "elapsed": elapsed}

            if managed.state == OrderState.DELAYED:
                cp_name = ""
                if order.counterparty:
                    cp_name = order.counterparty.real_name or order.counterparty.name or ""
                reason = "\u23f0 30min timeout \u2014 no matching EUR received"
                if cp_name and self._has_non_latin(cp_name):
                    script = self._detect_script(cp_name)
                    reason += "\n\u274c " + script + " name: " + cp_name[:30]
                return {"reason": reason, "elapsed": elapsed}

            if managed.state == OrderState.AGENT_REQUIRED:
                return {"reason": "\U0001f46e Agent required \u2014 needs manual review/KYC", "elapsed": elapsed}

            if managed.state == OrderState.APPEALED:
                cp_name = ""
                if order.counterparty:
                    cp_name = order.counterparty.real_name or order.counterparty.name or ""
                reason = "\u26a0\ufe0f APPEALED \u2014 needs manual intervention"
                if cp_name and self._has_non_latin(cp_name):
                    script = self._detect_script(cp_name)
                    reason += "\n\u274c " + script + " name: " + cp_name[:30]
                return {"reason": reason, "elapsed": elapsed}

        return None
