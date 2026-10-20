"use client";

import { AnimatePresence, motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AgentPipeline } from "@/components/review/agent-pipeline";
import { GENERIC_ERROR_MESSAGE, readErrorMessage } from "@/lib/utils/read-error-message";

type Phase = "idle" | "running" | "done" | "error";

interface RunReviewPanelProps {
  claimId: string;
  hasExistingReview: boolean;
}

function postReview(claimId: string): Promise<Response> {
  return fetch(`/api/claims/${claimId}/ai-reviews`, {
    method: "POST",
    credentials: "same-origin",
  });
}

export function RunReviewPanel({ claimId, hasExistingReview }: RunReviewPanelProps) {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleRun(): Promise<void> {
    if (phase === "running") {
      return;
    }
    setPhase("running");
    setError(null);

    try {
      let response = await postReview(claimId);

      if (response.status === 401) {
        // The access token may have expired; refresh once and retry.
        const refreshed = await fetch("/api/auth/refresh", {
          method: "POST",
          credentials: "same-origin",
        });
        if (!refreshed.ok) {
          router.replace(`/login?next=${encodeURIComponent(`/claims/${claimId}`)}`);
          return;
        }
        response = await postReview(claimId);
      }

      if (response.ok) {
        setPhase("done");
        router.refresh();
        return;
      }

      const data: unknown = await response.json().catch(() => null);
      setError(readErrorMessage(data));
      setPhase("error");
    } catch {
      setError(GENERIC_ERROR_MESSAGE);
      setPhase("error");
    }
  }

  const isRunning = phase === "running";

  return (
    <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-foreground/50">
        AI review
      </h2>
      <p className="mt-2 text-sm text-foreground/60">
        Four AI agents read the claim, check it against policy rules and look for fraud signals.
        The final decision stays with you.
      </p>

      <div className="my-6">
        <AgentPipeline active={isRunning} />
      </div>

      <motion.button
        type="button"
        onClick={handleRun}
        disabled={isRunning}
        whileHover={isRunning ? undefined : { scale: 1.02 }}
        whileTap={isRunning ? undefined : { scale: 0.98 }}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-accent-violet/25 disabled:cursor-wait disabled:opacity-80"
      >
        {isRunning && (
          <motion.span
            aria-hidden="true"
            className="inline-block h-4 w-4 rounded-full border-2 border-white/30 border-t-white"
            animate={{ rotate: 360 }}
            transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
          />
        )}
        {isRunning
          ? "Agents are reviewing..."
          : hasExistingReview
            ? "Run AI review again"
            : "Run AI review"}
      </motion.button>

      <p className="mt-2 text-center text-xs text-foreground/40">
        Usually takes 5 to 15 seconds.
      </p>

      <AnimatePresence mode="wait">
        {phase === "done" && (
          <motion.p
            key="done"
            role="status"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-4 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-300"
          >
            Review complete. Results are updated below.
          </motion.p>
        )}
        {phase === "error" && error !== null && (
          <motion.p
            key="error"
            role="alert"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-4 rounded-xl border border-accent-pink/30 bg-accent-pink/10 px-4 py-3 text-sm text-accent-pink"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </section>
  );
}