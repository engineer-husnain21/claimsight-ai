import { ExtractionPanel, FraudPanel, ValidationPanel } from "@/components/review/finding-panels";
import { StepsTimeline } from "@/components/review/steps-timeline";
import { FadeIn } from "@/components/ui/fade-in";
import { GlassCard } from "@/components/ui/glass-card";
import { formatAmount, formatDate } from "@/lib/utils/format";
import type { ClaimReviewResponse, Recommendation } from "@/types/claim-review";

const RECOMMENDATION_STYLES: Record<Recommendation, { label: string; className: string }> = {
  approved: {
    label: "Approve",
    className: "border-emerald-400/40 bg-emerald-400/10 text-emerald-300",
  },
  rejected: { label: "Reject", className: "border-rose-400/40 bg-rose-400/10 text-rose-300" },
  needs_review: {
    label: "Needs review",
    className: "border-amber-400/40 bg-amber-400/10 text-amber-300",
  },
};

const UNKNOWN_RECOMMENDATION = {
  label: "Unknown",
  className: "border-white/15 bg-white/5 text-foreground/70",
};

/** Everything the agents found, laid out for the human reviewer. */
export function ReasoningView({ review }: { review: ClaimReviewResponse }) {
  const { result } = review;
  const recommendation =
    RECOMMENDATION_STYLES[review.recommendation] ?? UNKNOWN_RECOMMENDATION;
  const keyPoints = result.summary.key_points ?? [];

  return (
    <section className="space-y-6">
      <FadeIn>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Agent reasoning</h2>
            <p className="mt-1 text-xs text-foreground/45">
              Latest review on {formatDate(review.created_at)} · model {review.llm_model}
            </p>
          </div>
          <span
            className={`rounded-full border px-4 py-1.5 text-sm font-medium ${recommendation.className}`}
          >
            AI recommends: {recommendation.label}
          </span>
        </div>
      </FadeIn>

      <div className="grid gap-6 lg:grid-cols-3">
        <FadeIn delay={0.05} className="lg:col-span-2">
          <GlassCard title="Summary agent">
            <p className="text-sm leading-relaxed text-foreground/85">{result.summary.summary}</p>
            {keyPoints.length > 0 && (
              <ul className="mt-4 space-y-2">
                {keyPoints.map((point, index) => (
                  <li key={`${point}-${index}`} className="flex gap-2 text-sm text-foreground/75">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-violet" />
                    {point}
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-5 text-xs text-foreground/45">
              Eligible amount:{" "}
              <span className="text-foreground/80">
                {review.eligible_amount === null ? "-" : formatAmount(review.eligible_amount)}
              </span>
            </p>
          </GlassCard>
        </FadeIn>

        <FadeIn delay={0.1}>
          <GlassCard title="Agent steps">
            <StepsTimeline steps={result.steps ?? []} />
          </GlassCard>
        </FadeIn>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <FadeIn delay={0.15}>
          <ExtractionPanel extraction={result.extraction} />
        </FadeIn>
        <FadeIn delay={0.2}>
          <ValidationPanel validation={result.validation} />
        </FadeIn>
        <FadeIn delay={0.25}>
          <FraudPanel fraud={result.fraud} />
        </FadeIn>
      </div>
    </section>
  );
}