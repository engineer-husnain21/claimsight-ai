"use client";

import { AnimatePresence, motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { GENERIC_ERROR_MESSAGE, readErrorMessage } from "@/lib/utils/read-error-message";
import type { ClaimStatus, ReviewDecision } from "@/types/claims";

const MAX_NOTE_LENGTH = 1000;

const DECISIONS: { value: ReviewDecision; label: string; idle: string; selected: string }[] = [
  {
    value: "approved",
    label: "Approve",
    idle: "border-emerald-400/25 text-emerald-300 hover:bg-emerald-400/10",
    selected: "border-emerald-400 bg-emerald-400/20 text-emerald-200 shadow-[0_0_20px_rgba(52,211,153,0.35)]",
  },
  {
    value: "needs_review",
    label: "Needs review",
    idle: "border-amber-400/25 text-amber-300 hover:bg-amber-400/10",
    selected: "border-amber-400 bg-amber-400/20 text-amber-200 shadow-[0_0_20px_rgba(251,191,36,0.35)]",
  },
  {
    value: "rejected",
    label: "Reject",
    idle: "border-rose-400/25 text-rose-300 hover:bg-rose-400/10",
    selected: "border-rose-400 bg-rose-400/20 text-rose-200 shadow-[0_0_20px_rgba(251,113,133,0.35)]",
  },
];

interface DecisionPanelProps {
  claimId: string;
  currentStatus: ClaimStatus;
}

function sendDecision(claimId: string, status: ReviewDecision, note: string): Promise<Response> {
  return fetch(`/api/claims/${claimId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, note }),
    credentials: "same-origin",
  });
}

/** Final human decision. The AI only recommends; this panel records what the reviewer decides. */
export function DecisionPanel({ claimId, currentStatus }: DecisionPanelProps) {
  const router = useRouter();
  const [selected, setSelected] = useState<ReviewDecision | null>(null);
  const [note, setNote] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const selectedOption = DECISIONS.find((option) => option.value === selected) ?? null;

  async function handleConfirm(): Promise<void> {
    if (selected === null || isSaving) {
      return;
    }
    setIsSaving(true);
    setError(null);
    setSavedMessage(null);

    try {
      let response = await sendDecision(claimId, selected, note);

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
        response = await sendDecision(claimId, selected, note);
      }

      if (response.ok) {
        setSavedMessage(`Decision saved: ${selectedOption?.label ?? selected}.`);
        setSelected(null);
        setNote("");
        router.refresh();
      } else {
        const data: unknown = await response.json().catch(() => null);
        setError(readErrorMessage(data));
      }
    } catch {
      setError(GENERIC_ERROR_MESSAGE);
    }
    setIsSaving(false);
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-foreground/50">
        Your decision
      </h2>
      <p className="mt-2 text-sm text-foreground/60">
        The AI only recommends. You make the final call.
      </p>

      <div className="mt-5 grid grid-cols-3 gap-2">
        {DECISIONS.map((option) => {
          const isSelected = selected === option.value;
          const isCurrent = currentStatus === option.value;
          return (
            <motion.button
              key={option.value}
              type="button"
              onClick={() => {
                setSelected(isSelected ? null : option.value);
                setError(null);
                setSavedMessage(null);
              }}
              disabled={isSaving}
              whileTap={{ scale: 0.96 }}
              aria-pressed={isSelected}
              className={`relative rounded-xl border px-2 py-2.5 text-xs font-semibold transition ${
                isSelected ? option.selected : option.idle
              } disabled:opacity-50`}
            >
              {option.label}
              {isCurrent && (
                <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-current" />
              )}
            </motion.button>
          );
        })}
      </div>

      <AnimatePresence initial={false}>
        {selectedOption !== null && (
          <motion.div
            key="confirm"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <label htmlFor="decision-note" className="mt-5 block text-xs text-foreground/50">
              Note (optional)
            </label>
            <textarea
              id="decision-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              maxLength={MAX_NOTE_LENGTH}
              rows={3}
              disabled={isSaving}
              placeholder="Reason for this decision"
              className="mt-2 w-full resize-none rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none transition placeholder:text-foreground/30 focus:border-accent-violet/60 focus:ring-4 focus:ring-accent-violet/15 disabled:opacity-60"
            />
            <p className="mt-1 text-right text-[11px] text-foreground/35">
              {note.length}/{MAX_NOTE_LENGTH}
            </p>

            <motion.button
              type="button"
              onClick={handleConfirm}
              disabled={isSaving}
              whileHover={isSaving ? undefined : { scale: 1.02 }}
              whileTap={isSaving ? undefined : { scale: 0.98 }}
              className={`mt-3 w-full rounded-xl border px-4 py-3 text-sm font-semibold ${selectedOption.selected} disabled:cursor-wait disabled:opacity-70`}
            >
              {isSaving ? "Saving..." : `Confirm: ${selectedOption.label}`}
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {savedMessage !== null && (
          <motion.p
            key="saved"
            role="status"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-4 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-300"
          >
            {savedMessage}
          </motion.p>
        )}
        {error !== null && (
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