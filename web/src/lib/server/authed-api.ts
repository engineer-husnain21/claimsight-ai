import "server-only";

import { redirect } from "next/navigation";
import { cache } from "react";

import { ApiError, apiRequest } from "@/lib/server/api-client";
import { getAccessToken } from "@/lib/server/session-cookies";
import type { UserResponse } from "@/types/auth";

type AuthedRequestOptions = Omit<NonNullable<Parameters<typeof apiRequest>[1]>, "accessToken">;

// Clears stale cookies first; redirecting straight to /login would loop through the proxy.
const SESSION_EXPIRED_PATH = "/api/auth/expired";

/** Calls the backend as the signed-in user. Sends the user to sign in again on 401. */
export async function authedRequest<T>(
  path: string,
  options: AuthedRequestOptions = {},
): Promise<T> {
  const accessToken = await getAccessToken();
  if (accessToken === null) {
    redirect(SESSION_EXPIRED_PATH);
  }

  try {
    return await apiRequest<T>(path, { ...options, accessToken });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirect(SESSION_EXPIRED_PATH);
    }
    throw error;
  }
}

/** Current user, fetched once per request even if several components ask for it. */
export const getCurrentUser = cache(
  async (): Promise<UserResponse> => authedRequest<UserResponse>("/auth/me"),
);