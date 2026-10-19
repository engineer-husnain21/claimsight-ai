import "server-only";

import { cookies } from "next/headers";
import type { NextRequest, NextResponse } from "next/server";

import type { TokenResponse } from "@/types/auth";

export const ACCESS_COOKIE = "cs_access";
export const REFRESH_COOKIE = "cs_refresh";

const DEFAULT_ACCESS_MAX_AGE_SECONDS = 15 * 60;
const REFRESH_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;

interface CookieOptions {
  httpOnly: true;
  secure: boolean;
  sameSite: "lax";
  path: string;
}

function baseCookieOptions(): CookieOptions {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
  };
}

/** Checks that the backend returned usable tokens before they are stored. */
export function isValidTokenResponse(tokens: TokenResponse): boolean {
  return (
    typeof tokens.access_token === "string" &&
    tokens.access_token.length > 0 &&
    typeof tokens.refresh_token === "string" &&
    tokens.refresh_token.length > 0
  );
}

/** Stores both tokens in httpOnly cookies. Tokens never reach browser JavaScript. */
export function setSessionCookies(response: NextResponse, tokens: TokenResponse): void {
  if (!isValidTokenResponse(tokens)) {
    throw new Error("Backend returned an invalid token response.");
  }
  const accessMaxAge =
    Number.isInteger(tokens.expires_in) && tokens.expires_in > 0
      ? tokens.expires_in
      : DEFAULT_ACCESS_MAX_AGE_SECONDS;

  response.cookies.set(ACCESS_COOKIE, tokens.access_token, {
    ...baseCookieOptions(),
    maxAge: accessMaxAge,
  });
  response.cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
    ...baseCookieOptions(),
    maxAge: REFRESH_MAX_AGE_SECONDS,
  });
}

/** Removes both session cookies. */
export function clearSessionCookies(response: NextResponse): void {
  response.cookies.set(ACCESS_COOKIE, "", { ...baseCookieOptions(), maxAge: 0 });
  response.cookies.set(REFRESH_COOKIE, "", { ...baseCookieOptions(), maxAge: 0 });
}

/** Reads the refresh token cookie from an incoming request. */
export function readRefreshToken(request: NextRequest): string | null {
  return request.cookies.get(REFRESH_COOKIE)?.value ?? null;
}

/** Reads the access token in server components. */
export async function getAccessToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(ACCESS_COOKIE)?.value ?? null;
}