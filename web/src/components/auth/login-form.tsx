"use client";

import { AnimatePresence, MotionConfig, motion, useAnimationControls } from "motion/react";
import type { Variants } from "motion/react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

const GENERIC_ERROR = "Something went wrong. Please try again.";
const MAX_EMAIL_LENGTH = 254;
const MAX_PASSWORD_LENGTH = 128;

const containerVariants: Variants = {
  hidden: { opacity: 0, y: 28, scale: 0.97 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.6, ease: "easeOut", staggerChildren: 0.08, delayChildren: 0.15 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

interface LoginFormProps {
  redirectTo: string;
}

function readErrorMessage(data: unknown): string {
  if (typeof data === "object" && data !== null && "error" in data) {
    const { error } = data as { error: unknown };
    if (typeof error === "string" && error.length > 0) {
      return error;
    }
  }
  return GENERIC_ERROR;
}

function ShieldLogo() {
  return (
    <motion.div
      className="relative mx-auto flex h-16 w-16 items-center justify-center"
      animate={{ rotate: [0, 4, -4, 0] }}
      transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
    >
      <motion.span
        className="absolute inset-0 rounded-2xl bg-linear-to-br from-accent-cyan via-accent-violet to-accent-pink blur-xl"
        animate={{ opacity: [0.35, 0.7, 0.35], scale: [0.9, 1.05, 0.9] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />
      <span className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-white/15 bg-background/80">
        <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" aria-hidden="true">
          <defs>
            <linearGradient id="logo-gradient" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#22d3ee" />
              <stop offset="50%" stopColor="#a78bfa" />
              <stop offset="100%" stopColor="#f472b6" />
            </linearGradient>
          </defs>
          <path
            d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3z"
            stroke="url(#logo-gradient)"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
          <path
            d="M8.5 12.5l2.3 2.3 4.7-5"
            stroke="url(#logo-gradient)"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
    </motion.div>
  );
}

function Spinner() {
  return (
    <motion.span
      aria-hidden="true"
      className="inline-block h-4 w-4 rounded-full border-2 border-white/30 border-t-white"
      animate={{ rotate: 360 }}
      transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
    />
  );
}

/** Login form. Credentials go to the Next.js BFF route; tokens never reach this component. */
export function LoginForm({ redirectTo }: LoginFormProps) {
  const router = useRouter();
  const shakeControls = useAnimationControls();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function showError(message: string): void {
    setError(message);
    void shakeControls.start({ x: [0, -10, 10, -6, 6, 0], transition: { duration: 0.4 } });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "same-origin",
      });

      if (response.ok) {
        setPassword("");
        router.replace(redirectTo);
        router.refresh();
        return;
      }

      const data: unknown = await response.json().catch(() => null);
      showError(readErrorMessage(data));
    } catch {
      showError(GENERIC_ERROR);
    }
    setIsSubmitting(false);
  }

  return (
    <MotionConfig reducedMotion="user">
      <motion.div className="w-full max-w-md" animate={shakeControls}>
        <motion.div variants={containerVariants} initial="hidden" animate="visible">
          <div className="rounded-3xl bg-linear-to-br from-accent-cyan/60 via-accent-violet/40 to-accent-pink/60 p-px shadow-[0_0_60px_-15px_rgba(167,139,250,0.55)]">
            <div className="rounded-3xl bg-background/80 px-8 py-10 backdrop-blur-xl">
              <motion.div variants={itemVariants} className="mb-8 text-center">
                <ShieldLogo />
                <h1 className="mt-5 bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink bg-clip-text text-3xl font-bold tracking-tight text-transparent">
                  ClaimSight AI
                </h1>
                <p className="mt-2 text-sm text-foreground/60">
                  Sign in to review hospital claims
                </p>
              </motion.div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <motion.div variants={itemVariants} className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium text-foreground/80">
                    Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="username"
                    required
                    maxLength={MAX_EMAIL_LENGTH}
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    disabled={isSubmitting}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm outline-none transition placeholder:text-foreground/30 focus:border-accent-cyan/70 focus:bg-white/[0.07] focus:ring-4 focus:ring-accent-cyan/15 disabled:opacity-60"
                    placeholder="you@hospital.com"
                  />
                </motion.div>

                <motion.div variants={itemVariants} className="space-y-2">
                  <label htmlFor="password" className="text-sm font-medium text-foreground/80">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      required
                      maxLength={MAX_PASSWORD_LENGTH}
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      disabled={isSubmitting}
                      className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-4 pr-16 text-sm outline-none transition placeholder:text-foreground/30 focus:border-accent-violet/70 focus:bg-white/[0.07] focus:ring-4 focus:ring-accent-violet/15 disabled:opacity-60"
                      placeholder="Your password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                      className="absolute inset-y-0 right-3 my-auto h-fit rounded-md px-2 py-1 text-xs text-foreground/60 transition hover:bg-white/10 hover:text-foreground"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                </motion.div>

                <AnimatePresence mode="wait">
                  {error !== null && (
                    <motion.p
                      key={error}
                      role="alert"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden rounded-xl border border-accent-pink/30 bg-accent-pink/10 px-4 py-3 text-sm text-accent-pink"
                    >
                      {error}
                    </motion.p>
                  )}
                </AnimatePresence>

                <motion.div variants={itemVariants}>
                  <motion.button
                    type="submit"
                    disabled={isSubmitting}
                    whileHover={isSubmitting ? undefined : { scale: 1.02 }}
                    whileTap={isSubmitting ? undefined : { scale: 0.98 }}
                    className="relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-accent-violet/25 transition-opacity disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {isSubmitting && <Spinner />}
                    {isSubmitting ? "Signing in..." : "Sign in"}
                  </motion.button>
                </motion.div>
              </form>

              <motion.p
                variants={itemVariants}
                className="mt-8 text-center text-xs text-foreground/40"
              >
                AI recommends. Humans decide.
              </motion.p>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </MotionConfig>
  );
}