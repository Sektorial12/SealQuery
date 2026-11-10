"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatNear } from "@/lib/format";
import { Skeleton, Stat } from "@/components/ui/primitives";

export function LiveStats({ compact = false }: { compact?: boolean }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["metrics"],
    queryFn: api.metrics,
    refetchInterval: 15_000,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-[104px]" />
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="panel-2 px-4 py-3 text-xs text-muted">
        Live testnet metrics are temporarily unavailable. The proof explorer and app still work.
      </div>
    );
  }

  const settled = data.queries.by_status.settled ?? 0;
  const refunded = data.queries.by_status.refunded ?? 0;
  const rate = data.queries.recent_success_rate;

  return (
    <div className={compact ? "grid grid-cols-2 gap-2 sm:grid-cols-4" : "grid grid-cols-2 gap-3 lg:grid-cols-4"}>
      <Stat label="Datasets" value={data.datasets.length} hint="approved computations" />
      <Stat label="Recent queries" value={data.queries.recent} hint={`${settled} settled · ${refunded} refunded`} />
      <Stat
        label="Recent success"
        value={rate === null ? "—" : `${Math.round(rate * 100)}%`}
        hint="settled or ready"
        tone={rate !== null && rate < 1 ? "warning" : "accent"}
      />
      <Stat
        label="Agent balance"
        value={`${formatNear(data.balances.agent, 3)}`}
        hint="NEAR testnet"
        tone={data.ok ? "default" : "danger"}
      />
    </div>
  );
}
