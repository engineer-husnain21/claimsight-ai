import { NextResponse, type NextRequest } from "next/server";

import { ApiError, apiRequest } from "@/lib/server/api-client";
import { isSameOriginRequest } from "@/lib/server/request-guards";
import { jsonError } from "@/lib/server/route-responses";
import {
  clearSessionCookies,
  readRefreshToken,
  setSessionCookies,
} from "@/lib/server/session-cookies";
import type { TokenResponse } from "@/types/auth";

function unauthorized(): NextResponse {
  const response = jsonError(401, "Session expired. Please sign in again.");
  clearSessionCookies(response);
  return response;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!isSameOriginRequest(request)) {
    return jsonError(403, "Forbidden.");
  }

  const refreshToken = readRefreshToken(request);
  if (refreshToken === null) {
    return unauthorized();
  }

  try {
    const tokens = await apiRequest<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    });
    const response = NextResponse.json({ ok: true });
    setSessionCookies(response, tokens);
    return response;
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 422)) {
      return unauthorized();
    }
    return jsonError(502, "Session refresh is temporarily unavailable.");
  }
}