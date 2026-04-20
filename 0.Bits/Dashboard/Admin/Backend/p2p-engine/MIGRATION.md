# Migration Guide: PearV1 → PearV2

## Overview

PearV2 is a hardened version of PearV1 that adds:
- The COP (Colombian Peso) trading path
- Comprehensive security fixes from 5 rounds of adversarial audit
- Structured logging, centralized config, and test coverage

## Breaking Changes

### 1. `API_SECRET_KEY` is now REQUIRED
PearV2 will **refuse to start** without `API_SECRET_KEY` set.

```bash
# Generate a key:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env:
API_SECRET_KEY=your-generated-key
```

### 2. CORS is restricted
V1 allowed all origins (`*`). V2 restricts to `CORS_ORIGINS` env var.

```bash
# .env
CORS_ORIGINS=http://localhost:3000,https://your-dashboard.com
```

### 3. `force=True` no longer bypasses terminal states
In V1, `state_manager.transition(order_id, state, force=True)` could transition orders out of COMPLETED/CANCELLED. This is now blocked (S1 fix).

### 4. New database columns
The `orders` table has a new `payout_sent_at` column. This is added automatically via migration — no manual SQL needed.

## New Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BINANCE_2FA_SECRET` | COP path | TOTP secret for crypto release |
| `FACILITAPAY_USERNAME` | COP path | FacilitaPay account |
| `FACILITAPAY_PASSWORD` | COP path | FacilitaPay password |
| `FACILITAPAY_CASH_IN_ACCOUNT_ID` | COP path | Bank account ID |
| `FACILITAPAY_WEBHOOK_SECRET` | COP path | Webhook signing secret |
| `GEMINI_API_KEY` | COP path | For AI chat extraction |
| `COP_POLL_INTERVAL` | Optional | COP polling interval (default: 30s) |
| `COP_DB_PATH` | Optional | COP database path |
| `FP_DB_PATH` | Optional | FacilitaPay DB path |
| `LOG_LEVEL` | Optional | Logging level (default: INFO) |
| `AUTO_SEND_COP_LINK` | Optional | Auto-send PSE links (default: false) |

## Migration Steps

```bash
# 1. Backup V1 database
cp data/orders.db data/orders_v1_backup.db

# 2. Install V2 dependencies
pip install -e ".[dev]"

# 3. Update .env (see .env.example)
cp .env.example .env
# Fill in all required values

# 4. Start V2 — migrations run automatically
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# 5. Verify
pytest tests/ -v
```

## Rollback Plan

If issues are found after deploying V2:

```bash
# 1. Stop V2
# 2. Restore V1 database
cp data/orders_v1_backup.db data/orders.db
# 3. Switch back to V1 code
# 4. Restart
```

The `payout_sent_at` column is backwards-compatible — V1 will ignore it.
