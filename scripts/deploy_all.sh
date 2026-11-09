#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

./scripts/deploy_contract.sh
./scripts/deploy_workload.sh
./scripts/register_computation.sh
