# PearV2 — Automated P2P Trading Bot

> Multi-exchange P2P trading bot with automated SEPA/COP payments, FIFO P&L tracking, and Telegram monitoring.

## Architecture

```
PearV2/
├── main.py                    Entry point — orchestrates all async tasks
├── src/
│   ├── core/                  Infrastructure: state machine, types, config, persistence
│   ├── exchanges/             Exchange adapters: Binance, OKX, Bitget, Bybit, KuCoin, HTX, MEXC
│   ├── fiat/                  Payment processors: EUR (Januar SEPA), COP (FacilitaPay), BRL, MXN
│   ├── services/              Business logic + monitoring
│   │   ├── order_orchestrator.py    Main brain — order lifecycle management
│   │   ├── pnl_tracker.py          FIFO P&L engine with Binance sync
│   │   ├── telegram_notifier.py    Telegram bot commands + reports
│   │   ├── stuck_monitor.py        Operational alerts with diagnostics
│   │   ├── order_analytics.py      Completion rates + missed volume
│   │   ├── ad_rebalancer.py        Dynamic ad pricing + surplus alerts
│   │   ├── kyc_screener.py         Counterparty risk scoring
│   │   ├── iban_screener.py        IBAN/SEPA validation
│   │   └── name_sanitizer.py       SEPA name sanitization
│   ├── logic/                 Matching: payment, name, amount, reference
│   └── kyc/                   KYC verification (DidIt API)
└── data/
    ├── orders.db              Active orders (state machine)
    └── pnl.db                 Completed trades + analytics
```

## Telegram Bot Commands

### P&L Reports
- `/pnl` — Today's realized P&L (FIFO, EUR-only matched spreads)
- `/pnl_yesterday`, `/pnl_week`, `/pnl_month`, `/pnl_year`, `/pnl_all`

### Analytics
- `/stats [today|week|month|year|all]` — Completion rates + missed volume
- `/heatmap [today|week|month|year|all]` — Opened vs completed volume by hour
- `/spread` — Spread analysis with best/worst hours + tips

### Operations
- `/inventory` — Current USDT holdings with avg cost
- `/status` — Active orders
- `/help` — Full command list

## Alert System

**Stuck Order Monitor** scans every 30s:
- 1st alert at **1 min**, escalation at **5 min**, max 2 alerts per order
- **Auto-resolve**: replies "✅ Resolved" + deletes messages when order completes
- **Diagnostic checklist** for sell orders:
  - Script detection (Arabic, Cyrillic, CJK → can't match SEPA sender)
  - Payment match status
  - Third-party/KYC flags

**Sell Ad Monitor**: alerts when surplus drops below $200 USDT.

## Scheduled Reports

| Report | Schedule | Survives daily cleanup? |
|--------|----------|------------------------|
| Daily P&L | 23:59 UTC | ✅ Yes |
| Weekly P&L | Sunday 23:59 UTC | ✅ Yes |
| Daily Status | Midnight UTC | No (refreshed) |

## FIFO P&L Engine

- **Matched-spreads only**: profit counted only when BOTH buy AND sell fall within the period
- **EUR-only filtering**: no cross-currency inflation
- **5-minute Binance sync cache**
- **Inventory tracking**: remaining units with weighted avg cost

## Environment Variables

```env
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
JANUAR_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
SELL_AD_ALERT_THRESHOLD=200    # optional, USDT
AD_REBALANCE_INTERVAL=300      # optional, seconds
```

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Start
python main.py

# Or with PM2
pm2 start main.py --name pearv2 --interpreter python3
```
