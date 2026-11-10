import type { AggregateResult } from "./types";

const YOCTO = 10n ** 24n;

export function formatNear(yocto: string | null | undefined, digits = 4): string {
  if (!yocto) return "—";
  try {
    const value = BigInt(yocto);
    const whole = value / YOCTO;
    const fraction = (value % YOCTO).toString().padStart(24, "0").slice(0, digits);
    return `${whole.toLocaleString()}.${fraction}`;
  } catch {
    return "—";
  }
}

export function formatUsd(yocto: string | null | undefined, nearPrice = 5): string {
  if (!yocto) return "—";
  try {
    const near = Number(BigInt(yocto)) / 1e24;
    return `$${(near * nearPrice).toFixed(2)}`;
  } catch {
    return "—";
  }
}

export function short(value: string | null | undefined, head = 8, tail = 6): string {
  if (!value) return "—";
  if (value.length <= head + tail + 1) return value;
  return `${value.slice(0, head)}…${value.slice(-tail)}`;
}

export function parseResult(raw: string | AggregateResult | null | undefined): AggregateResult | null {
  if (!raw) return null;
  if (typeof raw === "object") return raw as AggregateResult;
  try {
    return JSON.parse(raw) as AggregateResult;
  } catch {
    return null;
  }
}

export function explorerTx(tx: string | null | undefined): string {
  return tx ? `https://explorer.testnet.near.org/transactions/${tx}` : "#";
}

export function explorerAccount(account: string | null | undefined): string {
  return account ? `https://explorer.testnet.near.org/accounts/${account}` : "#";
}

export function timeAgo(timestamp: number): string {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - timestamp));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function statusTone(status: string): "accent" | "warning" | "danger" | "muted" {
  if (status === "settled" || status === "ready") return "accent";
  if (status === "failed") return "danger";
  if (status === "refunded") return "warning";
  return "muted";
}
