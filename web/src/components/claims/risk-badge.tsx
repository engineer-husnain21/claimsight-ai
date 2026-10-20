export type RiskLevel = "low" | "medium" | "high";

/** Same thresholds as the backend FraudAgent: 0-29 low, 30-69 medium, 70+ high. */
export function riskLevelFor(score: number): RiskLevel {
  if (score >= 70) {
    return "high";
  }
  return score >= 30 ? "medium" : "low";
}

const RISK_STYLES: Record<RiskLevel, string> = {
  low: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  medium: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  high: "border-rose-400/40 bg-rose-400/15 text-rose-300 shadow-[0_0_12px_rgba(251,113,133,0.35)]",
};

export function RiskBadge({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="text-xs text-foreground/40">Not reviewed</span>;
  }
  const level = riskLevelFor(score);
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${RISK_STYLES[level]}`}
    >
      {Math.round(score)}
      <span className="opacity-70">· {level}</span>
    </span>
  );
}