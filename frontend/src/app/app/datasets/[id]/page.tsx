"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, Play, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { QueryHistory } from "@/components/query-history";
import { api } from "@/lib/api";
import { explorerAccount, formatNear, short } from "@/lib/format";

export default function DatasetDetailPage() {
  const params = useParams();
  const datasetId = String(params.id);
  const { data, isLoading, error } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 20_000 });
  const entry = data?.datasets.find((item) => item.dataset_id === datasetId);
  const queries = (data?.recent_queries ?? []).filter((query) => query.dataset_id === datasetId);

  if (isLoading) return <div className="skeleton h-80" />;
  if (error) return <div className="panel border-danger/30 p-5 text-sm text-danger">{String(error)}</div>;
  if (!entry?.dataset) return <div className="panel p-5 text-sm text-muted">Dataset not found.</div>;

  const dataset = entry.dataset;
  const quote = entry.quote;
  const usage = dataset.budget_per_day ? Math.min(100, (entry.budget.count / dataset.budget_per_day) * 100) : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link href="/app/datasets" className="inline-flex items-center gap-1 text-xs text-muted hover:text-ink">
          <ArrowLeft size={13} /> Datasets
        </Link>
        <div className="flex gap-2">
          <Link href="/app" className="btn btn-ghost btn-sm"><Play size={13} /> Run query</Link>
          <Link href="/app/proofs" className="btn btn-ghost btn-sm"><ShieldCheck size={13} /> Proofs</Link>
        </div>
      </div>

      <section className="panel overflow-hidden">
        <div className="border-b border-line p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="eyebrow">Dataset</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">{entry.dataset_id}</h1>
              <p className="mt-1 text-xs text-muted">version {dataset.version} · {entry.computation.operation}</p>
            </div>
            <div className="text-right">
              <p className="metric-label">Price per query</p>
              <p className="mt-1 text-2xl font-bold tracking-[-0.04em] text-accent">{formatNear(quote.price_yocto)} NEAR</p>
            </div>
          </div>
        </div>
        <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4 sm:p-6">
          <Field label="Owner" value={dataset.owner} href={explorerAccount(dataset.owner)} />
          <Field label="Owner reward" value={`${formatNear(dataset.reward_yocto)} NEAR`} />
          <Field label="Compute deposit" value={`${formatNear(dataset.compute_deposit_yocto)} NEAR`} />
          <Field label="Dataset hash" value={short(dataset.data_hash, 18, 12)} />
          <Field label="Computation" value={entry.computation_id} />
          <Field label="Approved operation" value={entry.computation.operation} />
          <Field label="WASM hash" value={short(entry.computation.wasm_hash, 18, 12)} />
          <Field label="OutLayer project" value={entry.computation.outlayer_project_id} />
        </div>
        <div className="border-t border-line p-5 sm:p-6">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-muted">Daily privacy budget</span>
            <span className="font-mono text-ink">{entry.budget.count}/{dataset.budget_per_day}</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-panel-3">
            <div className="h-full rounded-full bg-gradient-to-r from-accent to-accent-2" style={{ width: `${usage}%` }} />
          </div>
          <p className="mt-2 text-[10px] text-faint">Resets per UTC day. The contract enforces the budget before OutLayer is called.</p>
        </div>
      </section>

      <section className="panel p-4 sm:p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="eyebrow">History</p>
            <h2 className="mt-1 text-lg font-semibold">Queries on this dataset</h2>
          </div>
          <Link href="/app/queries" className="text-[11px] text-accent">All queries →</Link>
        </div>
        <div className="mt-3">
          <QueryHistory queries={queries} limit={10} />
        </div>
      </section>
    </div>
  );
}

function Field({ label, value, href }: { label: string; value: string; href?: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel-2 p-3">
      <p className="metric-label text-[9px]">{label}</p>
      {href ? (
        <a href={href} target="_blank" rel="noreferrer" className="mt-1 flex items-center gap-1 truncate font-mono text-[11px] text-accent">
          {short(value, 18, 10)} <ExternalLink size={10} />
        </a>
      ) : (
        <p className="mt-1 truncate font-mono text-[11px] text-ink" title={value}>{value}</p>
      )}
    </div>
  );
}
