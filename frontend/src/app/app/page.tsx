"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { LiveStats } from "@/components/live-stats";
import { QueryConsole } from "@/components/query-console";
import { QueryHistory } from "@/components/query-history";
import { api } from "@/lib/api";

export default function AppOverviewPage() {
  const { data: state } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 15_000 });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">Overview</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-[-0.035em]">Private data compute</h1>
          <p className="mt-1 text-xs text-muted">
            Quote, pay, execute, verify, and settle an approved computation on NEAR testnet.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/app/proofs" className="btn btn-ghost btn-sm"><ShieldCheck size={13} /> Proof explorer</Link>
          <Link href="/docs#mcp" className="btn btn-ghost btn-sm">MCP <ArrowUpRight size={12} /></Link>
        </div>
      </div>

      <LiveStats compact />
      <QueryConsole />

      <section className="panel p-4 sm:p-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Activity</p>
            <h2 className="mt-2 text-lg font-semibold">Recent queries</h2>
          </div>
          <Link href="/app/queries" className="text-[11px] text-accent">View all →</Link>
        </div>
        <div className="mt-3">
          <QueryHistory queries={state?.recent_queries ?? []} limit={6} />
        </div>
      </section>
    </div>
  );
}
