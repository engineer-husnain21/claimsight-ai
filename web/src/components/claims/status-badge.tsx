import type { ClaimStatus } from "@/types/claims";

const STATUS_STYLES: Record<ClaimStatus, { label: string; className: string }> = {
  submitted: { label: "Submitted", className: "border-sky-400/30 bg-sky-400/10 text-sky-300" },
  needs_review: {
    label: "Needs review",
    className: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  },
  approved: {
    label: "Approved",
    className: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  },
  rejected: { label: "Rejected", className: "border-rose-400/30 bg-rose-400/10 text-rose-300" },
};

const FALLBACK = { label: "Unknown", className: "border-white/15 bg-white/5 text-foreground/70" };

export function StatusBadge({ status }: { status: ClaimStatus }) {
  const style = STATUS_STYLES[status] ?? FALLBACK;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${style.className}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {style.label}
    </span>
  );
}

export function statusLabel(status: ClaimStatus): string {
  return (STATUS_STYLES[status] ?? FALLBACK).label;
}