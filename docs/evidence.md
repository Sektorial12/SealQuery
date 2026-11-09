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
- Local unit tests: 8 contract tests and 5 workload tests passed
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
- Reproducible contract hash: `5e60a3d25970a34f265afd4ae83b7993462cf38be0f962c2d6bc5995709e94f9`
- CI: `.github/workflows/ci.yml` runs format, clippy, tests, workload build, contract build, and secret scan.
- Deploy scripts: `scripts/deploy_contract.sh`, `scripts/deploy_workload.sh`, `scripts/register_computation.sh`.

## Clean-clone verification

- Clone: `git clone /home/spektor/code/nearhack/code /tmp/opencode/sealquery-clean`
- `cargo fmt --all -- --check`: passed
- `cargo clippy --workspace --all-targets -- -D warnings`: passed
- `cargo test --workspace`: 8 contract tests and 5 workload tests passed
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

## Known limitations

- The dataset is public and used as a private-data stand-in.
- OutLayer currently holds centralized governance keys; the TEE proves what ran, not that the approved build is honest.
- The NEAR callback output is limited to 900 bytes; larger results would require off-chain delivery plus hash settlement.
- Execution is limited to 180 seconds.
- The PoC supports one dataset, one computation, one agent, and one contract.
- Dataset rotation, differential privacy, and multi-tenant marketplace features are not implemented.
- Cross-chain payments and NEAR Intents are intentionally out of scope.
