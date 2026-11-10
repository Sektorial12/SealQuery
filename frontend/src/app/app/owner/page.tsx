"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Building2, Plus, Wallet } from "lucide-react";
import Link from "next/link";
import { QueryHistory } from "@/components/query-history";
import { SectionHeading, Stat } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { explorerAccount, formatNear, short } from "@/lib/format";

export default function OwnerPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 20_000 });
  const { data: summary } = useQuery({ queryKey: ["owner-summary"], queryFn: api.ownerSummary, refetchInterval: 20_000 });

  if (isLoading) return <div className="skeleton h-80" />;
  if (error) return <div className="panel border-danger/30 p-5 text-sm text-danger">{String(error)}</div>;

  const datasets = data?.datasets ?? [];
  const queries = data?.recent_queries ?? [];
  const owners = summary?.owners ?? [];
  const totalSettled = owners.reduce((total, owner) => total + owner.settled, 0);
  const totalGross = owners.reduce((total, owner) => total + BigInt(owner.gross_reward_yocto), 0n);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <SectionHeading
          eyebrow="Data owner"
          title="Owner console"
          description="Datasets, approved computations, prices, budgets, and indexed owner rewards. Registration and rotation controls are not enabled in the demo."
        />
        <button type="button" className="btn btn-ghost btn-sm" disabled title="Owner self-serve registration is not enabled in the demo">
          <Plus size={13} /> Register dataset
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Stat label="Datasets" value={summary?.datasets ?? datasets.length} />
        <Stat label="Owners" value={owners.length} />
        <Stat label="Settled queries" value={totalSettled} tone="accent" />
        <Stat label="Gross owner reward" value={`${formatNear(totalGross.toString())} NEAR`} hint="indexed accepted queries" />
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        {owners.map((owner) => {
          const owned = datasets.filter((entry) => entry.dataset.owner === owner.owner);
          return (
            <section key={owner.owner} className="panel p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="grid size-9 place-items-center rounded-lg border border-line bg-panel-3 text-accent"><Building2 size={15} /></span>
                  <div>
                    <p className="font-mono text-xs">{short(owner.owner, 18, 10)}</p>
                    <p className="text-[10px] text-faint">data owner</p>
                  </div>
                </div>
                <a href={explorerAccount(owner.owner)} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">Explorer <ArrowUpRight size={12} /></a>
              </div>
              <div className="mt-4 grid gap-2">
                {owner.datasets.map((item) => {
                  const entry = owned.find((candidate) => candidate.dataset_id === item.dataset_id);
                  return (
                    <div key={item.dataset_id} className="rounded-xl border border-line bg-panel-2 p-3">
                      <div className="flex items-center justify-between">
                        <Link href={`/app/datasets/${item.dataset_id}`} className="text-xs font-semibold hover:text-accent">{item.dataset_id}</Link>
                        <span className="text-[10px] text-accent">{formatNear(item.gross_reward_yocto)} NEAR earned</span>
                      </div>
                      <p className="mt-1 text-[10px] text-faint">
                        {item.settled} settled · {item.refunded} refunded · {item.failed} failed
                        {entry ? ` · budget ${entry.budget.count}/${entry.dataset.budget_per_day}` : ""}
                      </p>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 flex items-center justify-between text-[10px] text-faint">
                <span className="flex items-center gap-1"><Wallet size={11} /> {owner.query_count} indexed queries</span>
                <Link href="/app/agent" className="text-accent">Agent view →</Link>
              </div>
            </section>
          );
        })}
      </div>

      <section className="panel p-4 sm:p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="eyebrow">Owner activity</p>
            <h2 className="mt-1 text-lg font-semibold">Recent queries across owned datasets</h2>
          </div>
          <Link href="/app/queries" className="text-[11px] text-accent">All queries →</Link>
        </div>
        <div className="mt-3">
          <QueryHistory queries={queries} limit={8} />
        </div>
      </section>
    </div>
  );
}
