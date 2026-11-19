#!/bin/sh
set -eu
TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="/backups/sajona_core_${TS}.sql.gz"
pg_dump -h "${PGHOST:-sajona-core-db}" -U "${PGUSER:-sajona_core}" -d "${PGDATABASE:-sajona_core}" | gzip > "$OUT"
ln -sf "$OUT" /backups/latest.sql.gz
ls -1t /backups/sajona_core_*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm -f
echo "[backup] Respaldo generado: $OUT"
