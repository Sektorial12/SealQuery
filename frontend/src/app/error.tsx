"use client";

import { RefreshCcw } from "lucide-react";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="mx-auto flex min-h-[70vh] w-full max-w-2xl flex-col items-center justify-center px-5 text-center">
      <span className="pill pill-danger">Client error</span>
      <h1 className="mt-5 text-3xl font-semibold tracking-[-0.04em]">The page failed to load.</h1>
      <p className="mt-3 text-sm leading-7 text-muted">
        The API may be down or the page data may be stale. Retry the request; the contract remains the
        source of truth.
      </p>
      <button type="button" className="btn btn-primary btn-sm mt-6" onClick={() => reset()}>
        <RefreshCcw size={13} /> Retry
      </button>
    </div>
  );
}
