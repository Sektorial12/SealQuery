# SealQuery Evidence Log

Reproducible evidence for the testnet proof. All values below are from real NEAR testnet and OutLayer testnet activity. No execution, attestation, access-control decision, or payment is mocked.

## Environment

- Network: NEAR testnet
- Deployer: `sealquery-1794187176.testnet`
- Contract: `contract.sealquery-1794187176.testnet`
- Data owner: `owner.sealquery-1794187176.testnet`
- Agent: `agent.sealquery-1794187176.testnet`
- Approved OutLayer project: `sealquery-1794187176.testnet/sealquery-approved`
- Probe OutLayer project: `sealquery-1794187176.testnet/sealquery-probe`
- Tool versions:
  - rustc 1.99.1
  - cargo-near 0.23.0
  - near-cli-rs 0.31.1
  - outlayer 0.2.2
  - wasmtime 50.0.1
  - outlayer-verify 0.1.0

## OutLayer TEE probe

- WASM SHA-256: `3c42ee40fc6d640569068f4ef1be6da09e235bfa22dfca00c1aaca4dffe17197`
- FastFS URL: `https://test.fastfs.io/sealquery-1794187176.testnet/outlayer.testnet/3c42ee40fc6d640569068f4ef1be6da09e235bfa22dfca00c1aaca4dffe17197.wasm`
- Upload transaction: `7ymAHgFdzix7d84PFq5KudqA6xbzRntjfMkSW72XTzVK`
- Execution transaction: `8pxfgLFmPSmKtpyBrGjEZPLfcqJBLS96zcJJBNcawJ3S`
- Task ID: `29081`
- Verification result: `PROVEN task 29081 (execute) 51626e3ed52949cb…8c587920`
- Testnet limitation: `outlayer-verify` 0.1.0 defaults to the retired `testnet-api.outlayer.fastnear.com` API. Pass `--api https://testnet-api.outlayer.ai`.

## Dataset

- Source: UCI Machine Learning Repository, Online Retail dataset
- Source URL: `https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx`
- Sample: 5,000 deterministic rows plus 1 synthetic canary row
- Total rows: 5,001
- Dataset SHA-256: `65a10103f741129dc4270d267e694e341efd8b3a4b8ebdf06e97d73bc08b1983`
- Canary row:
  - Invoice: `CANARY-0001`
  - Stock code: `CANARY`
  - Country: `Canaryland`
  - Customer ID: `99999`
- The source is public; it is used as a private-data stand-in. The privacy claim is about the SealQuery architecture, not the secrecy of this public source.

## Approved computation

- Computation ID: `spend_growth_v1`
- Operation: `spend_growth`
- Dataset version: `retail_v1`
- Current approved workload WASM SHA-256: `3b1bc4eaabcde79492959f8ac34e47173f11b358ca06b31f1694053494acca47`
- Current FastFS URL: `https://test.fastfs.io/sealquery-1794187176.testnet/outlayer.testnet/3b1bc4eaabcde79492959f8ac34e47173f11b358ca06b31f1694053494acca47.wasm`
- Current upload transaction: `9XvfEPBmQXmkLmiiaG4fDUDeKat7SRabJz3qTaccdWxE`
- Computation update transaction: `3wqMpjaMHnfU3gJYui6tg1njQuEimBaSQsKdHdgpqrX9`
- The earlier proof used workload hash `0f20f00c…`; the current source builds to `3b1bc4ea…`.
- Local unit tests: 25 contract tests and 5 workload tests passed
- Test command:
  ```bash
  cargo test -p sealquery-workload
  ```

## Dataset upload to encrypted worker storage

- Execution type: HTTPS API with a project-restricted payment key
- Call ID: `0d5219d3-709e-4561-9d56-eda39035c548`
- OutLayer task ID: `29129`
- Secrets profile: `sealquery-1794187176.testnet/upload`
- Output:
  ```json
  {"bytes":451984,"ok":true,"operation":"upload_dataset","sha256":"65a10103f741129dc4270d267e694e341efd8b3a4b8ebdf06e97d73bc08b1983","stored":true,"version":"retail_v1"}
  ```
- Attestation result: `PROVEN task 29129`
- Proof bundle: `data/upload_proof.json` (local evidence)

## Contract deployment and registration

- Initial deploy transaction: `EXD8MBqzVQz9toRGCXQrjmurXtfLR7UqzhMCNAhs8wpq`
- Current code deploy transaction: `GG7eUiyneH2MNYbPjS3qJ6g3Bd8KovPqB3FjDViTmNfv`
- Current contract code SHA-256 (reproducible build): `5e60a3d25970a34f265afd4ae83b7993462cf38be0f962c2d6bc5995709e94f9`
- Contract version: `0.1.0` (`version()` view)
- Dataset registration transaction: `FVgTfY7jY6Tc1hQPtk2kS24WnDc6vqxbPaDSvzJaYvQU`
- Computation registration transaction: `7kV4TwhMKzqR5kKYM38ZxFwxoLasKqYJFrV8trtRCDQM`
- Economics update transaction: `J2GEPcotbYM6nCfg5AmtvBpuhAHiJCoWECTqB6n1wuZ2`
- Contract query price: `0.02 NEAR`
- Compute deposit: `0.01 NEAR`
- Data-owner reward: `0.01 NEAR`
- Daily privacy budget: 20 queries per agent per dataset

## Multi-tenant contract (v2)

- v2 deployer: `sealquery-v2-1794194344.testnet`
- v2 contract: `contract.sealquery-v2-1794194344.testnet`
- Contract version at the original deploy (historical): `0.2.0`
- Live contract version: `0.2.2`
- v2 code SHA-256 at the original deploy (historical): `3c96314f65221702b1851454e0e2592ab277f8bb274cc1420c6e648dedb5c2d4`
- Hardened v0.2.1 code SHA-256 (historical): `1f9662513bb27354e2289545ad4aecada25acf3301c9c90578ee26bef5a6354e`
- Hardened v0.2.1 deploy transaction (historical): `GSPnhNo8izDYVPoVQytYYSSSEJrxRB9BagHZVZy3d5HN`
- Hardened v0.2.2 code SHA-256: `6749f0bab47ffa6bdc1aaeb9a54fc9eeb8b84f5c2e58f5a0fa4c4902fe5e146c`
- Hardened v0.2.2 deploy transaction: `59FLXYrCv6m7d9zvaTPT2bQpXBYpVE1BjxUbLfs88RhR`
- Hardened v0.2.2 source commit: `90e382d`
- Removed duplicate `retail_alt` dataset: transaction `6kaJX4xU2JHzgobdUdkuiPbSGmg1HVMWYGpcCfScoLtA`
- Reset demo budget for `agent2` on `retail_v1`: transaction `CZeXe9y4zQrtwmbUSiAECTKVZpkxDdDz5KXSHUaRgZBj`
- Contract account funding transaction: `98B7gLLQRMfBbHMNtzMGz7Gp8wHABVpKscFETXRNvquh`
- Initial deploy transaction: `dL3mcj92RyifeLzud5d4WdbxLYvYPQ9Z33kMssKTR4j`
- Reproducible code deploy transaction: `DmA4RP8JvQFyTv9a4Yxu1R3D8f1MpEUw2Dv99EV5bbEX`
- Compute secret access locked to v2 contract: transaction `6AiVHiGSwq2tRRw4nYrwQ1N3aGSGYLw7popd45AWHaGw`
- Dataset `retail_v1`:
  - Owner: `owner.sealquery-1794187176.testnet`
  - Version: `retail_v1`
  - Price: `0.02 NEAR`; reward: `0.01 NEAR`; budget: 20/day
  - Registration transaction: `AdhM7BcdYq2sEAaFShW3pLAutvnA7AwtbWW8meK7FUF5`
  - Computation `spend_growth_v1` registration: `6Z1v6ak9Svc5WtohPS5YFPZsVb9bLQB3i34YwgBAg9Pp`
- Dataset `retail_alt`:
  - Owner: `owner2.sealquery-v2-1794194344.testnet`
  - Version: `retail_v1`
  - Price: `0.03 NEAR`; reward: `0.02 NEAR`; budget: 2/day
  - Registration transaction: `35n6W3crx1m8WPQTDvLo1sx5Hts7RviGYmYxdJx54qkt`
  - Computation `spend_growth_alt` registration: `2BWKC1FgdASd2ZiyDWah5fei7SubjamRksHvusFVexza`
- Query `1` on `retail_v1`:
  - Agent: `agent2.sealquery-1794187176.testnet`
  - Request transaction: `9PHos2pKyLaMd1NCWb9N6oXc69omuDMW1DSB4atGPizf`
  - OutLayer task: `29204`
  - Attestation: `PROVEN task 29204 (execute) 6be38d736a6a8d54…fa818660`
  - Status: `settled`
- Query `2` on `retail_alt`:
  - Request transaction: `A5CtDSXtbJ1tUwwCmBJvY9yugND3fGZAroJzWFFtLxyG`
  - OutLayer task: `29205`
  - Attestation: `PROVEN task 29205 (execute) 5ffaa8843c717f7a…706e1cc2`
  - Status: `settled`
  - Data-owner balance before: `499590340385875400000000`
  - Data-owner balance after: `519590340385875400000000`
- Pause test:
  - `set_paused(true)` by contract owner succeeded
  - Agent query rejected with `contract is paused`
  - `set_paused(false)` restored service
- Dataset rotation:
  - `retail_alt` rotated to `retail_v2`: `7cJBzGaWD4qhzn4Hn8ZrZXAcdDq1VWmBgMt7CxPhnLju`
  - Rotated back to `retail_v1`: `DETpxobXMMZrLVc2KLbgeWHUb8Nw72vta5HfXE2YB64A`
- Query `3` after reproducible v2 deploy:
  - Request transaction: `6RJhWeGkyCs6yzZkFzEwrk3FfRqiGiDZ23GD3SyYQ2Wp`
  - OutLayer task: `29215`
  - Attestation: `PROVEN task 29215 (execute) bcbd5d99243e0a06…6f6368e7`
  - Status: `settled`
- Demo API query `4` (retail_v1):
  - Request transaction: `B7WdyHky452KKVUySK6pa4jBimYHjCCzsbDtHwbzaNbd`
  - Acceptance transaction: `9snQL3FXHTHjhSmnM3LJoryGtMNdcBLrBPRFHgwdqxR6`
  - Proof: `true`
  - Data-owner balance before: `1068217144068062800000000`
  - Data-owner balance after: `1078217144068062800000000`
- Authenticated machine query `5` (`/api/v1/query`, API key + idempotency):
  - Request transaction: `9RUAXRcPN3qzDkTiK3PmopQ5JNWa26SZ2L1e6wLCdVdp`
  - Acceptance transaction: `CSdxbHN61TYtbXhim4q1TyGnCxR9SSdBTCJzmHoFpNg3`
  - OutLayer task: `30169`
  - Attestation: `PROVEN task 30169 (execute) 9b68a814e31e143d…2bb8a8bd`
  - Data-owner balance before: `1078217144068062800000000`
  - Data-owner balance after: `1088217144068062800000000`
  - Replay with the same `Idempotency-Key`: `X-Idempotent-Replay: true`, same query ID, budget unchanged
  - Unauthenticated request: HTTP `401`
- Demo UI query `7` after API refactor (browser endpoint):
  - Request transaction: `6r3tGfDMNAUZXFAdqro5MY9vsMW729M4Qe1nsN9bsQP`
  - Acceptance transaction: `8kayzZtgUCVu1vEj6XMQVijNmSkpLf4pyXJSQtbRTkC8`
  - Proof: `true`
  - Data-owner balance before: `1098217144068062800000000`
  - Data-owner balance after: `1108217144068062800000000`
- Rejected-query path (UI endpoint, disallowed country):
  - Query: `8`
  - Request transaction: `83ZR1a378VZ8wC1YzdokvkGGqMEYnLuMgPM1pGrWcNnW`
  - Status: `failed`; contract status `refunded`
  - Refund transaction: `CK6nNxLJF9U8C3nEWD7rYxoFTk7yR1ggbnNZB9pbcHew`
  - Data-owner balance before/after: `1108217144068062800000000` (unchanged)
  - Budget after: 7/20 queries for `agent2` on `retail_v1`
- Attestation explorer for query `6`:
  - Request transaction: `B5eS1qparbbvut8UEDt3YQ4HYuMxKgc424mJdgjqLLS3`
  - `GET /api/attestation/<tx>`: `proven: true`
  - Task: `30170`; type: `execute`; TCB: `UpToDate`
  - Verdicts: authenticity, identity, binding, input, output all `pass`
  - MRTD: `7fe60787222bd394cb516abca2435f22f035ab2cc9c0a4b4b3b148e46297f3d931a237b72f359052c6e657d8c1409173`
  - Proof bundle: `data/proofs/B5eS1qparbbvut8UEDt3YQ4HYuMxKgc424mJdgjqLLS3.json` (33,665 bytes)
  - Offline check: `outlayer-verify bundle <bundle> --offline --short` returned `PROVEN task 30170 (execute) a133d34367f73895…19be358f`, exit `0`
- MCP query `6` (`run_query` through `mcp/server.py`):
  - Request transaction: `B5eS1qparbbvut8UEDt3YQ4HYuMxKgc424mJdgjqLLS3`
  - Acceptance transaction: `H3pb1M14SLA6GHCCPcwnhv4VE1M4hb4YT7J47jCYou9e`
  - OutLayer task: `30170`
  - Attestation: `PROVEN task 30170 (execute) a133d34367f73895…19be358f`
  - Status: `settled`
  - MCP tools exercised: `list_datasets`, `quote`, `run_query`, `get_query`, `verify_query`
- Multi-tenant views after queries 3-6:
  - `list_datasets`: `["retail_alt","retail_v1"]`
  - `list_computations`: `["spend_growth_alt","spend_growth_v1"]`
  - `get_queries_for_agent(agent2)`: `[1,2,3,4,5,6]`
  - `get_queries_for_dataset(retail_v1)`: `[1,3,4,5,6]`
  - `get_queries_for_dataset(retail_alt)`: `[2]`

## Contract settlement hardening

- `on_query_result` ignores callbacks unless the query is still `pending`.
- `refund_query` rejects a `ready` query. The ready result stays visible, but the
  agent cannot take the answer and refund the deposit.
- `settle_query` lets anyone settle a ready query to the dataset owner after the
  200-block timeout, so an abandoned result still pays the owner.
- `refund_query` is terminal for settled/refunded queries and still refunds
  failed queries and timed-out pending queries.
- Duplicate `computation_id` values are rejected.
- `reward + compute_deposit <= price` is enforced.
- Dataset economics cannot change after the dataset has queries.
- Protocol fees cannot change after the first query.
- Dataset registration is contract-owner gated; the duplicate `retail_alt`
  record was removed on-chain.
- The owner-only `withdraw_contract_balance` method was removed.
- `reset_budget` is owner-only and used only to restore the testnet demo budget.
- Added contract tests for ready-query refund rejection, pending/failed refunds,
  owner settlement after timeout, accept replay, protocol-fee freezing,
  owner-gated registration, budget reset, dataset removal, and late/failed callbacks.
- Hosted query `32` after the v0.2.1 upgrade: task `41071`, `PROVEN`, settled.
- Post-v0.2.2 query `36`: task `45967`, `PROVEN`, settled; request
  `G7UEUxyenoruZzQiheLeCM7ND58Kd2dU6vRKdTdpo2YA`, accept
  `EVUoAdUKMhxfDiuVUU9JeFHd8SAmo6R56qgyx4hGLVGK`.
- Ready-result regression on the live v0.2.2 contract: query `37` request
  `Ba6Jw8f22YNXkqS7oCrpLKe8B1XooqyRY6YVTBrsyBjj`; after the callback set it
  `ready`, `refund_query` was rejected with
  `Smart contract panicked: ready query must be settled, not refunded`.
- After the 200-block timeout, permissionless `settle_query` paid the owner:
  transaction `2nVhVTfXKcUuhbxsZa1HaMcEyAm8viBcjzXuDYWmc4Wo`; query `37` is
  `settled`.
- Live v0.2.2 state after cleanup: `list_datasets` = `["retail_v1"]`, budget
  `2/20`, `paused=false`.
- Post-upgrade async incident drill on v0.5.0 API: job
  `a8929f45227d461ca71d469b3d712deb` failed fast with `contract is paused`;
  pause/unpause finished with `DRILL PASSED`.

## End-to-end query

### Manual end-to-end proof

- Query ID: `3`
- Request transaction: `8m9AHapqYu4qmXLfcLmToCbQ2vTw7h65fN643wbSDkBD`
- OutLayer task ID: `29143`
- OutLayer cost: `0.0013357096 NEAR`
- OutLayer refund to contract: `0.0086642904 NEAR`
- Result:
  ```json
  {"dataset_sha256":"65a10103f741129dc4270d267e694e341efd8b3a4b8ebdf06e97d73bc08b1983","min_cohort_size":100,"ok":true,"operation":"spend_growth","period_a":"2011-11","period_b":"2011-12","results":[{"cohort_a":"100+","cohort_b":"100+","country":"United Kingdom","growth_pct":-69.2,"spend_a":13000.0,"spend_b":4000.0}],"version":"retail_v1"}
  ```
- Attestation verification: `PROVEN task 29143 (execute) 75e9224ff7a77e94…6b119adb`
- Acceptance transaction: `FwXwHRedYyZjr4PAZ9WFSBRF2vrjX8y963p2uRdBEr4y`
- Data-owner balance before: `999452337112338100000000` yoctoNEAR
- Data-owner balance after: `1009452337112338100000000` yoctoNEAR
- Payout: `0.01 NEAR`

### Automated agent client

- Command:
  ```bash
  python3 agent/agent.py \
    --contract contract.sealquery-1794187176.testnet \
    --agent agent.sealquery-1794187176.testnet \
    --params-file data/agent_params.json \
    --proof data/agent_query_proof.json
  ```
- Query ID: `4`
- Request transaction: `fZe76tS4V67HmWbZi4cg8AFF1nS2bvnfnyDUz5zjp5v`
- OutLayer task ID: `29145`
- Attestation verification: `PROVEN task 29145 (execute) a1425e965a25237d…af2e5e15`
- Final status: `settled`

### Current-build query after workload update

- Agent: `agent2.sealquery-1794187176.testnet`
- Query ID: `21`
- Request transaction: `72zzvaARAAk6y55DcDANG97BMC12wqyHFUbB23Bo2QGX`
- OutLayer task ID: `29176`
- Workload hash: `3b1bc4eaabcde79492959f8ac34e47173f11b358ca06b31f1694053494acca47`
- Attestation verification: `PROVEN task 29176 (execute) e8ef182665618d8a…d5d01625`
- Final status: `settled`

### Reproducible-build query

- Agent: `agent2.sealquery-1794187176.testnet`
- Query ID: `22`
- Request transaction: `FoVASC9pAvu4pBkCDs41BPoTRUCExuD4sBTSJ5Nhbse7`
- OutLayer task ID: `29184`
- Contract hash: `5e60a3d25970a34f265afd4ae83b7993462cf38be0f962c2d6bc5995709e94f9`
- Attestation verification: `PROVEN task 29184 (execute) d8790b0e0ec9afcf…f133a848`
- Final status: `settled`

### Independent verification command

```bash
python3 scripts/verify_query.py \
  --contract contract.sealquery-1794187176.testnet \
  --query-id 4 \
  --tx-hash fZe76tS4V67HmWbZi4cg8AFF1nS2bvnfnyDUz5zjp5v \
  --proof data/verify_query4_proof.json
```

## Access control

- The compute secret access condition was updated to:
  ```json
  {"Predecessor":{"condition":{"Whitelist":{"accounts":["contract.sealquery-1794187176.testnet"]}}}}
  ```
- Update transaction: `6FM61PmZZECjeNUwgybqaLyJr96YYn5rUgfQ7359hHGC`
- Direct call by the data-owner payment key:
  - Call ID: `e509aebf-5007-475e-bfbb-88963a3596b7`
  - Result: denied by access condition
  - Error: `Access denied by access condition — signer sealquery-1794187176.testnet, called from sealquery-1794187176.testnet`
- The contract-only path succeeded for queries 3 and 4.

## Refunds and failure handling

- Query 1 failed because the contract sent `input_data` as an object instead of a string.
- Query 2 failed because the attached compute deposit was below OutLayer's required amount.
- Refund query 1 transaction: `DLH2qbG1aBFhq3GTbxZU61J8AwD2CdSRtkzfK9QbADq4`
- Refund query 2 transaction: `ChM6C5kdymCMj4Sy6m3ZvEip4Sk1fZGdBLAD65E8ubsn`
- Each refund returned `0.02 NEAR` to the agent.
- Agent balance before refunds: `937233287987583900000000` yoctoNEAR
- Agent balance after refunds: `976749901381819700000000` yoctoNEAR

## Negative tests

- Unauthorized acceptance from the data owner: failed with `only the requesting agent can accept`.
- Replay acceptance of settled query 3: failed with `query result is not ready`.
- Direct OutLayer call with the data-owner payment key: failed with access-condition denial.
- Tampered proof bundle:
  - Command: `outlayer-verify bundle data/tampered_proof.json --offline --short`
  - Exit code: `1`
  - Result: `NOT PROVEN task 29136 (execute) … — failed`
- Privacy budget:
  - Budget state after 20 successful queries: `{"count":20,"day":20766}`
  - 21st query failed with `daily privacy budget exceeded`
- Small-cohort suppression and disallowed-country rejection are covered by local unit tests and the approved workload code.

## Privacy checks

- Canary absent from query 3 and query 4 results.
- Canary absent from agent logs.
- Agent never received the dataset or the compute secret.
- Direct OutLayer access denied.
- Repeated-query budget enforced at 20 per agent per dataset per day.
- Output is rounded: spend to nearest 1,000; growth to 0.1%; cohort reported as `100+` or `suppressed`.

## Reproducible build and CI

- Contract reproducible-build metadata is in `contracts/sealquery/Cargo.toml`.
- Build image: `sourcescan/cargo-near:0.22.0-rust-1.99.1`
- Image digest: `sha256:c9655eaf7436b90c87ea8b25739f91063032c5c30ba24cfeafe72c142943b5bb`
- Reproducible build command: `cd contracts/sealquery && cargo near build reproducible-wasm`
- Reproducible contract hash: `6749f0bab47ffa6bdc1aaeb9a54fc9eeb8b84f5c2e58f5a0fa4c4902fe5e146c` (v0.2.2)
- Historical contract hash: `5e60a3d25970a34f265afd4ae83b7993462cf38be0f962c2d6bc5995709e94f9` (v0.1.0)
- CI: `.github/workflows/ci.yml` runs format, clippy, tests, workload build, contract build, and secret scan.
- Deploy scripts: `scripts/deploy_contract.sh`, `scripts/deploy_workload.sh`, `scripts/register_computation.sh`.

## Clean-clone verification

- Clone: `git clone <repository> /tmp/sealquery-clean`
- `cargo fmt --all -- --check`: passed
- `cargo clippy --workspace --all-targets -- -D warnings`: passed
- `cargo test --workspace`: 25 contract tests and 5 workload tests passed
- Approved workload WASM build: passed
- Contract WASM build: passed
- `./scripts/check_secrets.sh`: passed
- Result: `CLEAN_CLONE_OK`
- Real query from the clean clone:
  - Query ID: `23`
  - Request transaction: `64HJboSXhy6cb18n45QBFGVEC1B34UY5n1iX7ZoZqP9Y`
  - OutLayer task ID: `29193`
  - Attestation verification: `PROVEN task 29193 (execute) 532ce5ebf1dd2e49…e41ba01d`
  - Final status: `settled`

## Operations and security validation

- Metrics endpoint `GET /api/metrics`:
  - Recent queries: 5 (`settled` 4, `refunded` 1); recent success rate `0.8`.
  - Agent balance after the drill: `750415838565469700000000` yoctoNEAR; contract balance: `7061316963159257100000000` yoctoNEAR.
  - Alerts: `recent_refunds` (info); no critical alert.
  - `python3 scripts/monitor.py --once`: exit `0`.
- State cache and load test:
  - Cold state read: `4.15 s`.
  - Warm state read: `0.016 s`.
  - `python3 scripts/load_test.py --requests 6 --concurrency 3`: 0 errors, min `1.3 ms`, p50 `26.4 ms`, p95 `54.9 ms`, max `57.0 ms`.
- Incident drill (`DRILL_CONFIRM=1`, `scripts/incident_drill.sh`):
  - Pause transaction: `9TGfh93yB6RFGQCMMA3RNvuEr9c8haJ7QXMWvkscUKJ6`
  - Query rejected while paused: `Eep8SArVr9RNCSx6xnHV19ZZhQN2ac7U1VDyK6ZP66AN` (`contract is paused`)
  - Unpause transaction: `AfLEwDXbZuBKWnazcVKWNq9Sb6okcKUuAAYhiobFmHh8`
  - Result: `DRILL PASSED`; contract resumed as `paused=false`
- SLOs and threat model:
  - SLOs are defined in `docs/operations.md`.
  - Threat model and privacy review are in `docs/threat-model.md`.
  - No critical finding in the testnet scope; production gaps are documented.

## Early web app validation (pre-FastAPI prototype)

- This early run used the Flask prototype; current FastAPI/hosted evidence is
  below.
- `frontend/` is a Next.js 16 + TypeScript + Tailwind app.
- `pnpm lint` and `pnpm build` pass.
- Routes verified in headless Chromium: `/`, `/pricing`, `/security`, `/status`,
  `/docs`, `/app`, `/app/datasets`, `/app/datasets/retail_v1`, `/app/queries`,
  `/app/queries/11`, `/app/proofs`, `/app/owner`, `/app/agent`.
- Browser query `11` through the Next.js app:
  - Request transaction: `CEgQY3Yy17kFPsemG6KmmkQzjBSvorBzB1L5ELLm2bQm`
  - Acceptance transaction: `E79o9QJ7ULdebmgzUF8twwxXcyfsCVr9FzoWGCHEY2bn`
  - OutLayer task: `30292`
  - Attestation: `PROVEN`, TCB `UpToDate`
  - Status: `settled`
- Browser rejected-query path `12`:
  - Request transaction: `AWXN48inL2QCPRs3XMZ1snfBt2d8yqoPbFyDaSuuL3k1`
  - Refund transaction: `H8bjSYq5jxwaxRSPUD7A8P9RUaphb47zegAb5ywV6hzi`
  - Status: `refunded`; no aggregate released

## FastAPI and Postgres validation

- `backend/` FastAPI service uses SQLAlchemy + Postgres (SQLite for local dev),
  Redis-backed rate limits/idempotency when configured, and a separate indexer.
- Local Postgres 16 test:
  - Created database `sealquery`; `init_db()` created `datasets` and `queries`.
  - Indexer synchronized 2 datasets and 15 queries.
  - `GET /api/queries?limit=2` returned the latest IDs `14`, `15` with statuses
    `settled`, `refunded`.
- FastAPI query `13`:
  - Request transaction: `4EbQGQ79bdJ9kAX7LvS8oEQS8ihdZnYpS3wYx2xnDUvA`
  - Acceptance transaction: `DFCAETdS9ofWXocpjLbeatqnFhxiPCkdzetM4pNhd3Cw`
  - OutLayer task: `30304`; attestation `PROVEN`; TCB `UpToDate`.
- FastAPI rejected query `15`:
  - Request transaction: `3KkHE5fNqu4ygPWJDE9m6sNAC8pKds3L4fuHtG3N8RWt`
  - Refund transaction: `EX4f86E4jWSJYv6p3VWwsxPNqcZjmGiuxCfZRG4s8Ydj`
  - Status: `refunded`.
- Next.js dev proxy tested against FastAPI on `:8000`; MCP smoke test and
  `get_query`/`verify_query` passed against FastAPI.
- Docker Compose runtime validation:
  - Backend and web images built successfully.
  - Compose brought up Next.js, FastAPI, indexer, Postgres, Redis, and Caddy.
  - Caddy app: `http://127.0.0.1:8080/` returned HTTP `200`.
  - Indexer logged `indexed datasets=2 queries=16`.
  - Compose query `16`:
    - Request transaction: `5a5wy2c1aRwDcirgFcSN4Tqngc7fwJYj95UMQRxogt4m`
    - Acceptance transaction: `7JysUQE6rFvo3FdhH1ee8WofhTcwcPNKQYFRyZECPXQq`
    - OutLayer task: `31582`; attestation `PROVEN`; TCB `UpToDate`.
    - Contract/API status: `settled`.
  - The backend container signed with the mounted access-key file and verified
    the proof with the built-in `outlayer-verify` binary.

## Async query worker and refund reconciler

- `POST /api/query` and `POST /api/v1/query` now enqueue a Postgres job and
  return `202` with a `job_id`.
- `GET /api/jobs/<job_id>` and `GET /api/v1/jobs/<job_id>` expose queue/running/
  terminal state.
- Worker processes jobs, updates query history, verifies TDX, and accepts or
  refunds.
- Async queries:
  - Query `18` — settled.
  - Query `19` via the Next.js UI — task `31785`, `PROVEN`, settled.
  - Query `20` with a disallowed country — `refunded`; refund tx
    `8gQbu15HZF6tNef14bypLqHBK4L9vDbTUcz69pQhwkrq`.
  - Query `22` via Docker Compose — `settled`.
  - Hosted async query `25` — task `31808`, `PROVEN`, settled; request tx
    `Z2fkhnhef4E3q18Deyt1yVMc8cpgsrH4yEzogK5xGTx`, accept tx
    `C1FcBieUfyZX7iBftfPDzqMsGsVGAbqou2W6pvDj9WA4`.
  - The Render worker consumed the hosted job (`attempts: 1`) and the hosted
    UI query page rendered the TDX report.
- Reconciler test: a stale running job without a query ID was moved to `error`
  with `job timed out before a query was submitted`.
- MCP `run_query` now polls the async job endpoint; MCP query `21` settled with
  `PROVEN`.
- Compose now runs a separate `worker` service with the mounted access-key file.

## Event-log indexer

- `indexer` now also streams NEP-297 `EVENT_JSON` logs from Neardata
  (`https://testnet.neardata.xyz`), stores them in `events`, and updates query
  records.
- Incremental by default from the latest finalized block; optional backfill via
  `EVENT_START_BLOCK`.
- Test backfill from block `277018789` with a 25-block window:
  - `query_requested` at block `277018789`.
  - `query_result` at block `277018801`.
  - `query_settled` at block `277018811`.
  - Query `25` ended `settled` with request tx `Z2fk...` and accept tx
    `C1FcB...`.
- Neardata event indexing defaults to 10 blocks per 5 seconds (about
  132 requests/minute including the latest-block lookup), with retry/backoff for
  429/5xx and an optional `NEARDATA_API_KEY`; the polling indexer remains the
  historical fallback.
- `GET /api/events` exposes recent indexed events.
- `GET /api/owner/summary` returns indexed owner earnings; the local test DB
  reported 2 owners, 16 settled queries, and `0.17 NEAR` gross owner reward.

## Demo flow script

- `scripts/demo_flow.py` runs the hosted/local async flow and prints a transcript.
- Accepted demo query `29` — OutLayer task `39338`, `PROVEN`, TCB `UpToDate`,
  request tx `4ze6cpKMDdSmYCsti6EYoA5fe4mCXCGXBs9gYLuSEYXK`, accept tx
  `F9woKqZh3B4TMXBiidPahcmXJqmt8uFwqp6KaTKNEinL`.
- Proof bundle: `data/demo_proof.json` (33,665 bytes); offline verification:
  `PROVEN task 39338 (execute) 8fb3786dc6c3c5ef…ac4991b3`.
- Rejected demo query `30` — `refunded`; request tx
  `GUZzDPS5jgHKfYjG6zqRHTkoAxPaykZuVYgq2qce7BQ8`, refund tx
  `2jG5kdP6tUZiso3u8eAEttgr1R2NaHdSPSgyveirSUDg`.
- Owner balance unchanged for the rejected query.

## Observability and backups

- `GET /api/ready` checks database readiness; Render and Compose health checks
  use it.
- `GET /metrics` exposes Prometheus gauges for paused state, budgets, query/job
  counts, event counts, event-indexer checkpoint, and service heartbeat age.
- Worker and indexer write heartbeats; `/api/metrics` raises
  `worker_missing`/`worker_stale` and `indexer_missing`/`indexer_stale` alerts.
- `scripts/backup_postgres.sh` was tested against local Postgres 16 and produced
  `backups/sealquery-20261110T154613Z.dump`; restore is guarded by
  `RESTORE_CONFIRM=1`.

## Known limitations

- The dataset is public and used as a private-data stand-in.
- OutLayer currently holds centralized governance keys; the TEE proves what ran, not that the approved build is honest.
- The NEAR callback output is limited to 900 bytes; larger results would require off-chain delivery plus hash settlement.
- Execution is limited to 180 seconds.
- The live demo has one owner-gated dataset and one approved computation. Dataset registration is not permissionless; multi-tenant onboarding still needs an owner-proof design.
- Aggregate results are public on-chain and through the API. Raw rows are not delivered, but results are not exclusive to the buyer.
- Differential privacy and a full marketplace discovery/ordering layer are not implemented.
- The demo API is a single FastAPI process; Redis backs idempotency/rate limits when deployed, with an in-memory local fallback.
- No central secret manager, on-call routing, or production dashboards are implemented.
- Paid concurrent-query load and a full OutLayer outage simulation are not run.
- Historical event backfill is optional because of the public Neardata rate limit; incremental events and polling history cover the demo.
- The UI uses the server-side demo agent; a human wallet connection is deferred.
- The browser query endpoint is allowlisted to configured demo datasets but remains key-free and can spend within the agent budget.
- Cross-chain payments and NEAR Intents are intentionally out of scope.
