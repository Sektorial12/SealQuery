#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${CONTRACT_ACCOUNT:?set CONTRACT_ACCOUNT}"
: "${AGENT_ACCOUNT:?set AGENT_ACCOUNT}"

export NEAR_NETWORK="${NEAR_NETWORK:-testnet}"
export NEAR_RPC="${NEAR_RPC:-https://rpc.testnet.fastnear.com}"
export OUTLAYER_API="${OUTLAYER_API:-https://testnet-api.outlayer.ai}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./backend/data/sealquery.db}"
export REDIS_URL="${REDIS_URL:-}"
export PYTHONPATH=backend

if [[ -x backend/.venv/bin/uvicorn ]]; then
  exec backend/.venv/bin/uvicorn app.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
fi

exec python3 -m uvicorn app.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
