"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { QueryHistory } from "@/components/query-history";
import { SectionHeading, Skeleton, Stat } from "@/components/ui/primitives";
import { api } from "@/lib/api";

export default function QueriesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["queries", 50],
    queryFn: () => api.queries(50),
    refetchInterval: 20_000,
  });

  const queries = data?.queries ?? [];
  const settled = queries.filter((query) => query.status === "settled" || query.status === "ready").length;
  const refunded = queries.filter((query) => query.status === "refunded").length;
  const failed = queries.filter((query) => query.status === "failed").length;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <SectionHeading
          eyebrow="Activity"
          title="Queries"
          description="Every query is a real on-chain request with an optional TDX proof, settlement link, and refund path."
        />
        <Link href="/app" className="btn btn-ghost btn-sm"><ArrowLeft size={13} /> Back to console</Link>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Stat label="Total" value={queries.length} />
        <Stat label="Settled / ready" value={settled} tone="accent" />
        <Stat label="Refunded" value={refunded} tone="warning" />
        <Stat label="Failed" value={failed} tone={failed ? "danger" : "default"} />
      </div>

      <section className="panel p-4 sm:p-5">
        {isLoading ? (
          <Skeleton className="h-48" />
        ) : error ? (
          <p className="text-sm text-danger">{String(error)}</p>
        ) : (
          <QueryHistory queries={queries} limit={50} />
        )}
      </section>
    </div>
  );
}
