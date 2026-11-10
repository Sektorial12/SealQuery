use std::collections::BTreeMap;

use near_sdk::json_types::U128;
use near_sdk::serde_json::{json, Value};
use near_sdk::{env, near, AccountId, Gas, NearToken, PanicOnDefault, Promise};

const OUTLAYER_ACCOUNT: &str = "outlayer.testnet";
const MAX_QUERIES_PER_DAY: u32 = 1_000;
const QUERY_TIMEOUT_BLOCKS: u64 = 200;
const DEFAULT_LIST_LIMIT: usize = 50;

#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct Dataset {
    pub owner: AccountId,
    pub version: String,
    pub data_hash: String,
    pub allowed_computations: Vec<String>,
    pub price_yocto: U128,
    pub compute_deposit_yocto: U128,
    pub reward_yocto: U128,
    pub budget_per_day: u32,
}

#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct Computation {
    pub dataset_id: String,
    pub outlayer_project_id: String,
    pub wasm_hash: String,
    pub operation: String,
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
    paused: bool,
    protocol_fee_bps: u16,
    protocol_fees_yocto: u128,
    datasets: BTreeMap<String, Dataset>,
    computations: BTreeMap<String, Computation>,
    queries: BTreeMap<u64, Query>,
    budgets: BTreeMap<String, Budget>,
    queries_by_agent: BTreeMap<AccountId, Vec<u64>>,
    queries_by_dataset: BTreeMap<String, Vec<u64>>,
    next_query_id: u64,
}

#[near]
impl SealQuery {
    #[init]
    pub fn new(owner: AccountId) -> Self {
        Self {
            owner,
            paused: false,
            protocol_fee_bps: 0,
            protocol_fees_yocto: 0,
            datasets: BTreeMap::new(),
            computations: BTreeMap::new(),
            queries: BTreeMap::new(),
            budgets: BTreeMap::new(),
            queries_by_agent: BTreeMap::new(),
            queries_by_dataset: BTreeMap::new(),
            next_query_id: 1,
        }
    }

    pub fn version() -> String {
        env!("CARGO_PKG_VERSION").to_string()
    }

    pub fn get_owner(&self) -> AccountId {
        self.owner.clone()
    }

    pub fn set_paused(&mut self, paused: bool) {
        self.assert_owner();
        self.paused = paused;
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "2.0.0",
                "event": "paused_changed",
                "data": [{"paused": paused}],
            })
        ));
    }

    pub fn get_paused(&self) -> bool {
        self.paused
    }

    pub fn set_protocol_fee_bps(&mut self, bps: u16) {
        self.assert_owner();
        if bps > 1_000 {
            env::panic_str("protocol fee cannot exceed 10%");
        }
        if self.next_query_id > 1 {
            env::panic_str("cannot change protocol fee after queries");
        }
        self.protocol_fee_bps = bps;
    }

    pub fn get_protocol_fee_bps(&self) -> u16 {
        self.protocol_fee_bps
    }

    pub fn get_protocol_fees(&self) -> U128 {
        U128(self.protocol_fees_yocto)
    }

    pub fn withdraw_protocol_fees(&mut self) -> Promise {
        self.assert_owner();
        let amount = self.protocol_fees_yocto;
        self.protocol_fees_yocto = 0;
        Promise::new(self.owner.clone()).transfer(NearToken::from_yoctonear(amount))
    }

    #[allow(clippy::too_many_arguments)]
    #[payable]
    pub fn register_dataset(
        &mut self,
        dataset_id: String,
        version: String,
        data_hash: String,
        allowed_computations: Vec<String>,
        price_yocto: U128,
        compute_deposit_yocto: U128,
        reward_yocto: U128,
        budget_per_day: u32,
    ) {
        self.assert_owner();
        let caller = env::predecessor_account_id();
        if self.datasets.contains_key(&dataset_id) {
            env::panic_str("dataset already exists");
        }
        validate_version(&version);
        validate_hash(&data_hash);
        if allowed_computations.is_empty() {
            env::panic_str("at least one computation must be allowed");
        }
        if reward_yocto.0.saturating_add(compute_deposit_yocto.0) > price_yocto.0 {
            env::panic_str("reward plus compute deposit must not exceed price");
        }
        if budget_per_day == 0 || budget_per_day > MAX_QUERIES_PER_DAY {
            env::panic_str("budget_per_day must be between 1 and 1000");
        }
        self.datasets.insert(
            dataset_id.clone(),
            Dataset {
                owner: caller.clone(),
                version,
                data_hash,
                allowed_computations,
                price_yocto,
                compute_deposit_yocto,
                reward_yocto,
                budget_per_day,
            },
        );
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "2.0.0",
                "event": "dataset_registered",
                "data": [{"dataset_id": dataset_id, "owner": caller}],
            })
        ));
    }

    pub fn remove_dataset(&mut self, dataset_id: String) {
        self.assert_owner();
        self.dataset(&dataset_id);
        if let Some(ids) = self.queries_by_dataset.get(&dataset_id) {
            for query_id in ids {
                if let Some(query) = self.queries.get(query_id) {
                    if query.status == "pending" || query.status == "ready" {
                        env::panic_str("cannot remove a dataset with open queries");
                    }
                }
            }
        }
        self.datasets.remove(&dataset_id);
        self.computations
            .retain(|_, computation| computation.dataset_id != dataset_id);
        self.queries_by_dataset.remove(&dataset_id);
        self.budgets
            .retain(|key, _| !key.ends_with(&format!(":{dataset_id}")));
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "2.0.0",
                "event": "dataset_removed",
                "data": [{"dataset_id": dataset_id}],
            })
        ));
    }

    pub fn reset_budget(&mut self, agent: AccountId, dataset_id: String) {
        self.assert_owner();
        self.budgets.remove(&budget_key(&agent, &dataset_id));
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "2.0.0",
                "event": "budget_reset",
                "data": [{"agent": agent, "dataset_id": dataset_id}],
            })
        ));
    }

    pub fn rotate_dataset(
        &mut self,
        dataset_id: String,
        new_version: String,
        new_data_hash: String,
    ) {
        let caller = env::predecessor_account_id();
        let mut dataset = self.dataset(&dataset_id);
        if dataset.owner != caller {
            env::panic_str("only the dataset owner can rotate");
        }
        validate_version(&new_version);
        validate_hash(&new_data_hash);
        if dataset.version == new_version {
            env::panic_str("new version must differ");
        }
        dataset.version = new_version.clone();
        dataset.data_hash = new_data_hash.clone();
        self.datasets.insert(dataset_id.clone(), dataset);
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "2.0.0",
                "event": "dataset_rotated",
                "data": [{"dataset_id": dataset_id, "version": new_version, "data_hash": new_data_hash}],
            })
        ));
    }

    pub fn update_dataset_economics(
        &mut self,
        dataset_id: String,
        price_yocto: U128,
        compute_deposit_yocto: U128,
        reward_yocto: U128,
        budget_per_day: u32,
    ) {
        let caller = env::predecessor_account_id();
        let mut dataset = self.dataset(&dataset_id);
        if dataset.owner != caller {
            env::panic_str("only the dataset owner can update economics");
        }
        if reward_yocto.0.saturating_add(compute_deposit_yocto.0) > price_yocto.0 {
            env::panic_str("reward plus compute deposit must not exceed price");
        }
        if self
            .queries_by_dataset
            .get(&dataset_id)
            .map(|ids| !ids.is_empty())
            .unwrap_or(false)
        {
            env::panic_str("cannot change economics after queries");
        }
        if budget_per_day == 0 || budget_per_day > MAX_QUERIES_PER_DAY {
            env::panic_str("budget_per_day must be between 1 and 1000");
        }
        dataset.price_yocto = price_yocto;
        dataset.compute_deposit_yocto = compute_deposit_yocto;
        dataset.reward_yocto = reward_yocto;
        dataset.budget_per_day = budget_per_day;
        self.datasets.insert(dataset_id, dataset);
    }

    #[allow(clippy::too_many_arguments)]
    pub fn register_computation(
        &mut self,
        computation_id: String,
        dataset_id: String,
        outlayer_project_id: String,
        wasm_hash: String,
        operation: String,
        secret_profile: String,
        secret_account: AccountId,
    ) {
        let caller = env::predecessor_account_id();
        let dataset = self.dataset(&dataset_id);
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
        if self.computations.contains_key(&computation_id) {
            env::panic_str("computation already exists");
        }
        validate_hash(&wasm_hash);
        self.computations.insert(
            computation_id.clone(),
            Computation {
                dataset_id,
                outlayer_project_id,
                wasm_hash,
                operation,
                secret_profile,
                secret_account,
            },
        );
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "2.0.0",
                "event": "computation_registered",
                "data": [{"computation_id": computation_id}],
            })
        ));
    }

    pub fn update_computation(
        &mut self,
        computation_id: String,
        outlayer_project_id: String,
        wasm_hash: String,
        operation: String,
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
        validate_hash(&wasm_hash);
        computation.outlayer_project_id = outlayer_project_id;
        computation.wasm_hash = wasm_hash;
        computation.operation = operation;
        computation.secret_profile = secret_profile;
        computation.secret_account = secret_account;
        self.computations.insert(computation_id, computation);
    }

    pub fn quote(&self, dataset_id: String, computation_id: String) -> Value {
        let dataset = self.dataset(&dataset_id);
        let computation = self.computation(&computation_id);
        json!({
            "dataset_id": dataset_id,
            "computation_id": computation_id,
            "dataset_version": dataset.version,
            "price_yocto": dataset.price_yocto,
            "reward_yocto": dataset.reward_yocto,
            "compute_deposit_yocto": dataset.compute_deposit_yocto,
            "budget_per_day": dataset.budget_per_day,
            "operation": computation.operation,
        })
    }

    #[payable]
    pub fn request_query(
        &mut self,
        dataset_id: String,
        computation_id: String,
        params: String,
    ) -> Promise {
        if self.paused {
            env::panic_str("contract is paused");
        }
        let agent = env::predecessor_account_id();
        let dataset = self.dataset(&dataset_id);
        let computation = self.computation(&computation_id);
        if computation.dataset_id != dataset_id {
            env::panic_str("computation does not belong to dataset");
        }
        if env::attached_deposit().as_yoctonear() != dataset.price_yocto.0 {
            env::panic_str("attach the exact query price");
        }
        self.charge_budget(&agent, &dataset_id, dataset.budget_per_day);

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
        self.queries_by_agent
            .entry(agent.clone())
            .or_default()
            .push(query_id);
        self.queries_by_dataset
            .entry(dataset_id.clone())
            .or_default()
            .push(query_id);

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
                "version": "2.0.0",
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
        match self.queries.get(&query_id) {
            Some(query) if query.status == "pending" => {}
            _ => {
                env::log_str("query callback ignored for non-pending query");
                return;
            }
        }
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
                "version": "2.0.0",
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
        self.settle(query_id, &query.dataset_id)
    }

    pub fn settle_query(&mut self, query_id: u64) -> Promise {
        let query = match self.queries.get(&query_id) {
            Some(query) => query.clone(),
            None => env::panic_str("query not found"),
        };
        if query.status != "ready" {
            env::panic_str("query result is not ready");
        }
        let timed_out = env::block_height() > query.created_block + QUERY_TIMEOUT_BLOCKS;
        if !timed_out {
            env::panic_str("query has not timed out");
        }
        self.settle(query_id, &query.dataset_id)
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
        if query.status == "ready" {
            env::panic_str("ready query must be settled, not refunded");
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
            stored.result = None;
        }
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "2.0.0",
                "event": "query_refunded",
                "data": [{"query_id": query_id, "agent": query.agent, "amount_yocto": query.deposit_yocto}],
            })
        ));
        Promise::new(query.agent).transfer(NearToken::from_yoctonear(query.deposit_yocto.0))
    }

    fn settle(&mut self, query_id: u64, dataset_id: &str) -> Promise {
        let dataset = self.dataset(dataset_id);
        if let Some(stored) = self.queries.get_mut(&query_id) {
            stored.status = "settled".to_string();
        }
        let fee = dataset.reward_yocto.0 * self.protocol_fee_bps as u128 / 10_000;
        let payout = dataset.reward_yocto.0.saturating_sub(fee);
        self.protocol_fees_yocto += fee;
        env::log_str(&format!(
            "EVENT_JSON:{}",
            json!({
                "standard": "sealquery",
                "version": "2.0.0",
                "event": "query_settled",
                "data": [{"query_id": query_id, "dataset_owner": dataset.owner, "payout_yocto": U128(payout), "protocol_fee_yocto": U128(fee)}],
            })
        ));
        Promise::new(dataset.owner).transfer(NearToken::from_yoctonear(payout))
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

    pub fn get_queries_for_agent(
        &self,
        agent: AccountId,
        from_index: Option<u64>,
        limit: Option<u64>,
    ) -> Vec<u64> {
        page(
            self.queries_by_agent.get(&agent),
            from_index.unwrap_or(0) as usize,
            limit.unwrap_or(DEFAULT_LIST_LIMIT as u64) as usize,
        )
    }

    pub fn get_queries_for_dataset(
        &self,
        dataset_id: String,
        from_index: Option<u64>,
        limit: Option<u64>,
    ) -> Vec<u64> {
        page(
            self.queries_by_dataset.get(&dataset_id),
            from_index.unwrap_or(0) as usize,
            limit.unwrap_or(DEFAULT_LIST_LIMIT as u64) as usize,
        )
    }

    pub fn list_datasets(&self, from_index: Option<u64>, limit: Option<u64>) -> Vec<String> {
        let keys: Vec<String> = self.datasets.keys().cloned().collect();
        page(
            Some(&keys),
            from_index.unwrap_or(0) as usize,
            limit.unwrap_or(DEFAULT_LIST_LIMIT as u64) as usize,
        )
    }

    pub fn list_computations(
        &self,
        dataset_id: Option<String>,
        from_index: Option<u64>,
        limit: Option<u64>,
    ) -> Vec<String> {
        let keys: Vec<String> = self
            .computations
            .iter()
            .filter(|(_, computation)| {
                dataset_id
                    .as_ref()
                    .map(|id| &computation.dataset_id == id)
                    .unwrap_or(true)
            })
            .map(|(id, _)| id.clone())
            .collect();
        page(
            Some(&keys),
            from_index.unwrap_or(0) as usize,
            limit.unwrap_or(DEFAULT_LIST_LIMIT as u64) as usize,
        )
    }

    pub fn get_dataset_count(&self) -> u64 {
        self.datasets.len() as u64
    }

    pub fn get_computation_count(&self) -> u64 {
        self.computations.len() as u64
    }

    pub fn get_query_count(&self) -> u64 {
        self.queries.len() as u64
    }

    fn assert_owner(&self) {
        if env::predecessor_account_id() != self.owner {
            env::panic_str("only the contract owner can call this");
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

    fn charge_budget(&mut self, agent: &AccountId, dataset_id: &str, limit: u32) {
        let day = env::block_timestamp() / 86_400_000_000_000;
        let key = budget_key(agent, dataset_id);
        let budget = self.budgets.entry(key).or_insert(Budget { day, count: 0 });
        if budget.day != day {
            budget.day = day;
            budget.count = 0;
        }
        if budget.count >= limit {
            env::panic_str("daily privacy budget exceeded");
        }
        budget.count += 1;
    }
}

fn budget_key(agent: &AccountId, dataset_id: &str) -> String {
    format!("{}:{}", agent, dataset_id)
}

fn validate_version(version: &str) {
    if version.is_empty() || version.len() > 64 {
        env::panic_str("version must be 1-64 characters");
    }
    if !version
        .bytes()
        .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-' || byte == b'_')
    {
        env::panic_str("version may contain only letters, digits, '-' and '_'");
    }
}

fn validate_hash(hash: &str) {
    if hash.len() != 64
        || !hash
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        env::panic_str("hash must be 64 lowercase hex characters");
    }
}

fn page<T: Clone>(items: Option<&Vec<T>>, from_index: usize, limit: usize) -> Vec<T> {
    match items {
        Some(items) => items.iter().skip(from_index).take(limit).cloned().collect(),
        None => Vec::new(),
    }
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
    object.insert("version".to_string(), json!(dataset.version.clone()));
    object.insert(
        "expected_sha256".to_string(),
        json!(dataset.data_hash.clone()),
    );
    input
}

#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::test_utils::VMContextBuilder;
    use near_sdk::testing_env;
    use near_sdk::PromiseResult;

    const DATA_HASH: &str = "65a10103f741129dc4270d267e694e341efd8b3a4b8ebdf06e97d73bc08b1983";
    const WASM_HASH: &str = "3b1bc4eaabcde79492959f8ac34e47173f11b358ca06b31f1694053494acca47";

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
            "retail_v1".to_string(),
            DATA_HASH.to_string(),
            vec!["spend_growth".to_string()],
            U128(20_000_000_000_000_000_000_000),
            U128(10_000_000_000_000_000_000_000),
            U128(10_000_000_000_000_000_000_000),
            20,
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
            "compute".to_string(),
            owner.clone(),
        );
    }

    fn ready_query(contract: &mut SealQuery, agent: &AccountId) {
        contract.queries.insert(
            1,
            Query {
                agent: agent.clone(),
                dataset_id: "retail_v1".to_string(),
                computation_id: "spend_growth_v1".to_string(),
                deposit_yocto: U128(20_000_000_000_000_000_000_000),
                status: "ready".to_string(),
                result: Some("{}".to_string()),
                created_block: 0,
            },
        );
    }

    #[test]
    fn registers_dataset_and_emits_event() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        assert_eq!(contract.get_dataset_count(), 1);
        assert_eq!(
            contract.get_dataset("retail_v1".to_string()).version,
            "retail_v1"
        );
    }

    #[test]
    fn quote_includes_version_and_economics() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        register_computation(&mut contract, &owner);
        let quote = contract.quote("retail_v1".to_string(), "spend_growth_v1".to_string());
        assert_eq!(quote["dataset_version"], "retail_v1");
        assert_eq!(quote["budget_per_day"], 20);
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
    fn rotates_dataset_version_and_hash() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        contract.rotate_dataset(
            "retail_v1".to_string(),
            "retail_v2".to_string(),
            "aa".repeat(32),
        );
        let dataset = contract.get_dataset("retail_v1".to_string());
        assert_eq!(dataset.version, "retail_v2");
        assert_eq!(dataset.data_hash, "aa".repeat(32));
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
            5,
        );
        let dataset = contract.get_dataset("retail_v1".to_string());
        assert_eq!(dataset.price_yocto.0, 30_000_000_000_000_000_000_000);
        assert_eq!(dataset.budget_per_day, 5);
    }

    #[test]
    fn build_input_binds_dataset_version_and_operation() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        let dataset = contract.get_dataset("retail_v1".to_string());
        let computation = Computation {
            dataset_id: "retail_v1".to_string(),
            outlayer_project_id: "owner.testnet/sealquery-approved".to_string(),
            wasm_hash: WASM_HASH.to_string(),
            operation: "spend_growth".to_string(),
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
    fn budget_rejects_after_dataset_limit() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        let agent = account("agent.testnet");
        testing_env!(VMContextBuilder::new()
            .block_timestamp(86_400_000_000_000)
            .build());
        for _ in 0..20 {
            contract.charge_budget(&agent, "retail_v1", 20);
        }
        contract.charge_budget(&agent, "retail_v1", 20);
    }

    #[test]
    fn owner_can_pause_and_unpause() {
        let (mut contract, owner) = setup();
        contract.set_paused(true);
        assert!(contract.get_paused());
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(owner)
            .build());
        contract.set_paused(false);
        assert!(!contract.get_paused());
    }

    #[test]
    fn settles_with_protocol_fee() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        register_computation(&mut contract, &owner);
        contract.set_protocol_fee_bps(500);
        let agent = account("agent.testnet");
        ready_query(&mut contract, &agent);
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(agent)
            .build());
        let _ = contract.accept_result(1);
        assert_eq!(contract.get_query(1).status, "settled");
        assert_eq!(contract.protocol_fees_yocto, 500_000_000_000_000_000_000);
    }

    #[test]
    fn late_callback_does_not_overwrite_refunded_query() {
        let (mut contract, _owner) = setup();
        contract.queries.insert(
            1,
            Query {
                agent: account("agent.testnet"),
                dataset_id: "retail_v1".to_string(),
                computation_id: "spend_growth_v1".to_string(),
                deposit_yocto: U128(20_000_000_000_000_000_000_000),
                status: "refunded".to_string(),
                result: None,
                created_block: 0,
            },
        );
        testing_env!(
            VMContextBuilder::new().build(),
            near_sdk::test_vm_config(),
            near_sdk::RuntimeFeesConfig::test(),
            Default::default(),
            vec![PromiseResult::Successful(br#"{"ok":true}"#.to_vec())],
        );
        contract.on_query_result(1);
        assert_eq!(contract.get_query(1).status, "refunded");
    }

    #[test]
    fn late_callback_does_not_overwrite_settled_query() {
        let (mut contract, _owner) = setup();
        contract.queries.insert(
            1,
            Query {
                agent: account("agent.testnet"),
                dataset_id: "retail_v1".to_string(),
                computation_id: "spend_growth_v1".to_string(),
                deposit_yocto: U128(20_000_000_000_000_000_000_000),
                status: "settled".to_string(),
                result: Some("{}".to_string()),
                created_block: 0,
            },
        );
        testing_env!(
            VMContextBuilder::new().build(),
            near_sdk::test_vm_config(),
            near_sdk::RuntimeFeesConfig::test(),
            Default::default(),
            vec![PromiseResult::Successful(br#"{"ok":true}"#.to_vec())],
        );
        contract.on_query_result(1);
        assert_eq!(contract.get_query(1).status, "settled");
    }

    #[test]
    #[should_panic(expected = "computation already exists")]
    fn rejects_duplicate_computation_id() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        register_computation(&mut contract, &owner);
        register_computation(&mut contract, &owner);
    }

    #[test]
    #[should_panic(expected = "reward plus compute deposit must not exceed price")]
    fn rejects_economics_that_exceed_price() {
        let (mut contract, _owner) = setup();
        contract.register_dataset(
            "retail_v1".to_string(),
            "retail_v1".to_string(),
            DATA_HASH.to_string(),
            vec!["spend_growth".to_string()],
            U128(20_000_000_000_000_000_000_000),
            U128(10_000_000_000_000_000_000_000),
            U128(11_000_000_000_000_000_000_000),
            20,
        );
    }

    #[test]
    #[should_panic(expected = "cannot change economics after queries")]
    fn rejects_economics_change_after_query() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        contract
            .queries_by_dataset
            .insert("retail_v1".to_string(), vec![1]);
        contract.update_dataset_economics(
            "retail_v1".to_string(),
            U128(20_000_000_000_000_000_000_000),
            U128(10_000_000_000_000_000_000_000),
            U128(10_000_000_000_000_000_000_000),
            20,
        );
    }

    #[test]
    #[should_panic(expected = "only the contract owner can call this")]
    fn rejects_dataset_registration_from_non_owner() {
        let (mut contract, _owner) = setup();
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(account("attacker.testnet"))
            .build());
        register_dataset(&mut contract, &account("attacker.testnet"));
    }

    #[test]
    #[should_panic(expected = "ready query must be settled, not refunded")]
    fn rejects_refund_of_ready_query_after_timeout() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        let agent = account("agent.testnet");
        ready_query(&mut contract, &agent);
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(agent)
            .block_height(1_000)
            .build());
        let _ = contract.refund_query(1);
    }

    #[test]
    fn refunds_pending_query_after_timeout() {
        let (mut contract, _owner) = setup();
        let agent = account("agent.testnet");
        contract.queries.insert(
            1,
            Query {
                agent: agent.clone(),
                dataset_id: "retail_v1".to_string(),
                computation_id: "spend_growth_v1".to_string(),
                deposit_yocto: U128(20_000_000_000_000_000_000_000),
                status: "pending".to_string(),
                result: None,
                created_block: 0,
            },
        );
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(agent)
            .block_height(201)
            .build());
        let _ = contract.refund_query(1);
        assert_eq!(contract.get_query(1).status, "refunded");
    }

    #[test]
    fn refunds_failed_query() {
        let (mut contract, _owner) = setup();
        let agent = account("agent.testnet");
        contract.queries.insert(
            1,
            Query {
                agent: agent.clone(),
                dataset_id: "retail_v1".to_string(),
                computation_id: "spend_growth_v1".to_string(),
                deposit_yocto: U128(20_000_000_000_000_000_000_000),
                status: "failed".to_string(),
                result: None,
                created_block: 0,
            },
        );
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(agent)
            .build());
        let _ = contract.refund_query(1);
        assert_eq!(contract.get_query(1).status, "refunded");
    }

    #[test]
    fn failed_callback_marks_query_failed() {
        let (mut contract, _owner) = setup();
        contract.queries.insert(
            1,
            Query {
                agent: account("agent.testnet"),
                dataset_id: "retail_v1".to_string(),
                computation_id: "spend_growth_v1".to_string(),
                deposit_yocto: U128(20_000_000_000_000_000_000_000),
                status: "pending".to_string(),
                result: None,
                created_block: 0,
            },
        );
        testing_env!(
            VMContextBuilder::new().build(),
            near_sdk::test_vm_config(),
            near_sdk::RuntimeFeesConfig::test(),
            Default::default(),
            vec![PromiseResult::Failed],
        );
        contract.on_query_result(1);
        assert_eq!(contract.get_query(1).status, "failed");
    }

    #[test]
    fn settles_ready_query_after_timeout() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        let agent = account("agent.testnet");
        ready_query(&mut contract, &agent);
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(account("settler.testnet"))
            .block_height(201)
            .build());
        let _ = contract.settle_query(1);
        assert_eq!(contract.get_query(1).status, "settled");
    }

    #[test]
    #[should_panic(expected = "query result is not ready")]
    fn rejects_accept_replay() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        let agent = account("agent.testnet");
        ready_query(&mut contract, &agent);
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(agent)
            .build());
        let _ = contract.accept_result(1);
        let _ = contract.accept_result(1);
    }

    #[test]
    #[should_panic(expected = "cannot change protocol fee after queries")]
    fn rejects_protocol_fee_change_after_query() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        contract.next_query_id = 2;
        contract.set_protocol_fee_bps(100);
    }

    #[test]
    fn owner_can_reset_budget_and_remove_dataset() {
        let (mut contract, owner) = setup();
        register_dataset(&mut contract, &owner);
        register_computation(&mut contract, &owner);
        let agent = account("agent.testnet");
        testing_env!(VMContextBuilder::new()
            .block_timestamp(86_400_000_000_000)
            .build());
        contract.charge_budget(&agent, "retail_v1", 20);
        testing_env!(VMContextBuilder::new()
            .predecessor_account_id(owner)
            .build());
        contract.reset_budget(agent.clone(), "retail_v1".to_string());
        assert_eq!(contract.get_budget(agent, "retail_v1".to_string()).count, 0);
        contract.remove_dataset("retail_v1".to_string());
        assert_eq!(contract.get_dataset_count(), 0);
        assert_eq!(contract.get_computation_count(), 0);
    }

    #[test]
    fn version_is_exposed() {
        assert_eq!(SealQuery::version(), "0.2.2");
    }
}
