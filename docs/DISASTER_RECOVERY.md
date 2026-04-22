# Disaster Recovery Runbook — 0core Infrastructure

> **Classification:** Internal — Operations Team Only
> **Last Updated:** 2026-04-22
> **Owner:** Platform Engineering

---

## Recovery Objectives

| Metric | Target | Current | Gap |
|---|---|---|---|
| **RTO** (Recovery Time Objective) | < 30 minutes | ~15 minutes | ✅ Met |
| **RPO** (Recovery Point Objective) | < 6 hours | 6 hours (backup cron) | ✅ Met |
| **Uptime SLA** | 99.9% (8.7h downtime/year) | ~99.5% | ⚠️ Close |

---

## Tier Classification

### Tier 1 — Critical (RTO < 15min)
- **0core API Server** — All dashboard operations depend on this
- **PostgreSQL Database** — Financial ledger, user data, orders
- **Redis** — Session state, rate limiting, BullMQ job queue

### Tier 2 — Important (RTO < 1hr)
- **BullMQ Workers** — P2P orchestration, Binance sync, fiat sync
- **WebSocket Bridge** — Real-time dashboard updates

### Tier 3 — Deferrable (RTO < 4hr)
- **Health Monitor** — Observability (not revenue-critical)
- **KYC Sync Worker** — Can be manually triggered

---

## Failure Scenarios and Response Procedures

### 1. API Server Crash
**Symptoms:** 0bit.app shows loading spinners, health endpoint unreachable
**Automated Recovery:** PM2 auto-restarts (current: 175+ restarts observed)
**Manual Recovery:**
```bash
ssh ubuntu@54.95.24.22
pm2 restart 5 --update-env
pm2 logs 5 --lines 20
```
**RTO:** < 30 seconds (PM2 auto-restart)

### 2. Database Failure
**Symptoms:** API returns 500, "Database unreachable" in health checks
**Recovery:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
sudo systemctl restart postgresql

# If data corruption, restore from backup
/data/0.Core/0.Bits/Dashboard/Admin/Backend/scripts/db-backup.sh  # First, backup current state
pg_restore --clean --dbname=zerobits /data/backups/postgres/zerobits_LATEST.sql.gz
```
**RTO:** 5-15 minutes | **RPO:** Last backup (6hr intervals)

### 3. Redis Failure
**Symptoms:** Rate limiting fails, BullMQ jobs stall, sessions lost
**Recovery:**
```bash
sudo systemctl restart redis-server
# All connected clients will reconnect automatically
# BullMQ jobs survive Redis restart (AOF persistence)
```
**RTO:** < 1 minute

### 4. Full VPS Failure
**Symptoms:** All services unreachable, SSH timeout
**Recovery:**
1. Contact AWS support or launch replacement EC2 instance
2. Restore PostgreSQL from latest backup in `/data/backups/postgres/`
3. `git clone` both `0.Core` and `0.Bits` repos
4. `npm ci && npx prisma generate && npm run build`
5. `pm2 start ecosystem.config.js`
**RTO:** 30-60 minutes | **RPO:** Last backup

### 5. Binance API Rate Limit Ban
**Symptoms:** Orders not syncing, health check shows "binance_api: down"
**Recovery:**
```bash
# Check ban status
pm2 logs 6 --lines 50 | grep -i "ban\|429\|rate"
# Reduce polling interval temporarily
# Wait 24hr for ban to lift (automatic)
```
**RTO:** Self-healing (24hr)

---

## Backup Strategy

| Component | Method | Frequency | Retention |
|---|---|---|---|
| PostgreSQL | `pg_dump` compressed | Every 6 hours | 30 days |
| Redis (AOF) | Append-only file | Continuous | Until restart |
| Application Code | Git (GitHub) | Every commit | Permanent |
| Configuration | `.env` in VPS | Manual backup | As needed |

### Backup Verification
```bash
# Run integrity check on latest backup
LATEST=$(ls -t /data/backups/postgres/zerobits_*.sql.gz | head -1)
pg_restore --list "$LATEST" > /dev/null && echo "PASS" || echo "FAIL"
```

---

## Escalation Matrix

| Severity | Response Time | Action |
|---|---|---|
| P1 (Service Down) | < 15 min | Restart services, restore from backup |
| P2 (Degraded) | < 1 hour | Investigate logs, apply hotfix |
| P3 (Warning) | < 4 hours | Review health checks, plan remediation |
| P4 (Informational) | Next business day | Update documentation, add tests |

---

## Post-Incident Checklist
- [ ] Root cause identified
- [ ] Timeline documented
- [ ] Health checks verify recovery
- [ ] Backup integrity confirmed
- [ ] Monitoring alert validated
- [ ] Runbook updated if needed
