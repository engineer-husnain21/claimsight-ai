import { redirect } from "next/navigation";

import { ApiError, apiRequest } from "@/lib/server/api-client";
import { getAccessToken } from "@/lib/server/session-cookies";
import type { UserResponse } from "@/types/auth";

async function loadCurrentUser(accessToken: string): Promise<UserResponse | null> {
  try {
    return await apiRequest<UserResponse>("/auth/me", { accessToken });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

/** Temporary placeholder; the real dashboard is built on Day 13. */
export default async function DashboardPage() {
  const accessToken = await getAccessToken();
  if (accessToken === null) {
    redirect("/login");
  }

  const user = await loadCurrentUser(accessToken);
  if (user === null) {
    redirect("/login");
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-semibold">Welcome, {user.full_name}</h1>
      <p className="text-sm opacity-70">Role: {user.role}</p>
    </main>
  );
}