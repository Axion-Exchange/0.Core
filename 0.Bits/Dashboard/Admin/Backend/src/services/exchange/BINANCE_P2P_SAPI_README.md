# Binance P2P SAPI (v7.4) - Master Reference

This document outlines the complete mapping of the Binance P2P SAPI v7.4 endpoints implemented in the `BinanceP2PConnector` class. It serves as an institutional reference for future technical expansion, multi-account scaling, and automated conversational flows.

## Core Architectural Changes

### 1. The `listWithPagination` Resolution
Previously, the backend attempted to fetch merchant advertisements using an undocumented or hallucinated endpoint (`GET /sapi/v1/c2c/ads/getAdList`). This resulted in persistent 404 Not Found errors, causing the background worker to silently skip advertisement syncing.

**The Fix:**
The official endpoint for fetching a merchant's own advertisement list is `POST /sapi/v1/c2c/ads/listWithPagination`. This endpoint is fully mapped in the `BinanceP2PConnector` via `listAdsWithPagination` and integrated into the `BinanceService.fetchMerchantAds()` pipeline.

### 2. Comprehensive SAPI Surface
The `BinanceP2PConnector` now supports the entirety of the Binance P2P SAPI v7.4. All endpoints utilize the authenticated HMAC SHA256 CCXT `request()` wrapper to ensure consistent IP proxying, signature generation, and payload integrity.

---

## Endpoint Index

### Ads Controller
- `GET c2c/ads/getAvailableAdsCategory`: `getAvailableAdsCategory`
- `POST c2c/ads/getDetailByNo`: `getAdDetailByNo`
- `POST c2c/ads/getReferencePrice`: `getReferencePrice`
- `POST c2c/ads/listWithPagination`: `listAdsWithPagination`
- `POST c2c/ads/post`: `postAd`
- `POST c2c/ads/search`: `searchAds`
- `POST c2c/ads/update`: `updateAd`
- `POST c2c/ads/updateStatus`: `updateAdStatus`

### Merchant Controller
- `POST c2c/merchant/closeBusiness`: `closeBusiness`
- `POST c2c/merchant/endRest`: `endRest`
- `GET c2c/merchant/getAdDetails`: `getMerchantAdDetail`
- `POST c2c/merchant/getOffline`: `getOffline`
- `POST c2c/merchant/getOnline`: `getOnline`
- `POST c2c/merchant/startBusiness`: `startBusiness`
- `POST c2c/merchant/startRest`: `startRest`

### Order Match Controller
- `POST c2c/orderMatch/cancelOrder`: `cancelOrder`
- `POST c2c/orderMatch/checkIfAllowedCancelOrder`: `checkIfAllowedCancelOrder`
- `POST c2c/orderMatch/checkIfCanPlaceOrder`: `checkIfCanPlaceOrder`
- `POST c2c/orderMatch/checkIfCanReleaseCoin`: `checkIfCanReleaseCoin`
- `POST c2c/orderMatch/getUserOrderDetail`: `getUserOrderDetail`
- `GET c2c/orderMatch/getUserOrderSummary`: `getUserOrderSummary`
- `POST c2c/orderMatch/listOrders`: `listOrders`
- `GET c2c/orderMatch/listUserOrderHistory`: `getTradeHistory`
- `POST c2c/orderMatch/markOrderAsPaid`: `markOrderAsPaid`
- `POST c2c/orderMatch/placeOrder`: `placeOrder`
- `POST c2c/orderMatch/queryCounterPartyOrderStatistic`: `queryCounterPartyOrderStatistic`
- `POST c2c/orderMatch/releaseCoin`: `releaseDigitalAsset`

### KYC & Payment Controllers
- `POST c2c/orderMatch/verifiedAdditionalKyc`: `verifiedAdditionalKyc`
- `GET c2c/paymentMethod/getById`: `getPaymentMethodById`
- `GET c2c/paymentMethod/getByUserId`: `getPaymentMethodByUserId`
- `GET c2c/paymentMethod/list`: `listAllOfValidPaymentMethods`

### User & Currency Controllers
- `GET c2c/user/getUserDetail`: `getUserDetail`
- `GET c2c/user/getRiskWarningTips`: `getRiskWarningTips`
- `POST c2c/digitalCurrency/list`: `queryDigitalCurrencyList`
- `POST c2c/fiatCurrency/list`: `queryFiatCurrencyList`

### Chat Controller
- `GET c2c/chat/getChatImagePresignedUrl`: `getChatImagePresignedUrl`
- `POST c2c/chat/markMessagesAsReadByUserAndOrder`: `markMessagesAsReadByUserAndOrder`
- `POST c2c/chat/markMessagesAsReadByUser`: `markMessagesAsReadByUser`
- `GET c2c/chat/retrieveChatWSS`: `retrieveChatWSS`
- `GET c2c/chat/retrieveChatMessagesWithPagination`: `retrieveChatMessages`
- `POST c2c/chat/sendMsg`: `sendChatMessage`

### Commission Controller
- `GET c2c/commission/overview`: `getCommissionOverview`
- `GET c2c/commission/takerRate`: `getTakerCommissionRate`

---

## Technical Notes

> [!WARNING]
> **API Key Permissions**: Ensure that the provided Binance API keys have "Enable P2P" checked in the API Management console. Without this, even valid signatures will result in HTTP 403 or 401 Unauthorized errors for SAPI endpoints.

> [!IMPORTANT]
> **SAPI Weight Limits**: Binance tightly throttles SAPI requests. The `BinanceSyncWorker` utilizes a 5-tick modulo mechanism (~2.5 minutes) to ensure `listAdsWithPagination` does not exceed API quotas, especially when scaling horizontally across multi-account deployments.

> [!TIP]
> **Math Algebra in `updateMerchantAdSurplus`**: Binance's surplus ad update mechanism relies on algebraic derivation (`initAmountAfter = initAmountBefore - surplusAmountBefore + newSurplusAmount`). Do not modify the math inside this method unless the Binance SAPI specification inherently changes.
