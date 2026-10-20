"use client";

import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
  const router = useRouter();
  const [isPending, setIsPending] = useState(false);

  async function handleLogout(): Promise<void> {
    setIsPending(true);
    try {
      await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
    } finally {
      router.replace("/login");
      router.refresh();
    }
  }

  return (
    <motion.button
      type="button"
      onClick={handleLogout}
      disabled={isPending}
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.96 }}
      className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-foreground/80 transition hover:border-accent-pink/40 hover:text-accent-pink disabled:opacity-50"
    >
      {isPending ? "Signing out..." : "Sign out"}
    </motion.button>
  );
}