"""
Binance P2P Chat Client (COP)
==============================
HTTP + WebSocket client for Binance P2P order management and chat.
Extracted from cop_standalone.py for PearV2.

SAFETY NOTES:
- release_crypto() is the IRREVERSIBLE action — once called, crypto is gone.
  Caller must ensure all guards (state, amount, lock) are satisfied first.
- Binance's releaseCoin API is naturally idempotent (releasing already-released
  order returns success), but we should not rely on this as the primary guard.
"""

import hmac
import time
import json
import asyncio
import hashlib
import urllib.parse
import logging
from typing import Any, Optional
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)


class BinanceChatClient:
    """
    Binance P2P API client for COP operations.

    Handles:
    - Fetching active P2P sell orders
    - Reading/sending chat messages via WebSocket
    - Releasing crypto (IRREVERSIBLE)
    - Marking messages as read
    """

    BASE_URL = "https://api.binance.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"X-MBX-APIKEY": api_key, "clientType": "web"},
            timeout=30.0,
        )

    def _sign(self, params: dict) -> dict:
        """Add timestamp and HMAC-SHA256 signature to params."""
        params["timestamp"] = int(time.time() * 1000)
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        sig = hmac.new(
            self.api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        params["signature"] = sig
        return params

    async def _signed_get(self, path: str, params: dict | None = None) -> dict:
        """GET with HMAC auth in query string (matches Binance SAPI spec)."""
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        sig = hmac.new(
            self.api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        url = f"{path}?{query}&signature={sig}"
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def _signed_post(self, path: str, body: dict | None = None) -> dict:
        """POST with JSON body and HMAC auth in query string (matches Binance SAPI spec)."""
        auth_params = self._sign({})
        query = urllib.parse.urlencode(auth_params)
        resp = await self.client.post(f"{path}?{query}", json=body or {})
        resp.raise_for_status()
        return resp.json()

    # ---- Orders ----

    async def get_active_orders(self) -> list[dict]:
        """Get active P2P orders (pending + paid) for both SELL and BUY."""
        all_orders = []
        # Binance uses numeric status: 1=pending, 2=paid, 5=appealed
        for trade_type in ["SELL", "BUY"]:
            for status in [1, 2]:
                try:
                    response = await self._signed_post(
                        "/sapi/v1/c2c/orderMatch/listOrders",
                        {"tradeType": trade_type, "orderStatus": status, "page": 1, "rows": 20}
                    )
                    if response.get("code") == "000000":
                        orders = response.get("data", [])
                        # Tag each order with its trade type for routing
                        for o in orders:
                            o["tradeType"] = trade_type
                        all_orders.extend(orders)
                except Exception as e:
                    logger.error(f"Error fetching {trade_type} orders (status={status}): {e}")
        return all_orders

    async def get_order_detail(self, order_number: str) -> dict | None:
        """Get detailed info for a specific order."""
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/getUserOrderDetail",
                {"adOrderNo": order_number, "clientType": "web"}
            )
            if response.get("code") == "000000":
                return response.get("data")
        except Exception as e:
            logger.error(f"Error fetching order detail: {e}")
        return None

    # ---- Chat ----

    async def get_chat_credentials(self) -> dict | None:
        """Get WebSocket chat credentials."""
        try:
            response = await self._signed_get("/sapi/v1/c2c/chat/retrieveChatCredential")
            if response.get("code") == "000000":
                return response.get("data")
        except Exception as e:
            logger.error(f"Error fetching chat credentials: {e}")
        return None

    async def get_chat_messages(self, order_id: str, page: int = 1, rows: int = 50) -> list[dict]:
        """Get chat messages for an order."""
        try:
            response = await self._signed_get(
                "/sapi/v1/c2c/chat/retrieveChatMessagesWithPagination",
                {"orderNo": order_id, "page": page, "rows": rows}
            )
            if response.get("code") == "000000":
                msgs = response.get("data", [])
                logger.debug(f"Chat messages for {order_id}: {len(msgs)} msgs")
                return msgs
            else:
                logger.warning(f"Chat response for {order_id}: code={response.get('code')} msg={response.get('message')}")
        except Exception as e:
            logger.error(f"Error fetching chat messages: {e}")
        return []

    async def send_chat_message(self, order_id: str, message: str) -> bool:
        """Send a chat message via WebSocket."""
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed. Run: pip install websockets")
            return False

        try:
            creds = await self.get_chat_credentials()
            if not creds:
                logger.error("Failed to get chat credentials")
                return False

            base_url = creds.get("chatWssUrl").rstrip('/')
            listen_key = creds.get("listenKey")
            listen_token = creds.get("listenToken")

            params = {"token": listen_token, "clientType": "web"}
            url = f"{base_url}/{listen_key}?{urllib.parse.urlencode(params)}"

            async with websockets.connect(url) as ws:
                send_msg = {
                    "action": "send",
                    "clientType": "web",
                    "orderNo": order_id,
                    "type": "text",
                    "content": message,
                    "uuid": str(uuid4())
                }

                await ws.send(json.dumps(send_msg))

                start_time = asyncio.get_event_loop().time()
                timeout = 5.0

                while True:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    if remaining <= 0:
                        logger.warning("Timed out waiting for ack, message may have sent.")
                        return True

                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        resp_data = json.loads(response)

                        if resp_data.get("self") is True and resp_data.get("content") == message:
                            logger.info(f"Chat sent to order {order_id}")
                            return True

                        if resp_data.get("error"):
                            logger.error(f"Chat send error: {resp_data}")
                            return False

                    except asyncio.TimeoutError:
                        logger.warning("Timed out waiting for ack, message may have sent.")
                        return True

        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
            return False

    async def mark_messages_read(self, order_id: str) -> bool:
        """Mark all messages for an order as read."""
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/chat/markOrderMessagesAsRead",
                {"orderNo": order_id}
            )
            return response.get("code") == "000000"
        except Exception:
            return False

    async def mark_order_paid(self, order_number: str) -> bool:
        """Mark a BUY order as paid on Binance.

        Called after COP payout is sent via FacilitaPay.
        SAFETY: This is NOT the irreversible action (COP send is).
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/markOrderAsPaid",
                {"orderNumber": order_number}
            )
            if response.get("code") == "000000":
                logger.info(f"Marked order {order_number} as paid")
                return True
            logger.warning(f"Failed to mark paid: {response.get('message')}")
            return False
        except Exception as e:
            logger.error(f"Error marking order paid: {e}")
            return False

    # ---- Release ----

    async def release_crypto(self, order_number: str, totp_secret: str = None) -> bool:
        """
        Release crypto for a SELL order. THIS IS IRREVERSIBLE.

        SAFETY: This method should ONLY be called after:
        1. Per-order lock acquired (M1)
        2. State is in RELEASABLE_STATES (handle_webhook guard)
        3. Amount verified against FacilitaPay (handle_webhook guard 3)
        4. Order transitioned to RELEASING state durably (before this call)

        Binance's releaseCoin is naturally idempotent (releasing an already-released
        order returns success or no-op), but we must not rely on this as primary protection.
        """
        body = {"orderNumber": order_number, "confirmSingleTrans": True}

        if totp_secret:
            try:
                import pyotp
                totp = pyotp.TOTP(totp_secret)
                body["googleVerifyCode"] = totp.now()  # Must match Binance spec
            except ImportError:
                logger.error("pyotp not installed. Run: pip install pyotp")
                return False

        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/releaseCoin",
                body
            )
            if response.get("code") == "000000":
                logger.info(f"Crypto released for order {order_number}")
                return True
            logger.error(f"Release failed: {response}")
            return False
        except httpx.HTTPStatusError as e:
            # Capture the full response body — critical for diagnosing Binance rejections
            body_text = e.response.text if e.response else "NO BODY"
            logger.error(
                f"Release HTTP error for {order_number}: "
                f"status={e.response.status_code} body={body_text}"
            )
            return False
        except Exception as e:
            logger.error(f"Error releasing crypto: {e}")
            return False

    async def close(self):
        await self.client.aclose()
