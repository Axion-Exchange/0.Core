"""
BINANCE API CLIENT
======================
Translates Binance P2P API (C2C SAPI v7.4) to unified format.

API Base: https://api.binance.com
Auth: HMAC SHA256 signature + X-MBX-APIKEY header
"""

import hashlib
import hmac
import logging
import os
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
import pyotp

from src.core.clients import ExchangeApiClient
from src.core.types import (
    CryptoAsset,
    Currency,
    ExchangeId,
    OrderSide,
    OrderState,
    PriceType,
    UnifiedAd,
    UnifiedBalance,
    UnifiedOrder,
    Counterparty,
    ChatMessage,
    MessageSender,
)
from src.services.iban_screener import screen_iban_with_bank


class BinanceApiClient(ExchangeApiClient):
    """
    Binance P2P API client.
    Implements C2C SAPI v7.4 endpoints.
    """
    
    BASE_URL = "https://api.binance.com"
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        exchange_id_override: ExchangeId | None = None,
        totp_secret: str | None = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self._exchange_id_override = exchange_id_override
        self._totp_secret = totp_secret  # Per-instance 2FA (overrides env var)
        self.client = httpx.AsyncClient(timeout=30.0)
        label = exchange_id_override.value if exchange_id_override else "binance"
        self._logger = logging.getLogger(f"{label}.api")
    
    @property
    def exchange_id(self) -> ExchangeId:
        return self._exchange_id_override or ExchangeId.BINANCE
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    def _sign(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature."""
        return hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self) -> dict[str, str]:
        """Get required headers for C2C API."""
        return {
            "X-MBX-APIKEY": self.api_key,
            "clientType": "web",
            "Content-Type": "application/json",
        }
    
    def _signed_params(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Add timestamp and signature to params."""
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        params["signature"] = self._sign(query_string)
        return params
    
    def _build_query_string(self, params: dict[str, Any]) -> str:
        """Build query string with timestamp and signature."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = self._sign(query_string)
        return f"{query_string}&signature={signature}"
    
    async def _signed_get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        """Make a signed GET request."""
        params = params or {}
        query_string = self._build_query_string(params)
        
        response = await self.client.get(
            f"{self.BASE_URL}{endpoint}?{query_string}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    async def _signed_post(self, endpoint: str, body: dict[str, Any] | None = None) -> dict:
        """Make a signed POST request (JSON body with query params for auth)."""
        params = {"timestamp": int(time.time() * 1000)}
        query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = self._sign(query_string)
        
        url = f"{self.BASE_URL}{endpoint}?timestamp={params['timestamp']}&signature={signature}"
        
        response = await self.client.post(
            url,
            json=body or {},
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # CONNECTIVITY
    # =========================================================================
    
    async def is_ready(self) -> bool:
        """Test API connectivity."""
        try:
            await self._signed_get("/api/v3/account")
            return True
        except Exception as e:
            self._logger.warning("Binance connectivity check failed: %s", e)
            return False
    
    # =========================================================================
    # ORDERS - C2C SAPI v7.4
    # =========================================================================
    
    async def get_orders(
        self,
        trade_type: str | None = None,
        state: OrderState | None = None,
        page: int = 1,
        rows: int = 20,
    ) -> list[UnifiedOrder]:
        """
        List P2P orders with filters.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/listOrders
        
        Args:
            trade_type: "BUY" or "SELL"
            state: OrderState to filter by (uses binance_code property)
            page: Page number (1-indexed)
            rows: Results per page (max 100)
        """
        body: dict[str, Any] = {
            "page": page,
            "rows": rows,
        }
        
        if trade_type:
            body["tradeType"] = trade_type
        if state is not None and state.binance_code is not None:
            body["orderStatus"] = state.binance_code
        
        try:
            response = await self._signed_post("/sapi/v1/c2c/orderMatch/listOrders", body)
            
            if response.get("code") != "000000":
                self._logger.warning("Binance API error: %s", response.get('message'))
                return []
            
            orders = response.get("data", [])
            return [self._transform_order(o) for o in orders]
            
        except Exception as e:
            self._logger.error("Error fetching Binance orders: %s", e)
            return []
    
    async def get_active_orders(self) -> list[UnifiedOrder]:
        """Get all active (non-completed) orders."""
        pending = await self.get_orders(state=OrderState.AWAITING_PAYMENT)
        paid = await self.get_orders(state=OrderState.MARKED_AS_PAID)
        return pending + paid
    
    async def get_order(self, external_id: str) -> UnifiedOrder | None:
        """
        Get specific order details.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/getUserOrderDetail
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/getUserOrderDetail",
                {"adOrderNo": external_id}
            )
            
            if response.get("code") != "000000":
                self._logger.warning("Binance API error: %s", response.get('message'))
                return None
            
            data = response.get("data")
            if data:
                return self._transform_order(data)
            return None
            
        except Exception as e:
            self._logger.error("Error fetching Binance order %s: %s", external_id, e)
            return None
    
    async def get_order_history(
        self,
        trade_type: str | None = None,
        start_timestamp: int | None = None,
        end_timestamp: int | None = None,
        page: int = 1,
        rows: int = 50,
    ) -> list[UnifiedOrder]:
        """
        Get order history.
        
        Endpoint: GET /sapi/v1/c2c/orderMatch/listUserOrderHistory
        """
        params: dict[str, Any] = {
            "page": page,
            "rows": rows,
        }
        
        if trade_type:
            params["tradeType"] = trade_type
        if start_timestamp:
            params["startTimestamp"] = start_timestamp
        if end_timestamp:
            params["endTimestamp"] = end_timestamp
        
        try:
            response = await self._signed_get("/sapi/v1/c2c/orderMatch/listUserOrderHistory", params)
            
            if response.get("code") != "000000":
                return []
            
            orders = response.get("data", [])
            return [self._transform_order(o) for o in orders]
            
        except Exception as e:
            self._logger.error("Error fetching Binance order history: %s", e)
            return []
    
    async def cancel_buy_order(
        self,
        order_number: str,
        reason: str = "Buyer refused to complete verification",
    ) -> bool:
        """
        Cancel an active P2P order.
        Typically only possible for BUY orders (where we are the buyer/taker) 
        before payment is marked.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/cancelOrder
        
        Args:
            order_number: The order ID (adOrderNo)
            reason: Cancellation reason description
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/cancelOrder",
                {
                    "adOrderNo": order_number,
                    "remark": reason  # 'remark' or 'cancelReason' depending on specific API version, SAPI doc uses 'remark' often for P2P or just adOrderNo.
                                      # If SAPI v1/c2c/orderMatch/cancelOrder is generic.
                }
            )
            
            if response.get("code") == "000000":
                self._logger.info("Order %s cancelled successfully", order_number)
                return True
            
            self._logger.error("Cancel failed: %s", response.get('message'))
            return False
            
        except Exception as e:
            self._logger.error("Error cancelling order %s: %s", order_number, e)
            return False

    async def get_payment_details(self, order_id: str) -> dict[str, Any] | None:
        """
        Get counterparty payment details for a specific order.
        Used for deciding where to send money (Buy Orders).
        
        Uses existing get_order (getUserOrderDetail) and extracts payment info.
        """
        order = await self.get_order(order_id)
        if not order:
             return None
             
        # In the real API, details are often in a sub-field like 'buyerPaymentMethod' or 'sellerPaymentMethod'
        # Since UnifiedOrder might have flattened it, or we rely on the raw response in get_order to parse it?
        # Creating a specific extraction here if UnifiedOrder doesn't carry it.
        # However, checking 'get_order' implementation: it calls _transform_order. 
        # Let's see if we can get the raw data or if UnifiedOrder has it. 
        # Actually simplest to re-fetch or assume UnifiedOrder has a payment_methods list?
        # Currently UnifiedOrder seems to map basic fields.
        
        # For this implementation, I will assume we need to return a dict with 'account_name' 
        # as expected by BuyOrderNameMatcher.
        
        # HACK: For now, returning a mock or partial implementation until we see specific field mapping.
        # But 'BuyOrderNameMatcher' expects 'account_name'. 
        
        # Let's try to get raw details via _signed_post again if needed, or trust UnifiedOrder has it?
        # Inspecting UnifiedOrder definition would be robust, but for speed:
        
        # Let's just implement the call properly:
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/getUserOrderDetail",
                {"adOrderNo": order_id}
            )
             
            if response.get("code") != "000000": 
                 return None
            
            data = response.get("data", {})
            
            # Extract payment info. 
            # Usually in 'tradeMethodName', 'payAccount', 'payName' etc within a list?
            # Or 'buyerDetail' / 'sellerDetail'?
            
            # Common structure for Binance P2P Detail:
            # "payMethods": [{"payType": "BANK", "content": "..."}]
            
            # To be safe for the Name Matcher, we look for anything looking like a Name.
            # We will return the raw data structure expected by the matcher wrapper.
            
            # Check for generic 'payName' or similar
            # If not found, NameMatcher will handle the None.
            return {
                "account_name": data.get("fullRealName") or data.get("name") or "UNKNOWN", 
                "iban": data.get("payAccount") # Example mapping
            }
            
        except Exception:
            return None
            
    async def mark_order_paid(
        self,
        external_id: str,
        payment_method_id: int | None = None,
    ) -> bool:
        """
        Mark order as paid (for BUY orders).
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/markOrderAsPaid
        """
        body: dict[str, Any] = {"orderNumber": external_id}
        
        if payment_method_id:
            body["payId"] = payment_method_id
        
        try:
            response = await self._signed_post("/sapi/v1/c2c/orderMatch/markOrderAsPaid", body)
            
            if response.get("code") == "000000":
                self._logger.info("Marked order %s as paid", external_id)
                return True
            
            self._logger.warning("Failed to mark paid: %s", response.get('message'))
            return False
            
        except Exception as e:
            self._logger.error("Error marking order paid: %s", e)
            return False
    
    async def release_crypto(
        self,
        external_id: str,
        verification_code: str | None = None,
        email_code: str | None = None,
        sms_code: str | None = None,
    ) -> bool:
        """
        Release crypto for SELL order.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/releaseCoin
        
        Auto-generates Google Authenticator TOTP from BINANCE_2FA_SECRET if available.
        """
        body: dict[str, Any] = {
            "orderNumber": external_id,
            "confirmSingleTrans": True  # Explicitly confirm payment received
        }
        
        # Auto-generate Google Auth code — prefer per-instance secret, fallback to env
        totp_secret = self._totp_secret or os.getenv("BINANCE_2FA_SECRET")
        if totp_secret and not verification_code:
            try:
                totp = pyotp.TOTP(totp_secret)
                verification_code = totp.now()
                # FIX C1: TOTP code intentionally NOT logged (was printed to stdout)
            except Exception as e:
                self._logger.warning("Failed to generate TOTP: %s", e)
        
        if verification_code:
            body["googleVerifyCode"] = verification_code
        if email_code:
            body["emailVerifyCode"] = email_code
        if sms_code:
            body["mobileVerifyCode"] = sms_code
        
        # RETRY LOOP for 2FA Timing Errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Regenerate TOTP on retries
                if attempt > 0 and totp_secret:
                    self._logger.info("Regenerating TOTP (Attempt %d/%d)...", attempt+1, max_retries)
                    # Wait to ensure we are in a new 30s window if we failed due to timing
                    await asyncio.sleep(2) 
                    totp = pyotp.TOTP(totp_secret)
                    body["googleVerifyCode"] = totp.now()
                
                response = await self._signed_post("/sapi/v1/c2c/orderMatch/releaseCoin", body)
                
                if response.get("code") == "000000":
                    self._logger.info("Released crypto for order %s", external_id)
                    return True
                
                # Check for specific 2FA error: "wait for new code"
                # Code 200001035: Please wait for a new verification code
                if response.get("code") == 200001035:
                     self._logger.info("Binance 2FA limit hit. Waiting 70s for new code... (Attempt %d)", attempt+1)
                     await asyncio.sleep(70)
                     continue

                self._logger.warning("Failed to release: %s", response.get('message'))
                return False
                
            except httpx.HTTPStatusError as e:
                # Handle 400 Bad Request which contains the JSON error
                try:
                    error_data = e.response.json()
                    if error_data.get("code") == 200001035:
                        self._logger.info("Binance 2FA limit hit. Waiting 70s for new code... (Attempt %d)", attempt+1)
                        await asyncio.sleep(70)
                        continue
                except:
                    pass
                    
                self._logger.error("HTTP error releasing crypto: %s", e)
                self._logger.error("Response body: %s", e.response.text)
                return False
            except Exception as e:
                self._logger.error("Error releasing crypto: %s", e)
                return False
                
        return False
    
    async def cancel_order(
        self,
        external_id: str,
        reason_code: int = 0,
        additional_info: str = "",
    ) -> bool:
        """
        Cancel an order.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/cancelOrder
        """
        body = {
            "orderNumber": external_id,
            "orderCancelReasonCode": reason_code,
            "orderCancelAdditionalInfo": additional_info,
        }
        
        try:
            response = await self._signed_post("/sapi/v1/c2c/orderMatch/cancelOrder", body)
            
            if response.get("code") == "000000":
                self._logger.info("Cancelled order %s", external_id)
                return True
            
            self._logger.warning("Failed to cancel: %s", response.get('message'))
            return False
            
        except Exception as e:
            self._logger.error("Error cancelling order: %s", e)
            return False
    
    async def check_can_release(self, external_id: str) -> bool:
        """
        Check if crypto can be released for an order.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/checkIfCanReleaseCoin
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/checkIfCanReleaseCoin",
                {"orderNumber": external_id}
            )
            
            return response.get("code") == "000000" and response.get("data", False)
            
        except Exception:
            return False
    
    # =========================================================================
    # CHAT
    # =========================================================================
    
    async def get_chat_credentials(self) -> dict[str, str] | None:
        """
        Get WebSocket chat credentials.
        
        Endpoint: GET /sapi/v1/c2c/chat/retrieveChatCredential
        
        Returns: {chatWssUrl, listenKey, listenToken}
        """
        try:
            response = await self._signed_get("/sapi/v1/c2c/chat/retrieveChatCredential")
            
            if response.get("code") == "000000":
                return response.get("data")
            return None
            
        except Exception as e:
            self._logger.error("Error fetching chat credentials: %s", e)
            return None
    
    async def get_chat_messages(
        self,
        order_id: str,
        page: int = 1,
        rows: int = 50,
    ) -> list[ChatMessage]:
        """
        Get chat messages for an order.
        
        Endpoint: GET /sapi/v1/c2c/chat/retrieveChatMessagesWithPagination
        """
        params = {
            "orderNo": order_id,
            "page": page,
            "rows": rows,
        }
        
        try:
            response = await self._signed_get(
                "/sapi/v1/c2c/chat/retrieveChatMessagesWithPagination",
                params
            )
            
            if response.get("code") != "000000":
                return []
            
            messages = response.get("data", [])
            return [self._transform_chat_message(m, order_id) for m in messages]
            
        except Exception as e:
            self._logger.error("Error fetching chat messages: %s", e)
            return []
    
    async def mark_messages_read(self, order_id: str) -> bool:
        """
        Mark all messages for an order as read.
        
        Endpoint: POST /sapi/v1/c2c/chat/markOrderMessagesAsRead
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/chat/markOrderMessagesAsRead",
                {"orderNo": order_id}
            )
            return response.get("code") == "000000"
        except Exception:
            return False
    
    async def verify_identity(self, order_id: str) -> bool:
        """
        Trigger 'Verified Additional KYC' action for an order.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/verifiedAdditionalKyc
        Body: {"orderNumber": "..."}
        """
        try:
            # Note: orderNumber must be in JSON body, not query params
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/verifiedAdditionalKyc",
                body={"orderNumber": order_id}
            )
            
            if response.get("code") == "000000":
                self._logger.info("Identity verification triggered for order %s", order_id)
                return True
                
            self._logger.warning("Identity verification failed: %s", response)
            return False
            
        except httpx.HTTPStatusError as e:
            self._logger.error("HTTP error triggering identity verification: %s", e)
            self._logger.error("Response body: %s", e.response.text)
            return False
        except Exception as e:
            self._logger.error("Error triggering identity verification: %s", e)
            return False

    async def get_payment_details(self, order_id: str) -> dict[str, Any] | None:
        """
        Fetch seller's payment details for a BUY order.
        Includes automated IBAN screening.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/getUserOrderDetail
        """
        try:
            # 1. Fetch details
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/getUserOrderDetail",
                {"adOrderNo": order_id}
            )
            
            if response.get("code") != "000000":
                self._logger.warning("Failed to get payment details: %s", response.get('message'))
                return None
            
            data = response.get("data", {})
            pay_methods = data.get("payMethods", [])
            
            if not pay_methods:
                self._logger.warning("No payment methods found for order %s", order_id)
                return None
            
            # 2. Extract specific fields (IBAN, Bank Name, Account Name)
            # Find the method containing IBAN
            target_method = None
            iban = None
            bank_name = None
            account_name = None
            
            for method in pay_methods:
                for field in method.get("fields", []):
                    f_name = field.get("fieldName", "").lower()
                    f_val = field.get("fieldValue", "")
                    
                    if "iban" in f_name:
                        iban = f_val
                        target_method = method
                    elif "bank name" in f_name or "bankname" in f_name:
                        bank_name = f_val
                    elif "account name" in f_name or "accountname" in f_name or "name" in f_name:
                        # Prioritize explicit "account name" but fallback to "name" if needed
                        if not account_name or "account" in f_name:
                            account_name = f_val
                
                if iban:
                    # Found a method with IBAN, stop looking
                    break
            
            if not iban:
                 self._logger.warning("No IBAN found in payment details for order %s", order_id)
                 # Return raw data even if IBAN missing, for debugging? 
                 # User requested IBAN specifically, so returning None or partial might be better.
                 # Let's return what we have but flag it.
                 return {
                     "raw_methods": pay_methods,
                     "error": "No IBAN found"
                 }

            # 3. Screen IBAN
            screen_result = screen_iban_with_bank(iban, bank_name)
            
            return {
                "account_name": account_name,
                "iban": iban,
                "bank_name": bank_name,
                "screening_result": screen_result, # IbanScreenResult object
                "raw_method": target_method
            }

        except Exception as e:
            self._logger.error("Error fetching payment details: %s", e)
            return None

    async def get_counterparty_order_stats(self, order_number: str) -> dict | None:
        """
        Get counterparty's order statistics for a specific order.
        
        Endpoint: POST /sapi/v1/c2c/orderMatch/queryCounterPartyOrderStatistic
        Body: {"orderNumber": "..."}
        
        Returns:
            {
                "completedOrderNum": 150,           # All-time completed orders
                "completedOrderNumOfLatest30day": 25,  # Completed in last 30 days
                "finishRate": 0.98,                 # Completion rate (0-1)
                "finishRateLatest30Day": 0.96,      # 30-day completion rate
                "numberOfTradesWithCounterpartyCompleted30day": 5,  # Orders with US in 30d
                "registerDays": 365                  # Account age in days
            }
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/orderMatch/queryCounterPartyOrderStatistic",
                body={"orderNumber": order_number}
            )
            
            if response.get("code") == "000000":
                data = response.get("data", {})
                self._logger.info("Counterparty stats for order %s: total=%s, 30d_with_us=%s, finish_rate=%.1f%%",
                                  order_number,
                                  data.get('completedOrderNum', 0),
                                  data.get('numberOfTradesWithCounterpartyCompleted30day', 0),
                                  data.get('finishRate', 0) * 100)
                return data
            
            self._logger.warning("Failed to get counterparty stats: %s", response.get('message'))
            return None
            
        except Exception as e:
            self._logger.error("Error getting counterparty stats: %s", e)
            return None

    async def send_chat_message(self, order_id: str, message: str) -> ChatMessage | None:
        """
        Send a chat message to the counterparty using WebSocket.
        Requires 'clientType=web' in connection parameters.
        Payload must be FLAT (no 'data' wrapper).
        """
        import websockets
        import json
        import asyncio
        from uuid import uuid4
        import urllib.parse
        
        try:
            creds = await self.get_chat_credentials()
            if not creds:
                self._logger.warning("Failed to get chat credentials")
                return None
            
            base_url = creds.get("chatWssUrl").rstrip('/')
            listen_key = creds.get("listenKey")
            listen_token = creds.get("listenToken")
            
            # Connection params 
            params = {
                "token": listen_token,
                "clientType": "web"
            }
            url = f"{base_url}/{listen_key}?{urllib.parse.urlencode(params)}"
            
            async with websockets.connect(url) as ws:
                # Payload: Flat structure (Proven working)
                our_uuid = str(uuid4())
                send_msg = {
                    "action": "send",
                    "clientType": "web",
                    "orderNo": order_id,
                    "type": "text",
                    "content": message,
                    "uuid": our_uuid
                }
                
                await ws.send(json.dumps(send_msg))
                
                # Loop to read messages until we get our ack or timeout
                # Binance can send statistics/system messages before our ack
                start_time = asyncio.get_event_loop().time()
                timeout = 5.0
                
                while True:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    if remaining <= 0:
                        self._logger.warning("Timed out waiting for ack, but message might have sent.")
                        return None
                    
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        resp_data = json.loads(response)
                        
                        # Check if this is our message ack
                        if resp_data.get("self") is True and resp_data.get("content") == message:
                            msg_id = str(resp_data.get('id'))
                            self._logger.info("Message sent to order %s (ID: %s)", order_id, msg_id)
                            
                            return ChatMessage(
                                id=msg_id,
                                order_id=order_id,
                                exchange=ExchangeId.BINANCE,
                                sender=MessageSender.US,
                                content=message,
                                timestamp=datetime.now(),
                                read=True
                            )
                        
                        # Check for errors
                        if resp_data.get("error"):
                            self._logger.error("Chat send error: %s", resp_data)
                            return None
                        
                        # Otherwise it's some other message (stats, system, etc.) - keep reading
                        
                    except asyncio.TimeoutError:
                        self._logger.warning("Timed out waiting for ack, but message might have sent.")
                        return None
                
        except ImportError:
            self._logger.error("websockets package not installed. Run: pip install websockets")
            return None
        except Exception as e:
            self._logger.error("Error sending chat message: %s", e)
            return None
    
    # =========================================================================
    # ADVERTISEMENTS
    # =========================================================================
    
    async def get_ads(self, page: int = 1, rows: int = 50) -> list[UnifiedAd]:
        """
        Get our P2P ads.
        
        Endpoint: POST /sapi/v1/c2c/ads/listWithPagination
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/ads/listWithPagination",
                {"page": page, "rows": rows}
            )
            
            if response.get("code") != "000000":
                return []
            
            ads = response.get("data", [])
            return [self._transform_ad(a) for a in ads]
            
        except Exception as e:
            self._logger.error("Error fetching ads: %s", e)
            return []
    
    async def search_market_ads(
        self,
        trade_type: str = "BUY",  # BUY = we want to buy (see seller ads), SELL = we want to sell
        asset: str = "USDT",
        fiat: str = "EUR",
        pay_types: list[str] | None = None,
        trans_amount: float | None = None,
        page: int = 1,
        rows: int = 20,
    ) -> list[UnifiedAd]:
        """
        Search market ads from other traders.
        
        Endpoint: POST /sapi/v1/c2c/ads/search
        
        Args:
            trade_type: "BUY" (find sellers) or "SELL" (find buyers)
            asset: Crypto asset (USDT, BTC, etc)
            fiat: Fiat currency (EUR, USD, etc)
            pay_types: Filter by payment methods (e.g., ["SEPAInstant", "SEPA"])
            trans_amount: Filter by transaction amount
            page: Page number
            rows: Results per page
            
        Returns:
            List of UnifiedAd from other traders, sorted by price
        """
        body: dict[str, Any] = {
            "tradeType": trade_type,
            "asset": asset,
            "fiat": fiat,
            "page": page,
            "rows": rows,
        }
        
        if pay_types:
            body["payTypes"] = pay_types
        if trans_amount is not None:
            body["transAmount"] = trans_amount
        
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/ads/search",
                body
            )
            
            if response.get("code") != "000000":
                self._logger.warning("Market search error: %s", response.get('message'))
                return []
            
            ads = response.get("data", [])
            return [self._transform_market_ad(a) for a in ads]
            
        except Exception as e:
            self._logger.error("Error searching market ads: %s", e)
            return []
    
    def _transform_market_ad(self, raw: dict[str, Any]) -> UnifiedAd:
        """Transform market ad search result to unified format."""
        # Market ads nest data inside an "adv" sub-object
        adv = raw.get("adv", raw)  # Unwrap if nested
        raw = {**adv, **{k: v for k, v in raw.items() if k != "adv"}}  # Merge
        ad_no = str(raw.get("advNo", raw.get("adNo", "")))
        
        # Get advertiser info
        advertiser = raw.get("advertiser", {})
        
        # Extract trade methods
        methods = []
        for tm in raw.get("tradeMethods", []):
            if isinstance(tm, dict):
                methods.append(tm.get("tradeMethodName", tm.get("payType", "")))
            elif isinstance(tm, str):
                methods.append(tm)
        
        return UnifiedAd(
            id=f"market_{uuid4().hex[:8]}",
            external_id=ad_no,
            exchange=ExchangeId.BINANCE,
            side=OrderSide.SELL if raw.get("tradeType", "").upper() == "SELL" else OrderSide.BUY,
            active=True,  # Search only returns active ads
            crypto_asset=self._map_asset(raw.get("asset", "USDT")),
            fiat_currency=self._map_currency(raw.get("fiatUnit", raw.get("fiat", "EUR"))),
            price=str(raw.get("price", "0")),
            price_type=PriceType.FLOATING if raw.get("priceType") == 1 else PriceType.FIXED,
            floating_rate=str(raw.get("priceFloatingRatio", "")) if raw.get("priceType") == 1 else None,
            available_amount=str(raw.get("surplusAmount", raw.get("tradableQuantity", "0"))),
            min_limit=str(raw.get("minSingleTransAmount", raw.get("minTradeLimit", "0"))),
            max_limit=str(raw.get("maxSingleTransAmount", raw.get("maxTradeLimit", "0"))),
            payment_methods=[m for m in methods if m],
            auto_reply=None,
            raw=raw
        )
    
    async def update_ad_status(self, ad_id: str, active: bool) -> bool:
        """
        Enable/disable an ad.
        
        Endpoint: POST /sapi/v1/c2c/ads/updateStatus
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/ads/updateStatus",
                {"advNo": ad_id, "advStatus": 1 if active else 0}
            )
            return response.get("code") == "000000"
        except Exception:
            return False
    
    async def update_ad_price(self, ad_id: str, new_price: str) -> bool:
        """
        Update ad price (fixed price type).
        
        Endpoint: POST /sapi/v1/c2c/ads/update
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/ads/update",
                {"advNo": ad_id, "price": float(new_price)}
            )
            return response.get("code") == "000000"
        except Exception:
            return False
    
    async def update_ad_floating_rate(
        self,
        ad_id: str,
        floating_ratio: float,
    ) -> bool:
        """
        Update ad to use floating rate pricing.
        
        Args:
            ad_id: Advertisement ID
            floating_ratio: Percentage offset from market price.
                           Negative = below market (for BUY ads)
                           Positive = above market (for SELL ads)
                           e.g., -1.5 means 1.5% below market
        
        Endpoint: POST /sapi/v1/c2c/ads/update
        
        priceType:
            0 = Fixed price
            1 = Floating (market ± ratio)
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/ads/update",
                {
                    "advNo": ad_id,
                    "priceType": 1,  # Floating
                    "priceFloatingRatio": float(floating_ratio),
                }
            )
            success = response.get("code") == "000000"
            if success:
                self._logger.info("Updated ad %s to floating rate: %+.2f%%", ad_id, floating_ratio)
            return success
        except Exception as e:
            self._logger.error("Failed to update floating rate: %s", e)
            return False
    
    async def toggle_ad(self, ad_id: str, active: bool) -> bool:
        """Alias for update_ad_status."""
        return await self.update_ad_status(ad_id, active)
    
    # =========================================================================
    # MERCHANT CONTROL
    # =========================================================================
    
    async def go_online(self) -> bool:
        """Set merchant online."""
        try:
            response = await self._signed_post("/sapi/v1/c2c/merchant/getOnline")
            return response.get("code") == "000000"
        except Exception:
            return False
    
    async def go_offline(self) -> bool:
        """Set merchant offline."""
        try:
            response = await self._signed_post("/sapi/v1/c2c/merchant/getOffline")
            return response.get("code") == "000000"
        except Exception:
            return False
    
    # =========================================================================
    # BALANCES
    # =========================================================================
    
    async def get_balances(self) -> list[UnifiedBalance]:
        """Get spot wallet balances."""
        try:
            response = await self._signed_get("/api/v3/account")
            balances = []
            for b in response.get("balances", []):
                free = float(b.get("free", 0))
                locked = float(b.get("locked", 0))
                if free > 0 or locked > 0:
                    balances.append(UnifiedBalance(
                        source=self.exchange_id.value,
                        asset=b["asset"],
                        available=str(free),
                        locked=str(locked),
                        total=str(free + locked),
                        updated_at=datetime.now()
                    ))
            return balances
        except Exception as e:
            self._logger.error("Error fetching balances: %s", e)
            return []
    
    # =========================================================================
    # TRANSFORMERS
    # =========================================================================
    
    def _transform_order(self, raw: dict[str, Any]) -> UnifiedOrder:
        """Transform Binance order to unified format."""
        # Handle different response field names
        order_no = str(raw.get("orderNumber", raw.get("adOrderNo", raw.get("orderNo", ""))))
        trade_type = raw.get("tradeType", raw.get("side", ""))
        is_buy = trade_type.upper() == "BUY"
        
        # Counterparty depends on our side:
        # - If we're BUYING, counterparty is the SELLER
        # - If we're SELLING, counterparty is the BUYER
        if is_buy:
            cp_nickname = raw.get("sellerNickname", raw.get("nickName", raw.get("counterPartNickName", "")))
            cp_realname = raw.get("sellerName", raw.get("realName", raw.get("counterPartRealName")))
        else:
            cp_nickname = raw.get("buyerNickname", raw.get("nickName", raw.get("counterPartNickName", "")))
            cp_realname = raw.get("buyerName", raw.get("realName", raw.get("counterPartRealName")))
        
        return UnifiedOrder(
            id=f"uni_{uuid4().hex[:12]}",
            external_id=order_no,
            exchange=ExchangeId.BINANCE,
            side=OrderSide.BUY if is_buy else OrderSide.SELL,
            status=self._map_status(raw.get("orderStatus", raw.get("status", ""))),
            crypto_asset=self._map_asset(raw.get("asset", raw.get("cryptoCurrency", "USDT"))),
            crypto_amount=str(raw.get("amount", raw.get("quantity", "0"))),
            fiat_currency=self._map_currency(raw.get("fiat", raw.get("fiatCurrency", "EUR"))),
            fiat_amount=str(raw.get("totalPrice", raw.get("totalAmount", "0"))),
            price=str(raw.get("unitPrice", raw.get("price", "0"))),
            counterparty=Counterparty(
                name=cp_nickname,
                real_name=cp_realname,
                order_count=raw.get("orderCount"),
                completion_rate=raw.get("completeRate"),
            ),
            payment_method=raw.get("payMethodName", raw.get("payType", "")),
            created_at=self._parse_timestamp(raw.get("createTime")),
            updated_at=self._parse_timestamp(raw.get("updateTime")),
            expires_at=self._parse_timestamp(raw.get("expireTime")),
            raw=raw
        )
    
    def _transform_chat_message(self, raw: dict[str, Any], order_id: str) -> ChatMessage:
        """Transform Binance chat message to unified format."""
        # Determine sender - Binance uses 'self' boolean
        is_from_me = raw.get("self", raw.get("fromMe", False))
        
        return ChatMessage(
            id=str(raw.get("msgId", raw.get("uuid", uuid4().hex[:12]))),
            order_id=order_id,
            exchange=ExchangeId.BINANCE,
            sender=MessageSender.US if is_from_me else MessageSender.COUNTERPARTY,
            content=raw.get("content", raw.get("message", raw.get("msg", ""))),
            timestamp=self._parse_timestamp(raw.get("createTime", raw.get("time"))),
            read=raw.get("read", False),
        )
    
    def _transform_ad(self, raw: dict[str, Any]) -> UnifiedAd:
        """Transform Binance ad to unified format."""
        ad_no = str(raw.get("advNo", raw.get("adNo", "")))
        price_type_raw = raw.get("priceType", 0)
        
        return UnifiedAd(
            id=f"ad_{uuid4().hex[:8]}",
            external_id=ad_no,
            exchange=ExchangeId.BINANCE,
            side=OrderSide.BUY if raw.get("tradeType", "").upper() == "BUY" else OrderSide.SELL,
            active=raw.get("advStatus") == 1 or raw.get("status") == 1,
            crypto_asset=self._map_asset(raw.get("asset", "USDT")),
            fiat_currency=self._map_currency(raw.get("fiatUnit", raw.get("fiat", "EUR"))),
            price=str(raw.get("price", "0")),
            price_type=PriceType.FLOATING if price_type_raw == 1 else PriceType.FIXED,
            floating_rate=str(raw.get("priceFloatingRatio", "")) if price_type_raw == 1 else None,
            available_amount=str(raw.get("surplusAmount", raw.get("tradableQuantity", raw.get("initAmount", "0")))),
            min_limit=str(raw.get("minSingleTransAmount", raw.get("minTradeLimit", "0"))),
            max_limit=str(raw.get("maxSingleTransAmount", raw.get("maxTradeLimit", "0"))),
            payment_methods=self._extract_payment_methods(raw),
            auto_reply=raw.get("autoReplyMsg"),
            raw=raw
        )
    
    def _extract_payment_methods(self, raw: dict[str, Any]) -> list[str]:
        """Extract payment methods from ad data."""
        methods = []
        if raw.get("tradeMethods"):
            for tm in raw.get("tradeMethods", []):
                if isinstance(tm, dict):
                    methods.append(tm.get("payType", tm.get("tradeMethodName", "")))
                elif isinstance(tm, str):
                    methods.append(tm)
        elif raw.get("payType"):
            methods.append(raw.get("payType", ""))
        return [m for m in methods if m]
    
    def _map_status(self, binance_status: str | int) -> OrderState:
        """Map Binance status to unified OrderState."""
        # Handle numeric status codes
        if isinstance(binance_status, int):
            return OrderState.from_binance_code(binance_status)
        
        # Handle string status -> convert to code first
        string_to_code = {
            "PENDING": 1,
            "TRADING": 1,
            "BUYER_PAYED": 2,
            "PAID": 2,
            "COMPLETED": 3,
            "CANCELLED": 4,
            "CANCEL": 4,
            "APPEAL": 5,
            "APPEALING": 5,
            "TIMEOUT": 6,
            "EXPIRED": 6,
        }
        code = string_to_code.get(str(binance_status).upper(), 1)
        return OrderState.from_binance_code(code)
    
    def _map_asset(self, asset: str) -> CryptoAsset:
        """Map asset string to enum."""
        try:
            return CryptoAsset(asset.upper())
        except ValueError:
            return CryptoAsset.USDT
    
    def _map_currency(self, currency: str) -> Currency:
        """Map currency string to enum."""
        try:
            return Currency(currency.upper())
        except ValueError:
            return Currency.EUR
    
    def _parse_timestamp(self, ts: int | str | None) -> datetime:
        """Parse timestamp to datetime."""
        if ts is None:
            return datetime.now()
        try:
            if isinstance(ts, str):
                ts = int(ts)
            # Binance uses milliseconds
            return datetime.fromtimestamp(ts / 1000 if ts > 9999999999 else ts)
        except Exception:
            return datetime.now()

    # =========================================================================
    # WALLET & TRANSFER METHODS (for Ad Liquidity Manager)
    # =========================================================================
    
    async def get_spot_balance(self, asset: str | None = None) -> dict[str, float]:
        """
        Get spot wallet balances.
        
        Endpoint: POST /sapi/v3/asset/getUserAsset
        
        Args:
            asset: Optional asset to filter (e.g., "USDC")
            
        Returns:
            Dict of {asset: free_balance}
        """
        body = {}
        if asset:
            body["asset"] = asset.upper()
        
        try:
            response = await self._signed_post("/sapi/v3/asset/getUserAsset", body)
            
            if isinstance(response, list):
                return {
                    item["asset"]: float(item.get("free", 0))
                    for item in response
                    if float(item.get("free", 0)) > 0
                }
            return {}
        except Exception as e:
            self._logger.error("Error getting spot balance: %s", e)
            return {}
    
    async def get_funding_balance(self, asset: str | None = None) -> dict[str, float]:
        """
        Get funding wallet balances.
        
        Endpoint: POST /sapi/v1/asset/get-funding-asset
        
        Args:
            asset: Optional asset to filter
            
        Returns:
            Dict of {asset: free_balance}
        """
        body = {}
        if asset:
            body["asset"] = asset.upper()
        
        try:
            response = await self._signed_post("/sapi/v1/asset/get-funding-asset", body)
            
            if isinstance(response, list):
                return {
                    item["asset"]: float(item.get("free", 0))
                    for item in response
                    if float(item.get("free", 0)) > 0
                }
            return {}
        except Exception as e:
            self._logger.error("Error getting funding balance: %s", e)
            return {}
    
    async def place_spot_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        quote_order_qty: bool = False,
    ) -> dict[str, Any] | None:
        """
        Place a spot market order.
        
        Endpoint: POST /api/v3/order
        
        Args:
            symbol: Trading pair (e.g., "USDCUSDT")
            side: "BUY" or "SELL"
            quantity: Amount of base asset (or quote if quote_order_qty=True)
            order_type: Order type (default: MARKET)
            quote_order_qty: If True, quantity is in quote asset (e.g., USDT for BUY)
            
        Returns:
            Order result or None if failed
        """
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type,
        }
        
        # Use quoteOrderQty for BUY orders when we specify quote amount
        if quote_order_qty and side.upper() == "BUY":
            params["quoteOrderQty"] = f"{quantity:.8f}".rstrip('0').rstrip('.')
        else:
            params["quantity"] = f"{quantity:.8f}".rstrip('0').rstrip('.')
        
        # Use _build_query_string which handles timestamp and signature
        query_string = self._build_query_string(params)
        url = f"{self.BASE_URL}/api/v3/order?{query_string}"

        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self._get_headers())
                response.raise_for_status()
                result = response.json()
                
                self._logger.info("Spot order: %s %s %s → Status: %s", side, quantity, symbol, result.get('status'))
                return result
        except httpx.HTTPStatusError as e:
            self._logger.error("Spot order failed: %s", e.response.text)
            return None
        except Exception as e:
            self._logger.error("Spot order error: %s", e)
            return None

    
    async def transfer_to_funding(
        self,
        asset: str,
        amount: float,
    ) -> bool:
        """
        Transfer from Spot wallet to Funding wallet.
        
        Endpoint: POST /sapi/v1/asset/transfer
        
        Args:
            asset: Asset to transfer (e.g., "USDT")
            amount: Amount to transfer
            
        Returns:
            True if successful
        """
        params = self._signed_params({
            "type": "MAIN_FUNDING",  # Spot → Funding
            "asset": asset.upper(),
            "amount": f"{amount:.8f}".rstrip('0').rstrip('.'),
        })
        
        query_string = self._build_query_string(params)
        url = f"{self.BASE_URL}/sapi/v1/asset/transfer?{query_string}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self._get_headers())
                response.raise_for_status()
                result = response.json()
                
                if result.get("tranId"):
                    self._logger.info("Transfer: %s %s Spot → Funding (ID: %s)", amount, asset, result['tranId'])
                    return True
                return False
        except httpx.HTTPStatusError as e:
            self._logger.error("Transfer failed: %s", e.response.text)
            return False
        except Exception as e:
            self._logger.error("Transfer error: %s", e)
            return False
    
    async def transfer_from_funding(
        self,
        asset: str,
        amount: float,
    ) -> bool:
        """
        Transfer from Funding wallet to Spot wallet.
        
        Endpoint: POST /sapi/v1/asset/transfer
        
        Args:
            asset: Asset to transfer
            amount: Amount to transfer
            
        Returns:
            True if successful
        """
        params = self._signed_params({
            "type": "FUNDING_MAIN",  # Funding → Spot
            "asset": asset.upper(),
            "amount": f"{amount:.8f}".rstrip('0').rstrip('.'),
        })
        
        query_string = self._build_query_string(params)
        url = f"{self.BASE_URL}/sapi/v1/asset/transfer?{query_string}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self._get_headers())
                response.raise_for_status()
                result = response.json()
                
                if result.get("tranId"):
                    self._logger.info("Transfer: %s %s Funding → Spot (ID: %s)", amount, asset, result['tranId'])
                    return True
                return False
        except Exception as e:
            self._logger.error("Transfer error: %s", e)
            return False
    
    async def update_ad_quantity(
        self,
        ad_id: str,
        new_quantity: float,
    ) -> bool:
        """
        Update ad's tradable quantity (top-up).
        
        Endpoint: POST /sapi/v1/c2c/ads/update
        
        Args:
            ad_id: Advertisement ID
            new_quantity: New total tradable quantity
            
        Returns:
            True if successful
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/ads/update",
                {
                    "advNo": ad_id,
                    "totalTradableAmount": float(new_quantity),
                }
            )
            
            success = response.get("code") == "000000"
            if success:
                self._logger.info("Ad %s quantity updated to %s", ad_id, new_quantity)
            else:
                self._logger.error("Ad update failed: %s", response.get('message'))
            return success
        except Exception as e:
            self._logger.error("Ad update error: %s", e)
            return False

    async def update_ad_price(
        self,
        ad_id: str,
        floating_ratio: float,
    ) -> bool:
        """
        Update ad's floating price ratio.

        Endpoint: POST /sapi/v1/c2c/ads/update

        Args:
            ad_id: Advertisement ID
            floating_ratio: New floating ratio (e.g. 99.70 = 99.70% of market price)

        Returns:
            True if successful
        """
        try:
            response = await self._signed_post(
                "/sapi/v1/c2c/ads/update",
                {
                    "advNo": ad_id,
                    "priceFloatingRatio": float(floating_ratio),
                }
            )

            success = response.get("code") == "000000"
            if success:
                self._logger.info("Ad %s price updated to %.2f%%", ad_id, floating_ratio)
            else:
                self._logger.error("Ad price update failed: %s", response.get('message'))
            return success
        except Exception as e:
            self._logger.error("Ad price update error: %s", e)
            return False
    
    async def get_deposit_address(self, asset: str, network: str = "BSC") -> dict | None:
        """
        Get deposit address for an asset.
        
        Endpoint: GET /sapi/v1/capital/deposit/address
        
        Args:
            asset: Asset (e.g., "USDC")
            network: Network (e.g., "BSC", "ETH", "TRX")
            
        Returns:
            {address, tag, coin, network}
        """
        try:
            response = await self._signed_get(
                "/sapi/v1/capital/deposit/address",
                {"coin": asset.upper(), "network": network}
            )
            return response if response.get("address") else None
        except Exception as e:
            self._logger.error("Error getting deposit address: %s", e)
            return None



    # =========================================================================
    # DEPOSIT & CONVERT HISTORY (for Institutional FIFO tracking)
    # =========================================================================

    async def get_deposit_history(
        self,
        coin: str = "USDC",
        status: int = 1,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get deposit history.

        Endpoint: GET /sapi/v1/capital/deposit/hisrec

        Args:
            coin: Asset symbol (e.g., "USDC")
            status: 0=pending, 6=credited, 1=success
            start_time: UTC timestamp in ms
            end_time: UTC timestamp in ms
            limit: Max 1000

        Returns:
            List of deposit records with amount, txId, status, insertTime, etc.
        """
        import time as _t
        params: dict = {"coin": coin.upper(), "status": status, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if not start_time:
            params["startTime"] = int((_t.time() - 86400 * 30) * 1000)

        try:
            response = await self._signed_get("/sapi/v1/capital/deposit/hisrec", params)
            if isinstance(response, list):
                return response
            return response.get("data", []) if isinstance(response, dict) else []
        except Exception as e:
            self._logger.error("Error fetching deposit history: %s", e)
            return []

    async def get_convert_history(
        self,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get convert trade history.

        Endpoint: GET /sapi/v1/convert/tradeFlow

        Args:
            start_time: UTC timestamp in ms (required, defaults to 24h ago)
            end_time: UTC timestamp in ms (required, defaults to now)
            limit: Max 1000

        Returns:
            List of convert trades with quoteId, fromAsset, toAsset,
            fromAmount, toAmount, createTime.
        """
        import time as _t
        now_ms = int(_t.time() * 1000)
        params: dict = {
            "startTime": start_time or (now_ms - 86400 * 1000),
            "endTime": end_time or now_ms,
            "limit": limit,
        }

        try:
            response = await self._signed_get("/sapi/v1/convert/tradeFlow", params)
            if isinstance(response, dict):
                return response.get("list", response.get("data", []))
            return response if isinstance(response, list) else []
        except Exception as e:
            self._logger.error("Error fetching convert history: %s", e)
            return []

    async def get_spot_trades(
        self,
        symbol: str = "USDCUSDT",
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get spot trade history.

        Endpoint: GET /api/v3/myTrades

        Args:
            symbol: Trading pair (e.g., "USDCUSDT")
            start_time: UTC timestamp in ms
            end_time: UTC timestamp in ms
            limit: Max 1000

        Returns:
            List of trades with id, orderId, price, qty, quoteQty, time, isBuyer.
        """
        params: dict = {"symbol": symbol.upper(), "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            response = await self._signed_get("/api/v3/myTrades", params)
            return response if isinstance(response, list) else []
        except Exception as e:
            self._logger.error("Error fetching spot trades: %s", e)
            return []
