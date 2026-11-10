#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${DATABASE_URL:?set DATABASE_URL}"
: "${BACKUP_FILE:?set BACKUP_FILE}"

if [[ "${RESTORE_CONFIRM:-}" != "1" ]]; then
  echo "Refusing to restore. Set RESTORE_CONFIRM=1 and target the correct database." >&2
  exit 1
fi

if [[ "$DATABASE_URL" != postgres* ]]; then
  echo "restore_postgres.sh requires a Postgres DATABASE_URL" >&2
  exit 1
fi
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

DB_URL="${DATABASE_URL/postgresql+psycopg:/postgresql:}"
DB_URL="${DB_URL/-pooler/}"
pg_restore "$DB_URL" --clean --if-exists --no-owner "$BACKUP_FILE"
echo "restore complete from $BACKUP_FILE"
