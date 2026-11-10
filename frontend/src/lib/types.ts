export type Dataset = {
  owner: string;
  version: string;
  data_hash: string;
  allowed_computations: string[];
  price_yocto: string;
  compute_deposit_yocto: string;
  reward_yocto: string;
  budget_per_day: number;
};

export type Computation = {
  dataset_id: string;
  operation: string;
  outlayer_project_id: string;
  wasm_hash: string;
  secret_profile: string;
  secret_account: string;
};

export type Quote = {
  dataset_id: string;
  computation_id: string;
  dataset_version: string;
  operation: string;
  price_yocto: string;
  compute_deposit_yocto: string;
  reward_yocto: string;
  budget_per_day: number;
};

export type Budget = {
  day: number;
  count: number;
};

export type DatasetState = {
  dataset_id: string;
  computation_id: string;
  dataset: Dataset;
  computation: Computation;
  quote: Quote;
  budget: Budget;
  error?: string;
};

export type QueryStatus = "requested" | "ready" | "settled" | "failed" | "refunded";

export type QueryRecord = {
  query_id: number;
  agent: string;
  dataset_id: string;
  computation_id: string;
  status: QueryStatus | string;
  result: string | null;
  deposit_yocto: string;
  created_block: number;
  tx_hash?: string | null;
  accept_tx?: string | null;
  refund_tx?: string | null;
  error?: string;
};

export type State = {
  contract: string;
  agent: string;
  paused: boolean;
  protocol_fee_bps: number;
  datasets: DatasetState[];
  recent_queries: QueryRecord[];
};

export type MetricAlert = {
  severity: "critical" | "warning" | "info";
  code: string;
  message: string;
};

export type Metrics = {
  ok: boolean;
  generated_at: string;
  contract: string;
  agent: string;
  paused: boolean;
  protocol_fee_bps: number;
  queries: {
    recent: number;
    by_status: Record<string, number>;
    recent_success_rate: number | null;
  };
  datasets: Array<{
    dataset_id: string;
    computation_id: string;
    owner: string;
    used: number;
    limit: number;
    exhausted: boolean;
  }>;
  balances: {
    agent: string | null;
    contract: string | null;
  };
  alerts: MetricAlert[];
};

export type AggregateRow = {
  country: string;
  spend_a: number;
  spend_b: number;
  growth_pct: number;
  cohort_a: string;
  cohort_b: string;
};

export type AggregateResult = {
  ok?: boolean;
  dataset_sha256?: string;
  min_cohort_size?: number;
  operation?: string;
  period_a?: string;
  period_b?: string;
  version?: string;
  results?: AggregateRow[];
};

export type ProofCheck = {
  verdict: string;
  detail: string;
};

export type AttestationReport = {
  task_id: number;
  task_type: string;
  timestamp: number;
  format: string;
  authenticity: ProofCheck;
  identity: ProofCheck;
  binding: ProofCheck;
  input: ProofCheck;
  output: ProofCheck;
  tcb_status: string;
  measurements: {
    mrtd: string;
    rtmr0: string;
    rtmr1: string;
    rtmr2: string;
    rtmr3: string;
  };
  collateral?: {
    fmspc?: string;
    valid_from?: string;
    valid_until?: string;
    contract_id?: string;
    source?: string;
    api_copy_matches_chain?: boolean;
  };
  report_data_prefix?: string;
  expected_task_hash?: string;
  input_hash_computed?: string;
  output_hash_computed?: string;
};

export type QueryRunResponse = {
  ok: boolean;
  dataset_id: string;
  computation_id: string;
  query_id: number;
  tx_hash: string;
  status: QueryStatus;
  result: AggregateResult | string | null;
  proof: boolean;
  proof_output: string;
  accept_tx: string | null;
  refund_tx: string | null;
  owner: string;
  owner_before: string | null;
  owner_after: string | null;
  error?: string;
};

export type Health = {
  ok: boolean;
  contract: string;
  agent: string;
  machine_auth: boolean;
};


export type JobStatus =
  | "queued"
  | "running"
  | "ready"
  | "settled"
  | "refunded"
  | "failed"
  | "error";

export type JobResponse = {
  ok: boolean;
  job_id: string;
  dataset_id: string;
  computation_id: string;
  status: JobStatus;
  query_id: number | null;
  tx_hash: string | null;
  accept_tx: string | null;
  refund_tx: string | null;
  result: AggregateResult | string | null;
  proof: boolean;
  proof_output: string;
  owner: string | null;
  owner_before: string | null;
  owner_after: string | null;
  error: string | null;
  attempts: number;
  created_at: string | null;
  updated_at: string | null;
};
