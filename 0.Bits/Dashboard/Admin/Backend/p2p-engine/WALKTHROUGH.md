# PearV2 Walkthrough

## COP Sell Order Flow

This is the complete lifecycle of a Colombian Peso (COP) sell order:

### 1. Order Discovery
```
Binance P2P → polling loop → COPChatHandler._poll_binance_orders()
```
- Handler polls Binance P2P API every 30 seconds
- New orders are tracked by `COPOrderTracker`
- State: **NEW** → **AWAITING_INFO**
- Welcome message sent via `BinanceChatClient`

### 2. Customer Information Extraction
```
Buyer sends: "Juan Perez 1234567890 Bancolombia juan@email.com"
→ COPInfoExtractor.extract_from_messages()
→ Gemini AI parses name, CC, bank, email
→ Regex fallback if AI fails
```
- CC validated (7-10 digits, Colombian format)
- Bank matched against known bank codes
- State: **AWAITING_INFO** → **INFO_RECEIVED**

### 3. PSE Link Generation
```
COPInfoExtractor → FacilitaPay Subject → PSE Payment Link
```
- FacilitaPay subject created/retrieved for the customer
- PSE payment link generated with exact COP amount
- Link sent to buyer via Binance chat
- State: **INFO_RECEIVED** → **LINK_SENT** → **AWAITING_PAYMENT**

### 4. Payment Verification (Webhook)
```
FacilitaPay → POST /webhooks/facilitapay → COPChatHandler.handle_webhook()
```
Safety checks applied in order:
1. **M1 Lock**: Per-order `asyncio.Lock` acquired
2. **Idempotency**: Skip if already COMPLETED/RELEASING
3. **State guard**: Only release from LINK_SENT, AWAITING_PAYMENT, PAYMENT_RECEIVED
4. **Amount verification**: EXACT match required (no tolerance)
5. State: **AWAITING_PAYMENT** → **PAYMENT_RECEIVED**

### 5. Crypto Release
```
PAYMENT_RECEIVED → RELEASING → release_crypto() → COMPLETED
```
- **Durable write pattern**: RELEASING state persisted BEFORE calling Binance API
- If crash occurs after release but before COMPLETED, reconciliation sweep detects and recovers (M2)
- State: **RELEASING** → **COMPLETED**

---

## EUR Buy Order Flow

### 1. Order Discovery
```
Binance P2P → OrderOrchestrator._poll_exchange()
```
- Orchestrator polls Binance for BUY orders
- Seller payment details (IBAN, name) fetched
- IBAN screened against sanctions

### 2. Payout Execution
```
OrderOrchestrator.execute_buy_payout()
```
Safety checks:
1. Per-order lock acquired
2. **S2**: `payout_sent_at` checked — skip if already sent
3. **A5**: Re-verify order is still active on Binance
4. Generate deterministic `replay_id` for Januar idempotency
5. Send EUR via Januar SEPA
6. Mark order as paid on Binance
7. State: → **MARKED_AS_PAID**

### 3. Seller Release
- Orchestrator monitors for seller crypto release
- 30-minute timeout → DELAYED state
- When seller releases, exchange poll detects COMPLETED

---

## Reconciliation Sweep

Runs every 60 seconds to recover from edge cases:

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| Missed webhook | Expired PSE link + no payment | Re-check FacilitaPay for payment |
| Stuck PAYMENT_RECEIVED | In state > 5 minutes | Retry `release_crypto()` |
| Stuck RELEASING (M2) | In state > 2 minutes | Check Binance for actual release status |
| Expired PSE link | `link_expires_at` passed | Generate new link or manual review |
