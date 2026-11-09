# SealQuery

SealQuery lets AI agents pay to execute approved computations against privately held datasets without receiving the raw data.

A data owner registers a dataset and the computations it permits. An agent requests one approved computation and pays for execution. The computation runs inside a trusted execution environment. The agent receives an attested result; the data owner receives payment. The raw data is never delivered to the agent.

## The problem

AI agents need external data, but the most valuable datasets cannot be handed over. Selling raw rows exposes sensitive information, violates contracts, or destroys the value of the data. Existing APIs expose only predefined aggregates, and enterprise clean rooms are not built for autonomous per-query agent access.

SealQuery sells the answer, not the dataset. The data owner keeps the raw data; the agent gets an attested result and a receipt.

## What was built

A working NEAR testnet proof with no mocked execution, attestation, access control, or payment:

- A real private dataset stored in OutLayer encrypted worker storage.
- One approved computation running in Intel TDX on OutLayer testnet.
- A multi-tenant NEAR contract (v2) that registers datasets/computations, escrows payment, calls OutLayer, receives the result, and settles to each dataset owner.
- An agent client that quotes, pays, waits, verifies the TEE attestation, and accepts the result.
- A per-dataset privacy budget (20 by default), minimum cohort of 100, output rounding, and a canary row that never appears in results.
- Multi-tenant controls: multiple owners, dataset versions and rotation, pause, per-dataset pricing/budgets, protocol fees, and query history.
- Negative-path tests for unauthorized computations, unauthorized acceptance, direct OutLayer calls, replay, failed executions, refunds, tampered attestations, budget exhaustion, and paused contracts.
- Reproducible contract build, CI, deploy scripts, and clean-clone verification with a real query.

## How NEAR is used

- **Dataset registry:** dataset metadata and approved computation list.
- **Query escrow:** the agent’s payment is held by the contract.
- **Execution request:** the contract calls `outlayer.testnet::request_execution`.
- **Callback:** OutLayer resumes the NEAR yield and the contract receives the TEE result.
- **Settlement:** the agent verifies the attestation and calls `accept_result`; the contract pays the data owner.
- **Refunds:** failed or timed-out queries are refunded to the agent.
- **Privacy budget:** enforced by the contract before the OutLayer call.

OutLayer provides Intel TDX execution and per-execution attestations. NEAR provides the ownership, escrow, callback, and settlement layer.

## Repository layout

```
contracts/sealquery/   NEAR contract
workload/              probe and approved WASI computation
agent/                 agent client
scripts/               dataset preparation and query verification
docs/                  evidence log
```

## Requirements

- Rust 1.99.1 (pinned in `rust-toolchain.toml`)
- `cargo-near` 0.23.0
- `near-cli-rs` 0.31.1
- `wasmtime` 50.0.1
- `outlayer` CLI 0.2.2
- `outlayer-verify` 0.1.0
- NEAR testnet accounts: deployer, contract, data owner, agent
- OutLayer testnet login and a project-restricted payment key

## Quick start

### 1. Prepare the dataset

```bash
python3 scripts/prepare_dataset.py
```

Expected:

- 5,000 deterministic UCI Online Retail rows plus 1 synthetic canary row.
- Dataset SHA-256: `65a10103f741129dc4270d267e694e341efd8b3a4b8ebdf06e97d73bc08b1983`
- Canary country `Canaryland`, customer `99999`, invoice `CANARY-0001`.

The source is public; it is used as a private-data stand-in. The privacy claim is about the architecture, not the secrecy of this public source.

### 2. Run the workload tests

```bash
cargo test -p sealquery-workload
```

Expected: `5 passed`.

### Reproducible build

```bash
cd contracts/sealquery
cargo near build reproducible-wasm
```

Expected contract hash: `5e60a3d25970a34f265afd4ae83b7993462cf38be0f962c2d6bc5995709e94f9`. CI runs format, clippy, tests, workload build, contract build, and the secret scan.

### 3. Build the approved workload

```bash
cargo build -p sealquery-workload \
  --bin sealquery-approved \
  --target wasm32-wasip2 \
  --release \
  --features wasm
```

Expected artifact: `target/wasm32-wasip2/release/sealquery-approved.wasm`.

### 4. Publish the workload to OutLayer

```bash
outlayer login testnet
outlayer upload target/wasm32-wasip2/release/sealquery-approved.wasm
outlayer deploy sealquery-approved <FastFS URL from upload>
```

Expected project: `<deployer>/sealquery-approved`.

Create and fund a project-restricted OutLayer payment key:

```bash
outlayer keys create --project '<deployer>/sealquery-approved'
outlayer keys topup <nonce> --usd 1
```

### 5. Store the access secrets

The upload secret is readable by the data owner. The compute secret is readable only when the SealQuery contract is the calling account.

```bash
outlayer secrets set \
  --profile upload \
  --generate PROTECTED_DATASET_UPLOAD_TOKEN:hex32 \
  --project '<deployer>/sealquery-approved' \
  --access 'whitelist:<deployer>'

outlayer secrets set \
  --profile compute \
  --generate PROTECTED_COMPUTE_ACCESS_TOKEN:hex32 \
  --project '<deployer>/sealquery-approved' \
  --access 'whitelist:<deployer>'
```

Then lock the compute secret to the contract:

```bash
near contract call-function as-transaction outlayer.testnet update_access \
  json-args '{
    "accessor":{"Project":{"project_id":"<deployer>/sealquery-approved"}},
    "profile":"compute",
    "new_access":{"Predecessor":{"condition":{"Whitelist":{"accounts":["<contract>"]}}}}
  }' \
  prepaid-gas '100 Tgas' attached-deposit '0.05 NEAR' \
  sign-as '<deployer>' network-config testnet sign-with-keychain send
```

Expected: `Access control updated`.

### 6. Upload the dataset to encrypted worker storage

Build `data/upload_input.json` with the CSV and its SHA-256, then run:

```bash
outlayer-verify run '<deployer>/sealquery-approved' \
  --network testnet \
  --api https://testnet-api.outlayer.ai \
  --payment-key "$(outlayer keys show <nonce>)" \
  --secrets-ref '<deployer>/upload' \
  --input data/upload_input.json \
  --bundle data/upload_proof.json
```

Expected output includes:

```json
{"bytes":451984,"ok":true,"operation":"upload_dataset","sha256":"65a10103f741129dc4270d267e694e341efd8b3a4b8ebdf06e97d73bc08b1983","stored":true,"version":"retail_v1"}
```

Expected verifier result: `PROVEN`.

### 7. Build and deploy the contract

```bash
cargo near build non-reproducible-wasm --locked --no-abi

near contract deploy '<contract>' \
  use-file target/near/sealquery/sealquery.wasm \
  with-init-call new \
  json-args '{"owner":"<data-owner>"}' \
  prepaid-gas '100 Tgas' attached-deposit '0 NEAR' \
  network-config testnet sign-with-keychain send
```

### 8. Register the dataset and computation

```bash
near contract call-function as-transaction '<contract>' register_dataset \
  json-args '{
    "dataset_id":"retail_v1",
    "version":"retail_v1",
    "data_hash":"65a10103f741129dc4270d267e694e341efd8b3a4b8ebdf06e97d73bc08b1983",
    "allowed_computations":["spend_growth"],
    "price_yocto":"20000000000000000000000",
    "compute_deposit_yocto":"10000000000000000000000",
    "reward_yocto":"10000000000000000000000",
    "budget_per_day":20
  }' \
  prepaid-gas '100 Tgas' attached-deposit '0 NEAR' \
  sign-as '<data-owner>' network-config testnet sign-with-keychain send

near contract call-function as-transaction '<contract>' register_computation \
  json-args '{
    "computation_id":"spend_growth_v1",
    "dataset_id":"retail_v1",
    "outlayer_project_id":"<deployer>/sealquery-approved",
    "wasm_hash":"<approved workload sha256>",
    "operation":"spend_growth",
    "secret_profile":"compute",
    "secret_account":"<deployer>"
  }' \
  prepaid-gas '100 Tgas' attached-deposit '0 NEAR' \
  sign-as '<data-owner>' network-config testnet sign-with-keychain send
```

### 9. Run the agent

Create `data/agent_params.json`:

```json
{"period_a":"2011-11","period_b":"2011-12","countries":["United Kingdom"],"min_cohort_size":100}
```

Run:

```bash
python3 agent/agent.py \
  --contract '<contract>' \
  --agent '<agent>' \
  --params-file data/agent_params.json \
  --proof data/agent_query_proof.json
```

Expected:

```
query_id=...
status=ready
result={"dataset_sha256":"65a1...","min_cohort_size":100,"ok":true,...}
PROVEN task ... (execute) ...
settled
```

The result is an aggregate spend growth, not raw rows. The data owner receives `0.01 NEAR`.

### 10. Verify independently

```bash
python3 scripts/verify_query.py \
  --contract '<contract>' \
  --query-id <query-id> \
  --tx-hash <request tx hash> \
  --proof data/verify_proof.json
```

Expected: the contract query record, the result, and `PROVEN`.

## Multi-tenant controls

```bash
# Rotate a dataset to a new version and hash
near contract call-function as-transaction '<contract>' rotate_dataset \
  json-args '{"dataset_id":"retail_v1","new_version":"retail_v2","new_data_hash":"<new hash>"}' \
  prepaid-gas '50 Tgas' attached-deposit '0 NEAR' \
  sign-as '<data-owner>' network-config testnet sign-with-keychain send

# Pause or unpause new queries (contract owner only)
near contract call-function as-transaction '<contract>' set_paused \
  json-args '{"paused":true}' \
  prepaid-gas '30 Tgas' attached-deposit '0 NEAR' \
  sign-as '<contract-owner>' network-config testnet sign-with-keychain send

# List datasets, computations, and query history
near contract call-function as-read-only '<contract>' list_datasets \
  json-args '{}' network-config testnet now
near contract call-function as-read-only '<contract>' list_computations \
  json-args '{}' network-config testnet now
near contract call-function as-read-only '<contract>' get_queries_for_agent \
  json-args '{"agent":"<agent>"}' network-config testnet now
```

## Payment flow

- Agent pays `0.02 NEAR` to the contract.
- Contract attaches `0.01 NEAR` to OutLayer for compute.
- OutLayer charges actual compute and refunds the unused amount to the contract.
- On acceptance, the contract pays the data owner `0.01 NEAR`.
- On failure or timeout, the agent can call `refund_query` and receive `0.02 NEAR`.

## Privacy controls

- Dataset stays in OutLayer encrypted worker storage; only the approved WASM can read it.
- The compute secret is readable only when the SealQuery contract is the predecessor account.
- The approved computation accepts only allowed countries and periods.
- Minimum cohort: 100.
- Output rounding: spend to nearest 1,000; growth to 0.1%.
- Cohort sizes are reported as `100+` or `suppressed`.
- Per-agent, per-dataset daily budget: 20 queries.
- A canary row is present in the dataset and must never appear in any result.

## Test evidence

See `docs/evidence.md` for transaction hashes, task IDs, attestation results, balances, and negative-test output.

Highlights:

- Dataset upload: OutLayer task `29129`, `PROVEN`.
- Approved computation: OutLayer task `29136`, `PROVEN`.
- Manual end-to-end query: task `29143`, `PROVEN`, payout `0.01 NEAR`.
- Automated agent query: task `29145`, `PROVEN`, settled.
- Refunds: queries 1 and 2 returned `0.02 NEAR` each.
- Direct OutLayer call: denied by the secret access condition.
- Replay and unauthorized acceptance: rejected.
- Tampered proof: `NOT PROVEN`.
- Privacy budget: 20 queries allowed; 21st rejected with `daily privacy budget exceeded`.

## Known limitations

- The dataset is public and used as a private-data stand-in.
- OutLayer currently holds centralized governance keys; the TEE proves what ran, not that the approved build is honest.
- The NEAR callback result is limited to about 900 bytes; larger results would require off-chain delivery plus hash settlement.
- Execution is limited to 180 seconds.
- One dataset, one computation, one agent, and one contract are supported.
- Dataset rotation, differential privacy, and multi-tenant marketplace features are not implemented.
- Cross-chain payments and NEAR Intents are intentionally out of scope.
- The TEE does not guarantee correctness; it proves which WASM ran on which input and output.

## Third-party components

- NEAR Protocol and NEAR testnet
- OutLayer verifiable compute and `outlayer-verify`
- UCI Machine Learning Repository Online Retail dataset
- `near-sdk`, `cargo-near`, `near-cli-rs`
- `wasmtime`
- Rust `csv`, `sha2`, `serde`, `serde_json`

## License

MIT. See `LICENSE`.
