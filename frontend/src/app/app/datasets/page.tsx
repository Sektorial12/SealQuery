"use client";

import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useState } from "react";
import { DatasetTile } from "@/components/dataset-card";
import { EmptyState, SectionHeading, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";

export default function DatasetsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 20_000 });
  const [filter, setFilter] = useState("");

  const datasets = (data?.datasets ?? []).filter((entry) =>
    `${entry.dataset_id} ${entry.computation_id} ${entry.dataset?.owner ?? ""}`.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <SectionHeading
          eyebrow="Private inventory"
          title="Datasets"
          description="Each dataset has an owner, a versioned hash, an approved computation, a per-query price, and a daily privacy budget."
        />
        <label className="relative w-full max-w-xs">
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
          <input
            className="input pl-9"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Filter datasets"
          />
        </label>
      </div>

      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} className="h-48" />)}
        </div>
      ) : error ? (
        <div className="panel border-danger/30 p-5 text-sm text-danger">{String(error)}</div>
      ) : datasets.length ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {datasets.map((entry) => (
            <DatasetTile key={entry.dataset_id} entry={entry} href={`/app/datasets/${entry.dataset_id}`} />
          ))}
        </div>
      ) : (
        <EmptyState title="No datasets found" description="Try a different filter or register a dataset on the contract." />
      )}
    </div>
  );
}
