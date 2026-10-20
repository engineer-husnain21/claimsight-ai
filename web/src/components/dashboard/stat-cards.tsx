"use client";

import { animate, motion, useMotionValue, useTransform } from "motion/react";
import { useEffect } from "react";

export interface StatCardData {
  label: string;
  value: number;
  accent: string;
}

function AnimatedNumber({ value }: { value: number }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest).toLocaleString("en-US"));

  useEffect(() => {
    const controls = animate(count, value, { duration: 1.2, ease: "easeOut" });
    return () => controls.stop();
  }, [count, value]);

  return <motion.span>{rounded}</motion.span>;
}

export function StatCards({ stats }: { stats: StatCardData[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
      {stats.map((stat, index) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: index * 0.07, ease: "easeOut" }}
          whileHover={{ y: -4 }}
          className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur-xl"
        >
          <span
            className={`absolute -right-8 -top-8 h-24 w-24 rounded-full opacity-30 blur-2xl transition-opacity group-hover:opacity-60 ${stat.accent}`}
          />
          <p className="relative text-xs font-medium uppercase tracking-wider text-foreground/50">
            {stat.label}
          </p>
          <p className="relative mt-3 text-3xl font-bold tabular-nums">
            <AnimatedNumber value={stat.value} />
          </p>
        </motion.div>
      ))}
    </div>
  );
}