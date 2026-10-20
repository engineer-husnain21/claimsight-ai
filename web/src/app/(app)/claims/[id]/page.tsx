import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ClaimDetails } from "@/components/claims/claim-details";
import { RiskOverview } from "@/components/claims/risk-overview";
import { StatusBadge } from "@/components/claims/status-badge";
import { ReasoningView } from "@/components/review/reasoning-view";
import { RunReviewPanel } from "@/components/review/run-review-panel";
import { FadeIn } from "@/components/ui/fade-in";
import { GlassCard } from "@/components/ui/glass-card";
import { getCurrentUser } from "@/lib/server/authed-api";
import { getClaim } from "@/lib/server/claims-api";
import { getLatestReview } from "@/lib/server/review-api";
import { formatDate } from "@/lib/utils/format";

export const metadata: Metadata = {
  title: "Claim | ClaimSight AI",
};

interface ClaimPageProps {
  params: Promise<{ id: string }>;
}

export default async function ClaimPage({ params }: ClaimPageProps) {
  const { id } = await params;
  const [user, claim] = await Promise.all([getCurrentUser(), getClaim(id)]);

  if (claim === null) {
    notFound();
  }

  const isReviewer = user.role === "reviewer" || user.role === "admin";
  const isOwnClaim = claim.submitted_by === user.id;
  const canReview = isReviewer && !isOwnClaim;
  const latestReview = canReview ? await getLatestReview(claim.id) : null;

  return (
    <div className="space-y-6">
      <FadeIn>
        <Link
          href="/dashboard"
          className="text-sm text-foreground/50 transition hover:text-foreground"
        >
          ← Back to dashboard
        </Link>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <h1 className="font-mono text-2xl font-bold tracking-tight text-accent-cyan">
            {claim.claim_number}
          </h1>
          <StatusBadge status={claim.status} />
        </div>
        <p className="mt-1 text-sm text-foreground/50">
          Submitted on {formatDate(claim.created_at)}
        </p>
      </FadeIn>

      <div className="grid gap-6 lg:grid-cols-3">
        <FadeIn delay={0.1} className="lg:col-span-2">
          <ClaimDetails claim={claim} />
        </FadeIn>

        <FadeIn delay={0.2} className="space-y-6">
          {canReview ? (
            <>
              <RunReviewPanel claimId={claim.id} hasExistingReview={claim.risk_score !== null} />
              <RiskOverview riskScore={claim.risk_score} aiSummary={claim.ai_summary} />
            </>
          ) : (
            <GlassCard title="Review status">
              <p className="text-sm leading-relaxed text-foreground/70">
                {isOwnClaim && isReviewer
                  ? "You submitted this claim, so another reviewer must review it."
                  : "Your claim is being processed. A reviewer will make the final decision."}
              </p>
            </GlassCard>
          )}
        </FadeIn>
      </div>

      {latestReview !== null && <ReasoningView review={latestReview} />}
    </div>
  );
}