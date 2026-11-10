"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowUpRight, Check, CircleDashed, Play, ShieldAlert } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { AttestationCard } from "@/components/attestation-card";
import { DatasetTile } from "@/components/dataset-card";
import { api } from "@/lib/api";
import { explorerTx, formatNear, parseResult, short } from "@/lib/format";
import type { AggregateRow, DatasetState, JobResponse, QueryRunResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

export function QueryConsole() {
  const queryClient = useQueryClient();
  const { data: state, isLoading, error } = useQuery({
    queryKey: ["state"],
    queryFn: api.state,
    refetchInterval: 15_000,
  });
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);

  const datasets = state?.datasets ?? [];
  const selected = datasets[selectedIndex] ?? datasets[0];

  const mutation = useMutation({
    mutationFn: api.runQuery,
    onSuccess: (data) => setJobId(data.job_id),
  });

  const { data: job, error: jobError } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.job(jobId!),
    enabled: Boolean(jobId),
    retry: 1,
    refetchInterval: (query) => {
      const value = query.state.data;
      return value && terminalStatuses.includes(value.status) ? false : 3000;
    },
  });

  const terminal = job ? terminalStatuses.includes(job.status) : false;
  const result = useMemo<QueryRunResponse | null>(
    () => (job && terminal ? jobToResult(job) : null),
    [job, terminal],
  );
  const rows = useMemo<AggregateRow[]>(() => {
    const parsed = result ? parseResult(result.result) : null;
    return parsed?.results ?? [];
  }, [result]);
  const rejected = result?.status === "failed";
  const inFlight = Boolean(jobId) && (!job || !terminal);
  const running = mutation.isPending || inFlight;
  const paused = Boolean(state?.paused);
  const exhausted = selected
    ? selected.budget_exhausted ?? selected.budget.count >= selected.dataset.budget_per_day
    : false;

  useEffect(() => {
    if (!terminal) return;
    void queryClient.invalidateQueries({ queryKey: ["state"] });
    void queryClient.invalidateQueries({ queryKey: ["metrics"] });
    void queryClient.invalidateQueries({ queryKey: ["queries"] });
  }, [terminal, job?.job_id, queryClient]);

  function selectDataset(entry: DatasetState) {
    const index = datasets.findIndex((item) => item.dataset_id === entry.dataset_id);
    setSelectedIndex(index >= 0 ? index : 0);
    setJobId(null);
    mutation.reset();
  }

  function run(mode: "normal" | "rejected") {
    if (!selected?.dataset || running || paused || exhausted) return;
    setJobId(null);
    mutation.reset();
    mutation.mutate({
      dataset_id: selected.dataset_id,
      computation_id: selected.computation_id,
      ...(mode === "rejected"
        ? {
            params: {
              period_a: "2011-11",
              period_b: "2011-12",
              countries: ["Canaryland"],
              min_cohort_size: 100,
            },
          }
        : {}),
    });
  }

  if (isLoading) {
    return (
      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="skeleton h-[420px]" />
        <div className="skeleton h-[420px]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel border-danger/30 p-5 text-sm text-danger">
        Could not load contract state: {String(error)}
      </div>
    );
  }

  if (!selected?.dataset) {
    return (
      <div className="panel p-6 text-sm text-muted">
        No datasets are available on this contract yet. Register a dataset to begin.
      </div>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[0.88fr_1.12fr]">
      <div className="panel p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="eyebrow">Private inventory</p>
            <h2 className="mt-2 text-lg font-semibold">Approved datasets</h2>
          </div>
          <span className="pill">{datasets.length} live</span>
        </div>
        <div className="mt-4 grid gap-2">
          {datasets.map((entry) => (
            <DatasetTile
              key={entry.dataset_id}
              entry={entry}
              selected={entry.dataset_id === selected.dataset_id}
              onSelect={selectDataset}
            />
          ))}
        </div>
      </div>

      <div className="panel p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="eyebrow">Agent console</p>
            <h2 className="mt-2 text-lg font-semibold">
              {selected.dataset_id}
              <span className="ml-2 text-xs font-normal text-muted">· {selected.computation_id}</span>
            </h2>
          </div>
          <span className={cn("pill", exhausted && "pill-danger")}>
            {selected.budget.count}/{selected.dataset.budget_per_day} today
            {exhausted ? " · exhausted" : ""}
          </span>
        </div>

        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          <Detail label="Computation" value={selected.quote.operation} />
          <Detail label="Owner" value={short(selected.dataset.owner, 14, 10)} />
          <Detail label="Price" value={`${formatNear(selected.quote.price_yocto)} NEAR`} />
          <Detail label="Owner reward" value={`${formatNear(selected.dataset.reward_yocto)} NEAR`} />
          <Detail label="Compute deposit" value={`${formatNear(selected.dataset.compute_deposit_yocto)} NEAR`} />
          <Detail label="Dataset hash" value={short(selected.dataset.data_hash, 16, 10)} />
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <button type="button" className="btn btn-primary flex-1" disabled={running || paused || exhausted} onClick={() => run("normal")}>
            <Play size={15} /> {exhausted ? "Daily budget exhausted" : mutation.isPending ? "Queueing…" : running ? (job?.status === "queued" ? "Queued…" : "Running attested query…") : "Run query"}
          </button>
          <button
            type="button"
            className="btn btn-ghost sm:w-auto"
            disabled={running || paused || exhausted}
            onClick={() => run("rejected")}
          >
            <ShieldAlert size={14} /> Test rejected query
          </button>
        </div>
        <p className="mt-3 text-[11px] leading-5 text-faint">
          The configured demo agent pays the on-chain price, verifies the TDX attestation, then settles
          the data owner. The rejected path requests a disallowed country and must refund.
        </p>

        {paused ? (
          <div className="mt-4 rounded-xl border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning">
            Contract is paused. New queries are rejected until the owner unpauses.
          </div>
        ) : exhausted ? (
          <div className="mt-4 rounded-xl border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning">
            The demo privacy budget is exhausted. It resets at UTC midnight; the
            contract owner can reset the testnet demo budget sooner.
          </div>
        ) : null}

        {mutation.isError || jobError ? (
          <div className="mt-4 rounded-xl border border-danger/30 bg-danger/5 px-3 py-2 text-xs text-danger">
            {String(mutation.error || jobError)}
          </div>
        ) : null}

        {job?.status === "error" ? (
          <div className="mt-4 rounded-xl border border-danger/30 bg-danger/5 px-3 py-2 text-xs text-danger">
            {job.error || "The query worker reported an error."}
          </div>
        ) : null}

        {jobId ? (
          <p className="mt-3 font-mono text-[10px] text-faint">
            job {short(jobId, 14, 8)} · {job?.status ?? "queued"}
          </p>
        ) : null}

        <Timeline running={running} result={result} jobStatus={job?.status} />

        {result ? <Result result={result} rows={rows} rejected={rejected} /> : null}
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel-2 px-3 py-2">
      <p className="metric-label text-[9px]">{label}</p>
      <p className="mt-1 truncate font-mono text-[11px] text-ink" title={value}>
        {value}
      </p>
    </div>
  );
}

const terminalStatuses = ["settled", "refunded", "failed", "error"];

function jobToResult(job: JobResponse): QueryRunResponse {
  return {
    ok: true,
    dataset_id: job.dataset_id,
    computation_id: job.computation_id,
    query_id: job.query_id ?? 0,
    tx_hash: job.tx_hash ?? "",
    status: job.status === "refunded" ? "failed" : (job.status as QueryRunResponse["status"]),
    result: job.result,
    proof: job.proof,
    proof_output: job.proof_output,
    accept_tx: job.accept_tx,
    refund_tx: job.refund_tx,
    owner: job.owner ?? "",
    owner_before: job.owner_before,
    owner_after: job.owner_after,
    error: job.error ?? undefined,
  };
}

function Timeline({
  running,
  result,
  jobStatus,
}: {
  running: boolean;
  result: QueryRunResponse | null;
  jobStatus?: JobResponse["status"];
}) {
  const steps = [
    { key: "request", label: "Request submitted" },
    { key: "compute", label: "TEE computation" },
    { key: "verify", label: "Attestation verified" },
    { key: "settle", label: "Owner settled" },
  ];
  if (!running && !result) return null;

  const done = {
    request: Boolean((jobStatus && jobStatus !== "queued") || result),
    compute: Boolean(
      result && result.status !== "failed" ||
        (jobStatus && ["ready", "settled", "refunded", "failed", "error"].includes(jobStatus)),
    ),
    verify: Boolean(result?.proof || jobStatus === "settled"),
    settle: Boolean(
      result?.accept_tx ||
        result?.refund_tx ||
        jobStatus === "settled" ||
        jobStatus === "refunded",
    ),
  } as Record<string, boolean>;
  const failed = result?.status === "failed" || jobStatus === "error";

  return (
    <div className="mt-4 grid gap-2 rounded-xl border border-line bg-panel-2 p-3">
      {steps.map((step) => {
        const active = running && !done[step.key];
        const isDone = done[step.key];
        const isFail = failed && (step.key === "compute" || step.key === "verify") && !isDone;
        return (
          <div key={step.key} className="flex items-center gap-2 text-[11px]">
            <StepIcon active={active} done={isDone} fail={isFail} />
            <span className={isDone ? "text-accent" : active ? "text-ink" : isFail ? "text-danger" : "text-faint"}>
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function StepIcon({ active, done, fail }: { active: boolean; done: boolean; fail: boolean }) {
  if (done) return <Check size={13} className="text-accent" />;
  if (fail) return <AlertTriangle size={13} className="text-danger" />;
  return (
    <CircleDashed
      size={13}
      className={cn(active ? "animate-spin text-accent" : "text-faint")}
    />
  );
}

function Result({
  result,
  rows,
  rejected,
}: {
  result: QueryRunResponse;
  rows: AggregateRow[];
  rejected: boolean;
}) {
  const badge = result.proof ? "PROVEN" : rejected ? "REJECTED · REFUNDED" : "NOT PROVEN";
  const parsed = parseResult(result.result);

  return (
    <div className="mt-5 border-t border-line pt-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="eyebrow">Attested aggregate · public result</p>
          <h3 className="mt-1 text-base font-semibold">
            {result.dataset_id} aggregate <span className="text-xs font-normal text-muted">#{result.query_id}</span>
          </h3>
        </div>
        <span className={cn("pill", result.proof ? "pill-accent" : "pill-danger")}>{badge}</span>
      </div>

      {rejected ? (
        <div className="mt-4 rounded-xl border border-warning/25 bg-warning/[0.06] p-4 text-xs leading-6 text-warning">
          The workload rejected the request. No aggregate was released, and the agent was refunded.
        </div>
      ) : rows.length ? (
        <>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {rows.map((row) => (
              <div key={row.country} className="rounded-xl border border-line bg-panel-2 p-3">
                <p className="metric-label text-[9px]">{row.country}</p>
                <p className="mt-1 text-2xl font-bold tracking-[-0.04em] text-accent">{row.growth_pct}%</p>
                <p className="text-[10px] text-muted">spend {row.spend_a} → {row.spend_b}</p>
              </div>
            ))}
          </div>
          <div className="mt-3 overflow-x-auto rounded-xl border border-line">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Country</th>
                  <th>Spend A</th>
                  <th>Spend B</th>
                  <th>Growth</th>
                  <th>Cohort A</th>
                  <th>Cohort B</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.country}>
                    <td>{row.country}</td>
                    <td className="mono">{row.spend_a}</td>
                    <td className="mono">{row.spend_b}</td>
                    <td className="mono text-accent">{row.growth_pct}%</td>
                    <td>{row.cohort_a}</td>
                    <td>{row.cohort_b}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p className="mt-4 text-xs text-muted">No aggregate rows were released.</p>
      )}

      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Meta label="Request tx" value={short(result.tx_hash, 12, 8)} href={explorerTx(result.tx_hash)} />
        <Meta
          label={result.accept_tx ? "Acceptance tx" : result.refund_tx ? "Refund tx" : "Settlement"}
          value={short(result.accept_tx || result.refund_tx, 12, 8)}
          href={explorerTx(result.accept_tx || result.refund_tx)}
        />
        <Meta label="Owner before" value={`${formatNear(result.owner_before)} NEAR`} />
        <Meta label="Owner after" value={`${formatNear(result.owner_after)} NEAR`} />
      </div>

      {!rejected && result.tx_hash ? <div className="mt-4"><AttestationCard txHash={result.tx_hash} /></div> : null}

      <details className="mt-4 rounded-xl border border-line bg-[#080c10]">
        <summary className="cursor-pointer px-4 py-3 text-[11px] text-muted">Raw attestation output</summary>
        <pre className="overflow-x-auto px-4 pb-4 text-[10px] leading-5 text-muted">{result.proof_output || "No attestation output."}</pre>
      </details>

      {parsed?.dataset_sha256 ? (
        <p className="mt-3 text-[10px] text-faint">
          Dataset hash <span className="font-mono text-muted">{short(parsed.dataset_sha256, 20, 12)}</span>
        </p>
      ) : null}
    </div>
  );
}

function Meta({ label, value, href }: { label: string; value: string; href?: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel-2 px-3 py-2">
      <p className="metric-label text-[9px]">{label}</p>
      {href ? (
        <a href={href} target="_blank" rel="noreferrer" className="mt-1 flex items-center gap-1 truncate font-mono text-[10px] text-accent">
          {value} <ArrowUpRight size={10} />
        </a>
      ) : (
        <p className="mt-1 truncate font-mono text-[10px] text-ink">{value}</p>
      )}
    </div>
  );
}
