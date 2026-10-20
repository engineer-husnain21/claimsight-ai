"use client";

import { motion } from "motion/react";

import type { AgentStep } from "@/types/claim-review";

const AGENT_COLORS: Record<string, string> = {
  extraction: "#22d3ee",
  validation: "#a78bfa",
  fraud: "#a78bfa",
  summary: "#f472b6",
};

function colorFor(agent: string): string {
  return AGENT_COLORS[agent.toLowerCase()] ?? "#60a5fa";
}

function formatDuration(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${Math.round(ms)} ms`;
}

/** How long each agent took, as animated bars relative to the slowest agent. */
export function StepsTimeline({ steps }: { steps: AgentStep[] }) {
  if (steps.length === 0) {
    return <p className="text-sm text-foreground/50">No step timings were recorded.</p>;
  }

  const slowest = Math.max(...steps.map((step) => step.duration_ms), 1);

  return (
    <ol className="space-y-4">
      {steps.map((step, index) => {
        const color = colorFor(step.agent);
        return (
          <li key={`${step.agent}-${index}`} className="grid grid-cols-[6.5rem_1fr_4rem] items-center gap-3">
            <span className="flex items-center gap-2 text-sm capitalize">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
              />
              {step.agent}
            </span>
            <div className="h-2 overflow-hidden rounded-full bg-white/10">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: color }}
                initial={{ width: 0 }}
                animate={{ width: `${Math.max((step.duration_ms / slowest) * 100, 2)}%` }}
                transition={{ duration: 0.8, delay: index * 0.15, ease: "easeOut" }}
              />
            </div>
            <span className="text-right text-xs tabular-nums text-foreground/55">
              {formatDuration(step.duration_ms)}
            </span>
          </li>
        );
      })}
    </ol>
  );
}