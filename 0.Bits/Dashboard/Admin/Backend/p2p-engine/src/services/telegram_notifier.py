"""
TelegramNotifier — send alerts + handle commands via Bot API.
Zero extra dependencies (uses aiohttp already in the project).
"""

import logging
import os
import asyncio
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger("telegram")


class TelegramNotifier:
    """Send messages to a Telegram channel and handle bot commands."""

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)
        self._api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self._update_offset = 0
        self._sent_message_ids: list[int] = []  # Track all messages sent for daily purge
        self._protected_ids: set[int] = set()  # P&L reports — never deleted

        if not self.enabled:
            logger.warning("TelegramNotifier disabled — TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")

    # ─── SEND ─────────────────────────────────────────────────────────────

    async def send_message(self, text: str, parse_mode: str = "HTML", chat_id: str | None = None) -> int | None:
        """Send a message. Returns message_id on success, None on failure. Never raises."""
        if not self.enabled:
            return None

        target_chat = chat_id or self.chat_id
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"{self._api_url}/sendMessage",
                    json={
                        "chat_id": target_chat,
                        "text": text,
                        "parse_mode": parse_mode,
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                if resp.status == 200:
                    data = await resp.json()
                    msg_id = data.get("result", {}).get("message_id")
                    if msg_id:
                        self._sent_message_ids.append(msg_id)
                    return msg_id
                body = await resp.text()
                logger.warning("Telegram API %d: %s", resp.status, body[:200])
                return None
        except Exception as e:
            logger.warning("Telegram send failed: %s", e)
            return None

    async def reply_to_message(self, message_id: int, text: str, parse_mode: str = "HTML") -> int | None:
        """Reply to a specific message. Returns new message_id or None."""
        if not self.enabled:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"{self._api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "reply_to_message_id": message_id,
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("result", {}).get("message_id")
                return None
        except Exception:
            return None

    async def delete_message(self, message_id: int) -> bool:
        """Delete a message. Returns True on success."""
        if not self.enabled:
            return False
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"{self._api_url}/deleteMessage",
                    json={"chat_id": self.chat_id, "message_id": message_id},
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                return resp.status == 200
        except Exception:
            return False

    async def send_stuck_alert(
        self,
        order_id: str,
        side: str,
        amount: str,
        currency: str,
        elapsed_seconds: float,
        reason: str,
        counterparty: str = "",
    ) -> bool:
        """Format and send a stuck-order alert."""
        emoji = "🔴" if elapsed_seconds > 300 else "⚠️"
        mins = int(elapsed_seconds // 60)
        secs = int(elapsed_seconds % 60)
        elapsed_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

        text = (
            f"{emoji} <b>STUCK {side.upper()} ORDER</b>\n"
            f"Order: <code>...{order_id[-8:]}</code>\n"
            f"Amount: {amount} {currency}\n"
            f"Stuck for: <b>{elapsed_str}</b>\n"
            f"\n"
            f"📋 <b>Reason:</b> {reason}\n"
        )
        if counterparty:
            text += f"\n🔗 Counterparty: {counterparty}"

        return await self.send_message(text)

    # ─── COMMAND POLLING ──────────────────────────────────────────────────

    async def poll_commands(self) -> None:
        """Long-poll Telegram for bot commands. Safe to run as asyncio.create_task()."""
        if not self.enabled:
            return

        logger.info("Telegram command polling started")

        while True:
            try:
                updates = await self._get_updates()
                for update in updates:
                    try:
                        await self._handle_update(update)
                    except Exception as e:
                        import traceback; traceback.print_exc(); logger.warning("Error handling update: %s", e)
                    self._update_offset = update["update_id"] + 1
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning("Telegram poll error: %s", e)
                await asyncio.sleep(5)
            await asyncio.sleep(2)

    async def _get_updates(self) -> list[dict]:
        """Fetch new updates from Telegram (long poll, 30s timeout)."""
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    f"{self._api_url}/getUpdates",
                    params={
                        "offset": self._update_offset,
                        "timeout": 30,
                        "allowed_updates": '["message","channel_post"]',
                    },
                    timeout=aiohttp.ClientTimeout(total=40),
                )
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data.get("result", [])
        except asyncio.CancelledError:
            raise
        except Exception:
            return []

    async def _handle_update(self, update: dict) -> None:
        """Route incoming message to the right handler."""
        msg = update.get("message") or update.get("channel_post") or {}
        text = msg.get("text", "").strip()
        chat_id = str(msg.get("chat", {}).get("id", ""))

        if not text.startswith("/"):
            return

        cmd = text.split()[0].lower().split("@")[0]  # Handle /cmd@botname
        print(f"CMD RECEIVED: {cmd} (full: {text[:50]}, chat: {chat_id})")

        # ─── P&L COMMANDS ─────────────────────────────────────────
        PNL_COMMANDS = {
            "/pnl": "today",
            "/pnl_today": "today",
            "/pnl_yesterday": "yesterday",
            "/pnl_week": "week",
            "/pnl_month": "month",
            "/pnl_year": "year",
            "/pnl_all": "all",
        }

        if cmd in PNL_COMMANDS:
            await self._handle_pnl(PNL_COMMANDS[cmd], chat_id)
        elif cmd == "/inventory":
            await self._handle_inventory(chat_id)
        elif cmd == "/status":
            await self._handle_status(chat_id)
        elif cmd == "/heatmap":
            await self._handle_heatmap(chat_id, text)
        elif cmd == "/spread":
            await self._handle_spread(chat_id)
        elif cmd == "/stats":
            await self._handle_stats(chat_id, text)
        elif cmd == "/competitors":
            await self._handle_competitors(chat_id)
        elif cmd == "/target":
            await self._handle_target(chat_id, text)
        elif cmd == "/help":
            await self._handle_help(chat_id)
        else:
            logger.debug("Unknown command: %s", cmd)

    async def _handle_pnl(self, period: str, chat_id: str) -> None:
        """Handle /pnl commands."""
        from src.services.pnl_tracker import get_fifo_tracker

        tracker = get_fifo_tracker()

        # Sync from Binance (respects 5min cooldown)
        await tracker.sync_from_binance()

        summary = tracker.get_summary(period)
        text = tracker.format_summary(summary)
        await self.send_message(text, chat_id=chat_id)

    async def _handle_inventory(self, chat_id: str) -> None:
        """Handle /inventory command."""
        from src.services.pnl_tracker import get_fifo_tracker

        tracker = get_fifo_tracker()
        await tracker.sync_from_binance()

        summary = tracker.compute_fifo()

        if summary.inventory_qty > 0:
            text = (
                "💰 <b>Current Inventory</b>\n\n"
                f"Units: <b>{summary.inventory_qty:.2f}</b>\n"
                f"Avg Cost: €{summary.inventory_avg_cost:.4f}/unit\n"
                f"Total Cost Basis: €{(summary.inventory_qty * summary.inventory_avg_cost):.2f}"
            )
        else:
            text = "💰 <b>Inventory:</b> Empty (all inventory sold)"

        await self.send_message(text, chat_id=chat_id)

    async def _handle_status(self, chat_id: str) -> None:
        """Handle /status command — show active orders."""
        from src.core.state_manager import state_manager

        active = state_manager.get_active_orders()
        if not active:
            await self.send_message("📋 <b>No active orders</b>", chat_id=chat_id)
            return

        lines = [f"📋 <b>Active Orders ({len(active)})</b>\n"]
        for m in active:
            o = m.order
            side_emoji = "🟢" if o.side.value == "buy" else "🔴"
            state = m.state.value if m.state else "?"
            cp = ""
            if o.counterparty:
                cp = o.counterparty.real_name or o.counterparty.name or ""
            lines.append(
                f"{side_emoji} {o.side.value.upper()} {o.fiat_amount} {o.fiat_currency.value if o.fiat_currency else '?'}"
                f" — <code>{state}</code>"
                f" — {cp[:20]}"
            )

        await self.send_message("\n".join(lines), chat_id=chat_id)

    async def _handle_heatmap(self, chat_id: str, text: str = "") -> None:
        """Handle /heatmap command. Supports /heatmap, /heatmap week, /heatmap month."""
        from src.services.order_analytics import get_analytics
        analytics = get_analytics()
        await analytics.sync_all_orders()

        parts = text.strip().split()
        period = parts[1] if len(parts) > 1 else "all"
        if period not in ("today", "week", "month", "year", "all"):
            period = "all"

        msg = analytics.get_heatmap(period=period)
        await self.send_message(msg, chat_id=chat_id)

    async def _handle_stats(self, chat_id: str, text: str = "") -> None:
        """Handle /stats command. Supports /stats, /stats week, /stats month."""
        from src.services.order_analytics import get_analytics
        analytics = get_analytics()
        await analytics.sync_all_orders()

        parts = text.strip().split()
        period = parts[1] if len(parts) > 1 else "today"
        if period not in ("today", "yesterday", "week", "month", "year", "all"):
            period = "today"

        msg = analytics.get_stats(period=period)
        await self.send_message(msg, chat_id=chat_id)

    async def _handle_spread(self, chat_id: str) -> None:
        """Handle /spread command."""
        from src.services.pnl_tracker import get_fifo_tracker
        tracker = get_fifo_tracker()
        await tracker.sync_from_binance()
        text = tracker.get_spread_analysis(days=30)
        await self.send_message(text, chat_id=chat_id)

    async def _handle_competitors(self, chat_id: str) -> None:
        """Handle /competitors command."""
        from src.services.market_intel import get_market_intel
        intel = get_market_intel()
        text = await intel.get_competitor_analysis()
        await self.send_message(text, chat_id=chat_id)

    async def _handle_target(self, chat_id: str, text: str = "") -> None:
        """Handle /target command. /target = show progress, /target 150 = set daily, /target 150 700 = set both."""
        from src.services.market_intel import get_market_intel
        intel = get_market_intel()

        parts = text.strip().split()
        if len(parts) == 1:
            msg = intel.get_target_progress()
        elif len(parts) == 2:
            try:
                daily = float(parts[1])
                msg = intel.set_targets(daily=daily)
            except ValueError:
                msg = "\u274c Usage: /target 150 (daily) or /target 150 700 (daily + weekly)"
        elif len(parts) >= 3:
            try:
                daily = float(parts[1])
                weekly = float(parts[2])
                msg = intel.set_targets(daily=daily, weekly=weekly)
            except ValueError:
                msg = "\u274c Usage: /target 150 (daily) or /target 150 700 (daily + weekly)"
        else:
            msg = intel.get_target_progress()

        await self.send_message(msg, chat_id=chat_id)

    async def _handle_help(self, chat_id: str) -> None:
        """Handle /help command."""
        text = (
            "\U0001f916 <b>PearV2 Bot Commands</b>\n\n"
            "<b>P&L Reports:</b>\n"
            "/pnl \u2014 Today\n"
            "/pnl_yesterday \u2014 Yesterday\n"
            "/pnl_week \u2014 This week\n"
            "/pnl_month \u2014 This month\n"
            "/pnl_year \u2014 This year\n"
            "/pnl_all \u2014 All-time\n\n"
            "<b>Analytics:</b>\n"
            "/stats \u2014 Completion rates + missed volume\n"
            "/stats week \u2014 Stats for this week\n"
            "/heatmap \u2014 Opened vs completed heatmap\n"
            "/heatmap month \u2014 Heatmap for this month\n"
            "/spread \u2014 Spread analysis + tips\n\n"
            "<b>Market Intel:</b>\n"
            "/competitors \u2014 Compare your ads vs market\n"
            "/target \u2014 Revenue target progress\n"
            "/target 150 700 \u2014 Set daily/weekly targets\n\n"
            "<b>Operations:</b>\n"
            "/inventory \u2014 Crypto inventory\n"
            "/status \u2014 Active orders\n"
            "/help \u2014 This message"
        )
        await self.send_message(text, chat_id=chat_id)

    async def purge_all_sent_messages(self) -> int:
        """Delete all non-protected messages the bot has sent. Returns count deleted."""
        deleted = 0
        remaining = []
        for mid in self._sent_message_ids:
            if mid in self._protected_ids:
                remaining.append(mid)
                continue
            if await self.delete_message(mid):
                deleted += 1
            await asyncio.sleep(0.1)  # Rate limit
        self._sent_message_ids = remaining
        return deleted

    # ─── DAILY REPORT ─────────────────────────────────────────────────────

    async def daily_report_loop(self) -> None:
        """Send automated daily P&L report at 23:59 UTC."""
        if not self.enabled:
            return

        logger.info("Daily P&L report scheduler started")

        while True:
            try:
                now = datetime.utcnow()
                target = now.replace(hour=23, minute=59, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)

                wait_seconds = (target - now).total_seconds()
                logger.debug("Next daily report in %.0f seconds", wait_seconds)
                await asyncio.sleep(wait_seconds)

                await self._send_daily_report()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning("Daily report error: %s", e)
                await asyncio.sleep(60)


    async def _send_daily_report(self) -> None:
        """Generate and send today's P&L report (protected from purge)."""
        from src.services.pnl_tracker import get_fifo_tracker

        tracker = get_fifo_tracker()
        await tracker.sync_from_binance(force=True)

        summary = tracker.get_summary("today")
        text = "\U0001f4c5 <b>End-of-Day Report</b>\n\n" + tracker.format_summary(summary)
        msg_id = await self.send_message(text)
        if msg_id:
            self._protected_ids.add(msg_id)
        logger.info("Daily P&L report sent (protected)")

    async def _send_weekly_report(self) -> None:
        """Generate and send this week's P&L report (protected from purge)."""
        from src.services.pnl_tracker import get_fifo_tracker

        tracker = get_fifo_tracker()
        await tracker.sync_from_binance(force=True)

        summary = tracker.get_summary("week")
        text = "\U0001f4c5 <b>Weekly Report</b>\n\n" + tracker.format_summary(summary)
        msg_id = await self.send_message(text)
        if msg_id:
            self._protected_ids.add(msg_id)
        logger.info("Weekly P&L report sent (protected)")

    async def weekly_report_loop(self) -> None:
        """Send weekly P&L report every Sunday at 23:59 UTC."""
        if not self.enabled:
            return
        logger.info("Weekly P&L report scheduler started")
        while True:
            try:
                now = datetime.utcnow()
                days_until_sunday = (6 - now.weekday()) % 7
                if days_until_sunday == 0 and (now.hour > 23 or (now.hour == 23 and now.minute >= 59)):
                    days_until_sunday = 7
                target = (now + timedelta(days=days_until_sunday)).replace(
                    hour=23, minute=59, second=0, microsecond=0
                )
                wait_seconds = (target - now).total_seconds()
                logger.debug("Next weekly report in %.0f seconds", wait_seconds)
                await asyncio.sleep(wait_seconds)
                await self._send_weekly_report()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning("Weekly report error: %s", e)
                await asyncio.sleep(60)
