# Changelog

## [2026-03-21] BUY Flow Hardening & SEPA Compliance

### New Features
- **Chat IBAN Fallback**: When seller's profile has no IBAN, bot polls chat
  every 30s until order expires. Auto-sends "please send IBAN" message
  (max 2 times, 5-minute anti-spam gap).
- **Smart Name Sanitization**: `extract_clean_latin_parts()` strips non-Latin
  words from names before retrying Januar, avoiding unnecessary chat fallback.
  Handles Cyrillic transliteration, accent stripping, and Arabic/emoji removal.
- **SEPA-Only Whitelist**: Only SEPA-zone IBANs accepted. Non-SEPA IBANs
  (AE, IL, TR, etc.) blocked with chat notification to seller.
- **Debug Profile Logging**: Every BUY order saves full JSON snapshot
  (counterparty, payment info, IBAN, outcome) to `data/debug_profiles/`.
- **Persistent Trustpilot Dedup**: `trustpilot_sent_at` column in orders DB
  prevents duplicate thank-you messages across restarts.

### Bug Fixes
- **Chat Fallback Payout Retry**: Removed broken `try_claim_eur_payout` re-claim.
  Retry now uses new `replay_id` directly for Januar idempotency.
- **Ad Rebalancer Init**: Fixed `AttributeError` — `self.topup_enabled` now
  initialized from `SELL_AD_TOPUP_ENABLED` env var.
- **IBAN Blocklist Cleanup**: Removed Albania (AL) from high-risk list. Cleared
  all SEPA countries from blocklist. Only BY, RU, SD, SY, UA remain blocked.

### Tests
- Added `tests/test_chat_fallback_retry.py` (3 test cases covering successful
  retry, no-name-found failure, and double-failure scenarios).
- `extract_clean_latin_parts()` verified with 10 test cases (Latin, Cyrillic,
  Arabic, accented, mixed names).

### Files Changed
- `src/services/order_orchestrator.py` — IBAN chat fallback, name cleanup,
  debug dumps, Trustpilot DB dedup, chat-fallback retry fix, non-SEPA chat msg
- `src/services/iban_screener.py` — SEPA whitelist, blocklist cleanup
- `src/services/name_sanitizer.py` — `extract_clean_latin_parts()`
- `src/core/persistence.py` — `trustpilot_sent_at` migration + DB methods
- `src/services/ad_rebalancer.py` — `topup_enabled` init fix
- `tests/test_chat_fallback_retry.py` — NEW test file


# Changelog — PearV2

## v2.0.0 (2026-02-11)

### COP Module Decomposition (P2-01)
- **Extracted** `cop_standalone.py` (1,805 lines) into 5 clean modules:
  - `cop_types.py` — Enums (`COPOrderState`), dataclasses (`COPOrder`), message templates
  - `binance_chat.py` — `BinanceChatClient` with structured logging
  - `info_extractor.py` — `COPInfoExtractor` using Gemini AI + regex fallback
  - `cop_tracker.py` — `COPOrderTracker` SQLite state machine with `VALID_TRANSITIONS`
  - `cop_handler.py` — `COPChatHandler` orchestrator with all safety fixes

### Security Fixes (P0)
- **V4-01**: Router-level `Depends(verify_api_key)` on all `/api` routes
- **V4-02**: CORS restricted from `["*"]` to `CORS_ORIGINS` env var
- **V4-03**: Payout idempotency via `payout_sent_at` guard + Januar `replay_id`
- **V4-04**: COP `VALID_TRANSITIONS` dict preventing invalid state changes
- **M1**: Per-order `asyncio.Lock` preventing COP race conditions
- **M2**: RELEASING state recovery via reconciliation sweep
- **M3**: `RuntimeError` if `API_SECRET_KEY` not set at startup

### Security Fixes (P1)
- **S1**: `force=True` now blocked on terminal states (COMPLETED, CANCELLED, EXPIRED, REFUNDED)
- **S2**: `payout_sent_at` column added to orders table

### Infrastructure
- **N1**: Structured `logging` module replacing all `print()` calls
- **S5**: Centralized `config.py` with validation and disk space check
- **P2-02**: Comprehensive `.gitignore`
- **P2-03**: Documented `.env.example` with all required/optional vars
- **P2-04**: Updated `pyproject.toml` (renamed to pear-v2 v2.0.0, added pyotp, websockets, slowapi)

### Tests
- `test_state_transitions.py` — Exhaustive COP transition matrix + EUR S1 guard
- `test_idempotency.py` — Double webhook/payout prevention
- `test_safety_invariants.py` — Terminal finality, release path constraints, audit log
- `test_cop_tracker.py` — COP order CRUD, transitions, audit log
- `test_cop_handler.py` — Webhook safety guards, amount verification, link expiry
