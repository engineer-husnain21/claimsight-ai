import "server-only";

import type { NextRequest } from "next/server";

/** Rejects cross-site requests (CSRF layer on top of SameSite cookies). */
export function isSameOriginRequest(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  return origin !== null && origin === request.nextUrl.origin;
}