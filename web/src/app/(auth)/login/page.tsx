import type { Metadata } from "next";

import { LoginForm } from "@/components/auth/login-form";
import { getSafeRedirectPath } from "@/lib/utils/safe-redirect";

export const metadata: Metadata = {
  title: "Sign in | ClaimSight AI",
};

interface LoginPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const { next } = await searchParams;

  return (
    <main className="flex min-h-screen flex-1 items-center justify-center px-4 py-12">
      <LoginForm redirectTo={getSafeRedirectPath(next)} />
    </main>
  );
}