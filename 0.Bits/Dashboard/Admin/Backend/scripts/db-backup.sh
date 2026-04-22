#!/bin/bash
# ── Automated PostgreSQL Backup ──────────────────────────────
# 
# Institutional-grade database backup with retention policy.
# Schedule via cron: 0 */6 * * * /data/0.Core/0.Bits/Dashboard/Admin/Backend/scripts/db-backup.sh
#
# Features:
# - Compressed pg_dump with timestamps
# - 30-day retention (auto-cleanup)
# - Integrity verification via pg_restore --list
# - Structured logging

set -euo pipefail

BACKUP_DIR="/data/backups/postgres"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/data/backups/backup.log"

# Source DB URL from .env
DB_URL=$(grep DATABASE_URL /data/0.Core/0.Bits/Dashboard/Admin/Backend/.env | head -1 | cut -d= -f2-)

# Create directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
  echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

BACKUP_FILE="$BACKUP_DIR/zerobits_${TIMESTAMP}.sql.gz"

log "Starting backup: $BACKUP_FILE"

# Run backup
if pg_dump "$DB_URL" --format=custom --compress=9 --file="$BACKUP_FILE" 2>>"$LOG_FILE"; then
  SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  log "Backup completed: $SIZE"
  
  # Verify backup integrity
  if pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
    log "Integrity check: PASSED"
  else
    log "WARNING: Integrity check FAILED for $BACKUP_FILE"
  fi
else
  log "ERROR: Backup FAILED"
  exit 1
fi

# Cleanup old backups
DELETED=$(find "$BACKUP_DIR" -name "zerobits_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
  log "Cleaned up $DELETED backups older than $RETENTION_DAYS days"
fi

# Summary
TOTAL=$(find "$BACKUP_DIR" -name "zerobits_*.sql.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Backup inventory: $TOTAL files, $TOTAL_SIZE total"
