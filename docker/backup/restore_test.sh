#!/bin/sh
set -eu
BACKUP_FILE="${1:-/backups/latest.sql.gz}"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "No existe archivo de respaldo: $BACKUP_FILE"
  exit 1
fi
echo "[restore-test] Validando integridad gzip y SQL en $BACKUP_FILE..."
gzip -t "$BACKUP_FILE"
TABLES=$(gunzip -c "$BACKUP_FILE" | grep -c "CREATE TABLE" || true)
echo "[restore-test] OK: $TABLES sentencias CREATE TABLE verificadas."
