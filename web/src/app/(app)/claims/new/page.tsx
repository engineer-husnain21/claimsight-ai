import type { Metadata } from "next";
import Link from "next/link";

import { NewClaimForm } from "@/components/claims/new-claim-form";
import { FadeIn } from "@/components/ui/fade-in";

export const metadata: Metadata = {
  title: "New claim | ClaimSight AI",
};

export default function NewClaimPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <FadeIn>
        <Link
          href="/dashboard"
          className="text-sm text-foreground/50 transition hover:text-foreground"
        >
          ← Back to dashboard
        </Link>
        <h1 className="mt-4 text-3xl font-bold tracking-tight">
          Submit a{" "}
          <span className="bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink bg-clip-text text-transparent">
            new claim
          </span>
        </h1>
        <p className="mt-1 text-sm text-foreground/55">
          A reviewer will check it with AI assistance and make the final decision.
        </p>
      </FadeIn>
      <NewClaimForm />
    </div>
  );
}