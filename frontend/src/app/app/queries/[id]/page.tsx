"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpRight, Check, Download, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AttestationCard } from "@/components/attestation-card";
import { EmptyState } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { explorerAccount, explorerTx, formatNear, parseResult, short, statusTone } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function QueryDetailPage() {
  const params = useParams();
  const queryId = Number(params.id);
  const { data: query, isLoading, error } = useQuery({
    queryKey: ["query", queryId],
    queryFn: () => api.query(queryId),
    retry: false,
  });
  const { data: state } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 20_000 });
  const dataset = state?.datasets.find((entry) => entry.dataset_id === query?.dataset_id);

  if (isLoading) return <div className="skeleton h-80" />;
  if (error || !query) {
    return (
      <div className="space-y-4">
        <Link href="/app/queries" className="inline-flex items-center gap-1 text-xs text-muted"><ArrowLeft size={13} /> Queries</Link>
        <EmptyState title="Query not found" description={String(error ?? "The contract does not have a query with this ID.")} />
      </div>
    );
  }

  const parsed = parseResult(query.result);
  const rows = parsed?.results ?? [];
  const rejected = query.status === "failed" || query.status === "refunded";
  const badge = rejected ? (query.refund_tx ? "REJECTED · REFUNDED" : "FAILED") : query.status === "settled" ? "PROVEN" : "READY";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link href="/app/queries" className="inline-flex items-center gap-1 text-xs text-muted hover:text-ink">
          <ArrowLeft size={13} /> Queries
        </Link>
        <div className="flex gap-2">
          {query.tx_hash ? (
            <a href={explorerTx(query.tx_hash)} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">
              Request tx <ArrowUpRight size={12} />
            </a>
          ) : null}
          {query.accept_tx || query.refund_tx ? (
            <a href={explorerTx(query.accept_tx || query.refund_tx)} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">
              {query.accept_tx ? "Acceptance" : "Refund"} tx <ArrowUpRight size={12} />
            </a>
          ) : null}
        </div>
      </div>

      <section className="panel overflow-hidden">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line p-5 sm:p-6">
          <div>
            <p className="eyebrow">Query #{query.query_id}</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-[-0.035em]">
              {query.dataset_id} <span className="text-sm font-normal text-muted">· {query.computation_id}</span>
            </h1>
            <p className="mt-1 text-[11px] text-faint">block {query.created_block} · {short(query.agent, 14, 10)}</p>
          </div>
          <span className={cn("pill", statusTone(query.status) === "accent" && "pill-accent", statusTone(query.status) === "warning" && "pill-warning", statusTone(query.status) === "danger" && "pill-danger")}>
            {badge}
          </span>
        </div>

        <div className="grid gap-2 p-5 sm:grid-cols-3 sm:p-6">
          <Meta label="Deposit" value={`${formatNear(query.deposit_yocto)} NEAR`} />
          <Meta label="Data owner" value={dataset?.dataset.owner ? short(dataset.dataset.owner, 16, 10) : "—"} href={dataset ? explorerAccount(dataset.dataset.owner) : undefined} />
          <Meta label="Dataset hash" value={short(parsed?.dataset_sha256 || dataset?.dataset.data_hash, 18, 12)} />
        </div>

        {rejected ? (
          <div className="mx-5 mb-5 rounded-xl border border-warning/25 bg-warning/[0.06] p-4 text-xs leading-6 text-warning sm:mx-6 sm:mb-6">
            The workload rejected this request. No aggregate was released.{" "}
            {query.refund_tx ? "The agent was refunded on-chain." : "A refund is pending."}
            {query.refund_tx ? (
              <a href={explorerTx(query.refund_tx)} target="_blank" rel="noreferrer" className="ml-1 underline">Inspect refund</a>
            ) : null}
          </div>
        ) : rows.length ? (
          <div className="mx-5 mb-5 overflow-x-auto rounded-xl border border-line sm:mx-6 sm:mb-6">
            <table className="data-table">
              <thead>
                <tr><th>Country</th><th>Spend A</th><th>Spend B</th><th>Growth</th><th>Cohort A</th><th>Cohort B</th></tr>
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
        ) : null}

        {!rejected && query.tx_hash ? (
          <div className="mx-5 mb-5 sm:mx-6 sm:mb-6"><AttestationCard txHash={query.tx_hash} /></div>
        ) : null}

        {query.tx_hash ? (
          <div className="border-t border-line p-5 sm:p-6">
            <a className="btn btn-ghost btn-sm" href={`/api/attestation/${query.tx_hash}/bundle`}>
              <Download size={13} /> Download proof bundle
            </a>
            <span className="ml-3 text-[10px] text-faint">Verify offline with <code className="font-mono">outlayer-verify bundle</code></span>
          </div>
        ) : null}
      </section>

      <section className="panel p-5">
        <p className="eyebrow">Next</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link href="/app" className="btn btn-primary btn-sm"><RotateCcw size={13} /> Run another query</Link>
          <Link href="/app/proofs" className="btn btn-ghost btn-sm"><Check size={13} /> Verify a proof</Link>
        </div>
      </section>
    </div>
  );
}

function Meta({ label, value, href }: { label: string; value: string; href?: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel-2 p-3">
      <p className="metric-label text-[9px]">{label}</p>
      {href ? <a href={href} target="_blank" rel="noreferrer" className="mt-1 block truncate font-mono text-[11px] text-accent">{value}</a> : <p className="mt-1 truncate font-mono text-[11px] text-ink">{value}</p>}
    </div>
  );
}
