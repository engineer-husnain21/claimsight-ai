"use client";

import { motion } from "motion/react";

const COLUMNS: { agents: string[]; color: string }[] = [
  { agents: ["Extraction"], color: "#22d3ee" },
  { agents: ["Validation", "Fraud"], color: "#a78bfa" },
  { agents: ["Summary"], color: "#f472b6" },
];

function AgentNode({
  name,
  color,
  active,
  delay,
}: {
  name: string;
  color: string;
  active: boolean;
  delay: number;
}) {
  return (
    <motion.div
      className="rounded-xl border px-3 py-2 text-center text-xs font-medium"
      style={{ borderColor: `${color}55`, color }}
      animate={
        active
          ? {
              backgroundColor: [`${color}0d`, `${color}33`, `${color}0d`],
              boxShadow: [`0 0 0px ${color}00`, `0 0 18px ${color}88`, `0 0 0px ${color}00`],
            }
          : { backgroundColor: `${color}0d`, boxShadow: `0 0 0px ${color}00` }
      }
      transition={
        active
          ? { duration: 1.8, repeat: Infinity, delay, ease: "easeInOut" }
          : { duration: 0.3 }
      }
    >
      {name}
    </motion.div>
  );
}

function Connector({ active, delay }: { active: boolean; delay: number }) {
  return (
    <div className="relative h-px w-6 shrink-0 overflow-hidden bg-white/15 sm:w-10">
      {active && (
        <motion.span
          className="absolute inset-y-0 w-3 bg-white"
          animate={{ x: ["-100%", "400%"] }}
          transition={{ duration: 1.8, repeat: Infinity, delay, ease: "easeInOut" }}
        />
      )}
    </div>
  );
}

/** Visual of the LangGraph flow: extraction, then validation and fraud in parallel, then summary. */
export function AgentPipeline({ active }: { active: boolean }) {
  return (
    <div className="flex items-center justify-center" aria-hidden="true">
      {COLUMNS.map((column, index) => (
        <div key={column.color} className="flex items-center">
          {index > 0 && <Connector active={active} delay={index * 0.5 - 0.25} />}
          <div className="flex flex-col gap-2">
            {column.agents.map((agent) => (
              <AgentNode
                key={agent}
                name={agent}
                color={column.color}
                active={active}
                delay={index * 0.5}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}