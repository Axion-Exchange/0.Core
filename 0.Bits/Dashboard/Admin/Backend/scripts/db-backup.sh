#!/bin/bash
set -euo pipefail

BACKUP_DIR="/data/backups/postgres"
GCS_BUCKET="axion-0core-backups"
TOKEN_SCRIPT="/data/gcp/get-token.sh"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

DB_URL=$(grep DATABASE_URL /data/0.Core/0.Bits/Dashboard/Admin/Backend/.env | head -1 | cut -d= -f2-)
mkdir -p "$BACKUP_DIR"

log() { echo "[$(date -Iseconds)] $1"; }

BACKUP_FILE="$BACKUP_DIR/zerobits_${TIMESTAMP}.sql.gz"
log "Starting backup: $BACKUP_FILE"

pg_dump "$DB_URL" --format=custom --compress=9 --file="$BACKUP_FILE"
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup completed: $SIZE"

if pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
  log "Integrity check: PASSED"
else
  log "WARNING: Integrity check FAILED"
fi

# Upload to GCS
if [ -x "$TOKEN_SCRIPT" ]; then
  log "Uploading to GCS..."
  ACCESS_TOKEN=$("$TOKEN_SCRIPT")
  if [ -n "$ACCESS_TOKEN" ]; then
    RESULT=$(curl -s -X POST \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/octet-stream" \
      "https://storage.googleapis.com/upload/storage/v1/b/$GCS_BUCKET/o?uploadType=media&name=postgres/zerobits_${TIMESTAMP}.sql.gz" \
      --data-binary @"$BACKUP_FILE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get(\"name\",\"FAILED\"))")
    log "GCS upload: $RESULT"
  else
    log "WARNING: No GCS token"
  fi
fi

# Cleanup old local backups
find "$BACKUP_DIR" -name "zerobits_*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

TOTAL=$(find "$BACKUP_DIR" -name "zerobits_*.sql.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Backup inventory: $TOTAL files, $TOTAL_SIZE total"
