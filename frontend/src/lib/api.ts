import type {
  AttestationReport,
  Health,
  Metrics,
  QueryRecord,
  QueryRunResponse,
  State,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Request failed (${response.status})`);
  }
  return payload as T;
}

export const api = {
  state: () => request<State>("/api/state"),
  metrics: () => request<Metrics>("/api/metrics"),
  health: () => request<Health>("/api/health"),
  queries: (limit = 20) =>
    request<{ agent: string; count: number; queries: QueryRecord[] }>(
      `/api/queries?limit=${limit}`,
    ),
  query: (queryId: number) => request<QueryRecord>(`/api/queries/${queryId}`),
  runQuery: (body: {
    dataset_id: string;
    computation_id: string;
    params?: Record<string, unknown>;
  }) =>
    request<QueryRunResponse>("/api/query", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  attestation: (txHash: string) =>
    request<{ proven: boolean; attestation: AttestationReport; output?: string }>(
      `/api/attestation/${txHash}`,
    ),
  proof: (txHash: string) =>
    request<{ proven: boolean; output: string }>(`/api/proof/${txHash}`),
};
