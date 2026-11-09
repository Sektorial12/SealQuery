#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${CONTRACT_ACCOUNT:?set CONTRACT_ACCOUNT}"
: "${OWNER_ACCOUNT:?set OWNER_ACCOUNT}"
: "${DATA_HASH:?set DATA_HASH}"
: "${WASM_HASH:?set WASM_HASH}"
: "${OUTLAYER_PROJECT_ID:?set OUTLAYER_PROJECT_ID}"
: "${SECRET_ACCOUNT:?set SECRET_ACCOUNT}"

NETWORK="${NEAR_NETWORK:-testnet}"
DATASET_ID="${DATASET_ID:-retail_v1}"
DATASET_VERSION="${DATASET_VERSION:-retail_v1}"
BUDGET_PER_DAY="${BUDGET_PER_DAY:-20}"
COMPUTATION_ID="${COMPUTATION_ID:-spend_growth_v1}"
OPERATION="${OPERATION:-spend_growth}"
VERSION="${VERSION:-retail_v1}"
SECRET_PROFILE="${SECRET_PROFILE:-compute}"
PRICE_YOCTO="${PRICE_YOCTO:-20000000000000000000000}"
COMPUTE_DEPOSIT_YOCTO="${COMPUTE_DEPOSIT_YOCTO:-10000000000000000000000}"
REWARD_YOCTO="${REWARD_YOCTO:-10000000000000000000000}"

near contract call-function as-transaction "$CONTRACT_ACCOUNT" register_dataset \
  json-args "{
    \"dataset_id\":\"$DATASET_ID\",
    \"version\":\"$DATASET_VERSION\",
    \"data_hash\":\"$DATA_HASH\",
    \"allowed_computations\":[\"$OPERATION\"],
    \"price_yocto\":\"$PRICE_YOCTO\",
    \"compute_deposit_yocto\":\"$COMPUTE_DEPOSIT_YOCTO\",
    \"reward_yocto\":\"$REWARD_YOCTO\",
    \"budget_per_day\":$BUDGET_PER_DAY
  }" \
  prepaid-gas '100 Tgas' attached-deposit '0 NEAR' \
  sign-as "$OWNER_ACCOUNT" network-config "$NETWORK" sign-with-keychain send

near contract call-function as-transaction "$CONTRACT_ACCOUNT" register_computation \
  json-args "{
    \"computation_id\":\"$COMPUTATION_ID\",
    \"dataset_id\":\"$DATASET_ID\",
    \"outlayer_project_id\":\"$OUTLAYER_PROJECT_ID\",
    \"wasm_hash\":\"$WASM_HASH\",
    \"operation\":\"$OPERATION\",
    \"secret_profile\":\"$SECRET_PROFILE\",
    \"secret_account\":\"$SECRET_ACCOUNT\"
  }" \
  prepaid-gas '100 Tgas' attached-deposit '0 NEAR' \
  sign-as "$OWNER_ACCOUNT" network-config "$NETWORK" sign-with-keychain send
