import { RiskBadge, riskLevelFor } from "@/components/claims/risk-badge";
import { GlassCard } from "@/components/ui/glass-card";

const RING_COLORS = {
  low: "#34d399",
  medium: "#fbbf24",
  high: "#fb7185",
} as const;

interface RiskOverviewProps {
  riskScore: number | null;
  aiSummary: string | null;
}

/** Risk score ring and the latest AI summary saved on the claim. */
export function RiskOverview({ riskScore, aiSummary }: RiskOverviewProps) {
  const circumference = 2 * Math.PI * 52;
  const score = riskScore ?? 0;
  const color = riskScore === null ? "#ffffff33" : RING_COLORS[riskLevelFor(score)];

  return (
    <GlassCard title="AI insights">
      <div className="flex items-center gap-6">
        <div className="relative h-32 w-32 shrink-0">
          <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
            <circle cx="60" cy="60" r="52" fill="none" stroke="#ffffff14" strokeWidth="10" />
            <circle
              cx="60"
              cy="60"
              r="52"
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - Math.min(score, 100) / 100)}
              style={{ filter: `drop-shadow(0 0 8px ${color})` }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold tabular-nums">
              {riskScore === null ? "-" : Math.round(score)}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-foreground/45">
              Risk score
            </span>
          </div>
        </div>
        <div className="space-y-2">
          <RiskBadge score={riskScore} />
          <p className="text-xs text-foreground/50">0-29 low · 30-69 medium · 70+ high</p>
        </div>
      </div>

      <div className="mt-6 border-t border-white/10 pt-5">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground/50">
          Summary
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-foreground/80">
          {aiSummary ?? "No AI review has been run for this claim yet."}
        </p>
      </div>
    </GlassCard>
  );
}