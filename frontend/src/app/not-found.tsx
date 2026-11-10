import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[70vh] w-full max-w-2xl flex-col items-center justify-center px-5 text-center">
      <span className="pill">404</span>
      <h1 className="mt-5 text-4xl font-semibold tracking-[-0.04em]">This route is not in the enclave.</h1>
      <p className="mt-3 text-sm leading-7 text-muted">
        The page does not exist, or the dataset or query ID is unknown. Return to the agent console or
        inspect the proof explorer.
      </p>
      <div className="mt-6 flex gap-2">
        <Link href="/app" className="btn btn-primary btn-sm">Agent console</Link>
        <Link href="/app/proofs" className="btn btn-ghost btn-sm">Proof explorer</Link>
      </div>
    </div>
  );
}
