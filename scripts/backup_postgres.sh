#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${DATABASE_URL:?set DATABASE_URL}"

if [[ "$DATABASE_URL" != postgres* ]]; then
  echo "backup_postgres.sh requires a Postgres DATABASE_URL" >&2
  exit 1
fi

DB_URL="${DATABASE_URL/postgresql+psycopg:/postgresql:}"
DB_URL="${DB_URL/-pooler/}"
mkdir -p backups
OUT="backups/sealquery-$(date -u +%Y%m%dT%H%M%SZ).dump"
pg_dump "$DB_URL" --format=custom --no-owner --file "$OUT"
ls -lh "$OUT"
echo "backup written to $OUT"
