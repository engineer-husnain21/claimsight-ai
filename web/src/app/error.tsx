"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { useEffect } from "react";

interface ErrorPageProps {
  error: unknown;
  retry: () => void;
}

/** Friendly fallback for unexpected errors, such as the backend being busy or unavailable. */
export default function ErrorPage({ error, retry }: ErrorPageProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-[70vh] flex-1 items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-full max-w-md rounded-2xl border border-white/10 bg-white/[0.04] p-8 text-center backdrop-blur-xl"
      >
        <p className="bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink bg-clip-text text-2xl font-bold text-transparent">
          Something went wrong
        </p>
        <p className="mt-3 text-sm text-foreground/60">
          The service is busy or temporarily unavailable. Please try again in a moment.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <button
            type="button"
            onClick={() => retry()}
            className="rounded-full bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink px-5 py-2 text-sm font-semibold text-white"
          >
            Try again
          </button>
          <Link
            href="/dashboard"
            className="rounded-full border border-white/15 bg-white/5 px-5 py-2 text-sm transition hover:bg-white/10"
          >
            Dashboard
          </Link>
        </div>
      </motion.div>
    </main>
  );
}