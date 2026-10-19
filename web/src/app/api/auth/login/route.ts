import { NextResponse, type NextRequest } from "next/server";

import { ApiError, apiRequest } from "@/lib/server/api-client";
import { isSameOriginRequest } from "@/lib/server/request-guards";
import { jsonError } from "@/lib/server/route-responses";
import { setSessionCookies } from "@/lib/server/session-cookies";
import type { TokenResponse } from "@/types/auth";

const MAX_EMAIL_LENGTH = 254;
const MAX_PASSWORD_LENGTH = 128;

interface LoginBody {
  email: string;
  password: string;
}

function parseLoginBody(value: unknown): LoginBody | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const { email, password } = value as Record<string, unknown>;
  if (typeof email !== "string" || typeof password !== "string") {
    return null;
  }
  const trimmedEmail = email.trim();
  if (trimmedEmail.length === 0 || trimmedEmail.length > MAX_EMAIL_LENGTH) {
    return null;
  }
  if (password.length === 0 || password.length > MAX_PASSWORD_LENGTH) {
    return null;
  }
  return { email: trimmedEmail, password };
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!isSameOriginRequest(request)) {
    return jsonError(403, "Forbidden.");
  }

  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return jsonError(400, "Invalid request.");
  }

  const body = parseLoginBody(raw);
  if (body === null) {
    return jsonError(401, "Invalid email or password.");
  }

  try {
    const tokens = await apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body,
    });
    const response = NextResponse.json({ ok: true });
    setSessionCookies(response, tokens);
    return response;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401 || error.status === 422) {
        return jsonError(401, "Invalid email or password.");
      }
      if (error.status === 429) {
        return jsonError(429, "Too many attempts. Please try again later.");
      }
    }
    return jsonError(502, "Login is temporarily unavailable.");
  }
}