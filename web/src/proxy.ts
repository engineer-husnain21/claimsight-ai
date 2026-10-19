import { NextResponse, type NextRequest } from "next/server";

import { ApiError, apiRequest } from "@/lib/server/api-client";
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  clearSessionCookies,
  isValidTokenResponse,
  setSessionCookies,
} from "@/lib/server/session-cookies";
import type { TokenResponse } from "@/types/auth";

const PUBLIC_PATHS = new Set(["/login"]);
const LOGIN_PATH = "/login";
const DEFAULT_AUTHENTICATED_PATH = "/dashboard";

function redirectTo(request: NextRequest, pathname: string, next?: string): NextResponse {
  const url = new URL(pathname, request.url);
  url.search = "";
  if (next !== undefined) {
    url.searchParams.set("next", next);
  }
  return NextResponse.redirect(url);
}

async function tryRefresh(refreshToken: string): Promise<TokenResponse | null> {
  try {
    const tokens = await apiRequest<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    });
    return isValidTokenResponse(tokens) ? tokens : null;
  } catch (error) {
    if (error instanceof ApiError) {
      return null;
    }
    throw error;
  }
}

/**
 * Optimistic route protection. Real authorization still happens in the backend,
 * which validates the access token on every API call.
 */
export async function proxy(request: NextRequest): Promise<NextResponse> {
  const { pathname, search } = request.nextUrl;
  const isPublic = PUBLIC_PATHS.has(pathname);
  const hasAccessToken = request.cookies.has(ACCESS_COOKIE);
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;

  if (hasAccessToken) {
    return isPublic ? redirectTo(request, DEFAULT_AUTHENTICATED_PATH) : NextResponse.next();
  }

  if (refreshToken) {
    const tokens = await tryRefresh(refreshToken);
    if (tokens !== null) {
      // Make the new tokens visible to server components in this same request.
      request.cookies.set(ACCESS_COOKIE, tokens.access_token);
      request.cookies.set(REFRESH_COOKIE, tokens.refresh_token);
      const response = isPublic
        ? redirectTo(request, DEFAULT_AUTHENTICATED_PATH)
        : NextResponse.next({ request: { headers: request.headers } });
      setSessionCookies(response, tokens);
      return response;
    }
  }

  const response = isPublic
    ? NextResponse.next()
    : redirectTo(request, LOGIN_PATH, `${pathname}${search}`);
  if (refreshToken) {
    clearSessionCookies(response);
  }
  return response;
}

export const config = {
  // Skip API routes, Next.js internals and static files (anything with a file extension).
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};