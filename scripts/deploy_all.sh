#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export INIT="${INIT:-1}"
echo "deploy_all: INIT=$INIT (1 creates a fresh contract; 0 upgrades an existing one)"
./scripts/deploy_contract.sh
./scripts/deploy_workload.sh
./scripts/register_computation.sh
