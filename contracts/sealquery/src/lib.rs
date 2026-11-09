use std::collections::BTreeMap;

use near_sdk::json_types::U128;
use near_sdk::serde_json::{json, Value};
use near_sdk::{env, near, AccountId, Gas, NearToken, PanicOnDefault, Promise};

const OUTLAYER_ACCOUNT: &str = "outlayer.testnet";
const MAX_QUERIES_PER_DAY: u32 = 20;
const QUERY_TIMEOUT_BLOCKS: u64 = 200;

#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct Dataset {
    pub owner: AccountId,
    pub data_hash: String,
    pub allowed_computations: Vec<String>,
    pub price_yocto: U128,
    pub compute_deposit_yocto: U128,
    pub reward_yocto: U128,
}

#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct Computation {
    pub dataset_id: String,
    pub outlayer_project_id: String,
    pub wasm_hash: String,
    pub operation: String,
    pub version: String,
    pub secret_profile: String,
    pub secret_account: AccountId,
}

#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct Query {
    pub agent: AccountId,
    pub dataset_id: String,
    pub computation_id: String,
    pub deposit_yocto: U128,
    pub status: String,
    pub result: Option<String>,
    pub created_block: u64,
}

#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct Budget {
    pub day: u64,
    pub count: u32,
}

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct SealQuery {
    owner: AccountId,
    datasets: BTreeMap<String, Dataset>,
    computations: BTreeMap<String, Computation>,
    queries: BTreeMap<u64, Query>,
    budgets: BTreeMap<String, Budget>,
    next_query_id: u64,
}

#[near]
impl SealQuery {
    #[init]
    pub fn new(owner: AccountId) -> Self {
        Self {
            owner,
            datasets: BTreeMap::new(),
            computations: BTreeMap::new(),
            queries: BTreeMap::new(),
            budgets: BTreeMap::new(),
            next_query_id: 1,
        }
    }

    #[allow(clippy::too_many_arguments)]
    #[payable]
    pub fn register_dataset(
        &mut self,
        dataset_id: String,
        data_hash: String,
        allowed_computations: Vec<String>,
        price_yocto: U128,
        compute_deposit_yocto: U128,
        reward_yocto: U128,
    ) {
        let caller = env::predecessor_account_id();
        if self.datasets.contains_key(&dataset_id) {
            env::panic_str("dataset already exists");
        }
        if data_hash.len() != 64 {
            env::panic_str("data_hash must be 64 hex characters");
        }
        if reward_yocto.0 > price_yocto.0 || compute_deposit_yocto.0 > price_yocto.0 {
            env::panic_str("reward and compute deposit must not exceed price");
        }
        let dataset = Dataset {
            owner: caller.clone(),
            data_hash,
            allowed_computations,
            price_yocto,
            compute_deposit_yocto,
            reward_yocto,
        };
        self.datasets.insert(dataset_id.clone(), dataset);
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "1.0.0",
                "event": "dataset_registered",
                "data": [{"dataset_id": dataset_id, "owner": caller}],
            })
        ));
    }

    #[allow(clippy::too_many_arguments)]
    pub fn register_computation(
        &mut self,
        computation_id: String,
        dataset_id: String,
        outlayer_project_id: String,
        wasm_hash: String,
        operation: String,
        version: String,
        secret_profile: String,
        secret_account: AccountId,
    ) {
        let caller = env::predecessor_account_id();
        let dataset = match self.datasets.get(&dataset_id) {
            Some(dataset) => dataset,
            None => env::panic_str("dataset not found"),
        };
        if dataset.owner != caller {
            env::panic_str("only the dataset owner can register computations");
        }
        if !dataset
            .allowed_computations
            .iter()
            .any(|item| item == &operation)
        {
            env::panic_str("operation is not allowed for this dataset");
        }
        if wasm_hash.len() != 64 {
            env::panic_str("wasm_hash must be 64 hex characters");
        }
        self.computations.insert(
            computation_id.clone(),
            Computation {
                dataset_id,
                outlayer_project_id,
                wasm_hash,
                operation,
                version,
                secret_profile,
                secret_account,
            },
        );
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "1.0.0",
                "event": "computation_registered",
                "data": [{"computation_id": computation_id}],
            })
        ));
    }

    pub fn update_dataset_economics(
        &mut self,
        dataset_id: String,
        price_yocto: U128,
        compute_deposit_yocto: U128,
        reward_yocto: U128,
    ) {
        let caller = env::predecessor_account_id();
        let mut dataset = self.dataset(&dataset_id);
        if dataset.owner != caller {
            env::panic_str("only the dataset owner can update economics");
        }
        if reward_yocto.0 > price_yocto.0 || compute_deposit_yocto.0 > price_yocto.0 {
            env::panic_str("reward and compute deposit must not exceed price");
        }
        dataset.price_yocto = price_yocto;
        dataset.compute_deposit_yocto = compute_deposit_yocto;
        dataset.reward_yocto = reward_yocto;
        self.datasets.insert(dataset_id, dataset);
    }

    pub fn version() -> String {
        env!("CARGO_PKG_VERSION").to_string()
    }

    #[allow(clippy::too_many_arguments)]
    pub fn update_computation(
        &mut self,
        computation_id: String,
        outlayer_project_id: String,
        wasm_hash: String,
        operation: String,
        version: String,
        secret_profile: String,
        secret_account: AccountId,
    ) {
        let caller = env::predecessor_account_id();
        let mut computation = self.computation(&computation_id);
        let dataset = self.dataset(&computation.dataset_id);
        if dataset.owner != caller {
            env::panic_str("only the dataset owner can update computations");
        }
        if !dataset
            .allowed_computations
            .iter()
            .any(|item| item == &operation)
        {
            env::panic_str("operation is not allowed for this dataset");
        }
        if wasm_hash.len() != 64 {
            env::panic_str("wasm_hash must be 64 hex characters");
        }
        computation.outlayer_project_id = outlayer_project_id;
        computation.wasm_hash = wasm_hash;
        computation.operation = operation;
        computation.version = version;
        computation.secret_profile = secret_profile;
        computation.secret_account = secret_account;
        self.computations.insert(computation_id, computation);
    }

    pub fn quote(&self, dataset_id: String, computation_id: String) -> Value {
        let dataset = self.dataset(&dataset_id);
        let _computation = self.computation(&computation_id);
        json!({
            "dataset_id": dataset_id,
            "computation_id": computation_id,
            "price_yocto": dataset.price_yocto,
            "reward_yocto": dataset.reward_yocto,
            "compute_deposit_yocto": dataset.compute_deposit_yocto,
            "max_queries_per_day": MAX_QUERIES_PER_DAY,
        })
    }

    #[payable]
    pub fn request_query(
        &mut self,
        dataset_id: String,
        computation_id: String,
        params: String,
    ) -> Promise {
        let agent = env::predecessor_account_id();
        let dataset = self.dataset(&dataset_id);
        let computation = self.computation(&computation_id);
        if computation.dataset_id != dataset_id {
            env::panic_str("computation does not belong to dataset");
        }
        if env::attached_deposit().as_yoctonear() != dataset.price_yocto.0 {
            env::panic_str("attach the exact query price");
        }
        self.charge_budget(&agent, &dataset_id);

        let query_id = self.next_query_id;
        self.next_query_id += 1;
        self.queries.insert(
            query_id,
            Query {
                agent: agent.clone(),
                dataset_id: dataset_id.clone(),
                computation_id: computation_id.clone(),
                deposit_yocto: dataset.price_yocto,
                status: "pending".to_string(),
                result: None,
                created_block: env::block_height(),
            },
        );

        let input = build_input(&dataset, &computation, &params);
        let args = json!({
            "source": {
                "Project": {
                    "project_id": computation.outlayer_project_id,
                    "version_key": computation.wasm_hash,
                }
            },
            "input_data": input.to_string(),
            "secrets_ref": {
                "profile": computation.secret_profile,
                "account_id": computation.secret_account,
            },
            "resource_limits": {
                "max_instructions": 10_000_000_000u64,
                "max_memory_mb": 128u32,
                "max_execution_seconds": 60u64,
            },
            "response_format": "Json",
            "payer_account_id": env::current_account_id(),
        });

        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "1.0.0",
                "event": "query_requested",
                "data": [{"query_id": query_id, "agent": agent, "dataset_id": dataset_id, "computation_id": computation_id}],
            })
        ));

        Promise::new(OUTLAYER_ACCOUNT.parse().unwrap())
            .function_call(
                "request_execution".to_string(),
                args.to_string().into_bytes(),
                NearToken::from_yoctonear(dataset.compute_deposit_yocto.0),
                Gas::from_tgas(150),
            )
            .then(
                Self::ext(env::current_account_id())
                    .with_static_gas(Gas::from_tgas(20))
                    .on_query_result(query_id),
            )
    }

    #[private]
    pub fn on_query_result(&mut self, query_id: u64) {
        let status = match env::promise_result_checked(0, 10_000) {
            Ok(data) => {
                let text = String::from_utf8(data).unwrap_or_default();
                let parsed: Value = near_sdk::serde_json::from_str(&text).unwrap_or(Value::Null);
                if parsed.get("ok").and_then(Value::as_bool).unwrap_or(false) {
                    if let Some(query) = self.queries.get_mut(&query_id) {
                        query.status = "ready".to_string();
                        query.result = Some(text);
                    }
                    "ready"
                } else {
                    if let Some(query) = self.queries.get_mut(&query_id) {
                        query.status = "failed".to_string();
                    }
                    "failed"
                }
            }
            Err(_) => {
                if let Some(query) = self.queries.get_mut(&query_id) {
                    query.status = "failed".to_string();
                }
                "failed"
            }
        };
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "1.0.0",
                "event": "query_result",
                "data": [{"query_id": query_id, "status": status}],
            })
        ));
    }

    pub fn accept_result(&mut self, query_id: u64) -> Promise {
        let agent = env::predecessor_account_id();
        let query = match self.queries.get(&query_id) {
            Some(query) => query.clone(),
            None => env::panic_str("query not found"),
        };
        if query.agent != agent {
            env::panic_str("only the requesting agent can accept");
        }
        if query.status != "ready" {
            env::panic_str("query result is not ready");
        }
        let dataset = self.dataset(&query.dataset_id);
        if let Some(stored) = self.queries.get_mut(&query_id) {
            stored.status = "settled".to_string();
        }
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "1.0.0",
                "event": "query_settled",
                "data": [{"query_id": query_id, "dataset_owner": dataset.owner, "reward_yocto": dataset.reward_yocto}],
            })
        ));
        Promise::new(dataset.owner).transfer(NearToken::from_yoctonear(dataset.reward_yocto.0))
    }

    pub fn refund_query(&mut self, query_id: u64) -> Promise {
        let agent = env::predecessor_account_id();
        let query = match self.queries.get(&query_id) {
            Some(query) => query.clone(),
            None => env::panic_str("query not found"),
        };
        if query.agent != agent {
            env::panic_str("only the requesting agent can refund");
        }
        if query.status == "settled" || query.status == "refunded" {
            env::panic_str("query already final");
        }
        let timed_out = env::block_height() > query.created_block + QUERY_TIMEOUT_BLOCKS;
        if query.status != "failed" && !timed_out {
            env::panic_str("query is not failed and has not timed out");
        }
        if let Some(stored) = self.queries.get_mut(&query_id) {
            stored.status = "refunded".to_string();
        }
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "1.0.0",
                "event": "query_refunded",
                "data": [{"query_id": query_id, "agent": query.agent, "amount_yocto": query.deposit_yocto}],
            })
        ));
        Promise::new(query.agent).transfer(NearToken::from_yoctonear(query.deposit_yocto.0))
    }

    pub fn withdraw_contract_balance(&mut self) -> Promise {
        let caller = env::predecessor_account_id();
        if caller != self.owner {
            env::panic_str("only the contract owner can withdraw");
        }
        let amount = env::account_balance().as_yoctonear();
        let reserve = NearToken::from_millinear(100).as_yoctonear();
        let withdraw = amount.saturating_sub(reserve);
        Promise::new(self.owner.clone()).transfer(NearToken::from_yoctonear(withdraw))
    }

    pub fn get_dataset(&self, dataset_id: String) -> Dataset {
        self.dataset(&dataset_id)
    }

    pub fn get_computation(&self, computation_id: String) -> Computation {
        self.computation(&computation_id)
    }

    pub fn get_query(&self, query_id: u64) -> Query {
        match self.queries.get(&query_id) {
            Some(query) => query.clone(),
            None => env::panic_str("query not found"),
        }
    }

    pub fn get_budget(&self, agent: AccountId, dataset_id: String) -> Budget {
        let key = budget_key(&agent, &dataset_id);
        match self.budgets.get(&key) {
            Some(budget) => budget.clone(),
            None => Budget { day: 0, count: 0 },
        }
    }

    fn dataset(&self, dataset_id: &str) -> Dataset {
        match self.datasets.get(dataset_id) {
            Some(dataset) => dataset.clone(),
            None => env::panic_str("dataset not found"),
        }
    }

    fn computation(&self, computation_id: &str) -> Computation {
        match self.computations.get(computation_id) {
            Some(computation) => computation.clone(),
            None => env::panic_str("computation not found"),
        }
    }

    fn charge_budget(&mut self, agent: &AccountId, dataset_id: &str) {
        let day = env::block_timestamp() / 86_400_000_000_000;
        let key = budget_key(agent, dataset_id);
        let budget = self.budgets.entry(key).or_insert(Budget { day, count: 0 });
        if budget.day != day {
            budget.day = day;
            budget.count = 0;
        }
        if budget.count >= MAX_QUERIES_PER_DAY {
            env::panic_str("daily privacy budget exceeded");
        }
        budget.count += 1;
    }
}

fn budget_key(agent: &AccountId, dataset_id: &str) -> String {
    format!("{}:{}", agent, dataset_id)
}

fn build_input(dataset: &Dataset, computation: &Computation, params: &str) -> Value {
    let mut input: Value = near_sdk::serde_json::from_str(params).unwrap_or(Value::Null);
    if !input.is_object() {
        input = json!({});
    }
    let object = input.as_object_mut().unwrap();
    object.insert(
        "operation".to_string(),
        json!(computation.operation.clone()),
    );
    object.insert("version".to_string(), json!(computation.version.clone()));
    object.insert(
        "expected_sha256".to_string(),
        json!(dataset.data_hash.clone()),
    );
    input
}

#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::test_utils::{get_logs, VMContextBuilder};
    use near_sdk::testing_env;

    const DATA_HASH: &str = "65a10103f741129dc4270d267e694e341efd8b3a4b8ebdf06e97d73bc08b1983";
    const WASM_HASH: &str = "0f20f00ce9c9caf451e47e88276901ebe9329e10c15c60e27479da161c2416ba";

    fn account(id: &str) -> AccountId {
        id.parse().unwrap()
    }

    fn setup() -> (SealQuery, AccountId) {
        let owner = account("owner.testnet");
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(owner.clone())
            .build());
        (SealQuery::new(owner.clone()), owner)
    }

    fn register_dataset(contract: &mut SealQuery, owner: &AccountId) {
        contract.register_dataset(
            "retail_v1".to_string(),
            DATA_HASH.to_string(),
            vec!["spend_growth".to_string()],
            U128(20_000_000_000_000_000_000_000),
            U128(10_000_000_000_000_000_000_000),
            U128(10_000_000_000_000_000_000_000),
        );
        assert_eq!(contract.get_dataset("retail_v1".to_string()).owner, *owner);
    }

    fn register_computation(contract: &mut SealQuery, owner: &AccountId) {
        contract.register_computation(
            "spend_growth_v1".to_string(),
            "retail_v1".to_string(),
            "owner.testnet/sealquery-approved".to_string(),
            WASM_HASH.to_string(),
            "spend_growth".to_string(),
            "retail_v1".to_string(),
            "compute".to_string(),
            owner.clone(),
        );
    }

    #[test]
    fn registers_dataset_and_emits_event() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        assert!(get_logs()
            .iter()
            .any(|log| log.contains("dataset_registered")));
    }

    #[test]
    fn quote_returns_dataset_and_computation() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        register_computation(&mut contract, &owner);
        let quote = contract.quote("retail_v1".to_string(), "spend_growth_v1".to_string());
        assert_eq!(quote["dataset_id"], "retail_v1");
        assert_eq!(quote["computation_id"], "spend_growth_v1");
    }

    #[test]
    #[should_panic(expected = "only the dataset owner can register computations")]
    fn rejects_computation_from_non_owner() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(account("attacker.testnet"))
            .build());
        register_computation(&mut contract, &account("attacker.testnet"));
    }

    #[test]
    fn updates_dataset_economics_for_owner() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        contract.update_dataset_economics(
            "retail_v1".to_string(),
            U128(30_000_000_000_000_000_000_000),
            U128(12_000_000_000_000_000_000_000),
            U128(15_000_000_000_000_000_000_000),
        );
        let dataset = contract.get_dataset("retail_v1".to_string());
        assert_eq!(dataset.price_yocto.0, 30_000_000_000_000_000_000_000);
    }

    #[test]
    fn build_input_binds_dataset_and_operation() {
        let (contract, owner) = setup();
        let mut contract = contract;
        register_dataset(&mut contract, &owner);
        let dataset = contract.get_dataset("retail_v1".to_string());
        let computation = Computation {
            dataset_id: "retail_v1".to_string(),
            outlayer_project_id: "owner.testnet/sealquery-approved".to_string(),
            wasm_hash: WASM_HASH.to_string(),
            operation: "spend_growth".to_string(),
            version: "retail_v1".to_string(),
            secret_profile: "compute".to_string(),
            secret_account: owner,
        };
        let input = build_input(&dataset, &computation, r#"{"period_a":"2011-11"}"#);
        assert_eq!(input["operation"], "spend_growth");
        assert_eq!(input["version"], "retail_v1");
        assert_eq!(input["expected_sha256"], DATA_HASH);
        assert_eq!(input["period_a"], "2011-11");
    }

    #[test]
    #[should_panic(expected = "daily privacy budget exceeded")]
    fn budget_rejects_after_limit() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        let agent = account("agent.testnet");
        testing_env!(VMContextBuilder::new()
            .block_timestamp(86_400_000_000_000)
            .build());
        for _ in 0..MAX_QUERIES_PER_DAY {
            contract.charge_budget(&agent, "retail_v1");
        }
        contract.charge_budget(&agent, "retail_v1");
    }
    #[test]
    fn version_is_exposed() {
        assert_eq!(SealQuery::version(), "0.1.0");
    }

    #[test]
    fn updates_computation_for_owner() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        register_computation(&mut contract, &owner);
        contract.update_computation(
            "spend_growth_v1".to_string(),
            "owner.testnet/sealquery-approved-v2".to_string(),
            "aa".repeat(32),
            "spend_growth".to_string(),
            "retail_v1".to_string(),
            "compute".to_string(),
            owner,
        );
        let computation = contract.get_computation("spend_growth_v1".to_string());
        assert_eq!(
            computation.outlayer_project_id,
            "owner.testnet/sealquery-approved-v2"
        );
    }
}
