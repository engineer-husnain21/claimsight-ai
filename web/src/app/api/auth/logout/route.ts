import { NextResponse, type NextRequest } from "next/server";

import { isSameOriginRequest } from "@/lib/server/request-guards";
import { jsonError } from "@/lib/server/route-responses";
import { clearSessionCookies } from "@/lib/server/session-cookies";

export function POST(request: NextRequest): NextResponse {
  if (!isSameOriginRequest(request)) {
    return jsonError(403, "Forbidden.");
  }
  const response = NextResponse.json({ ok: true });
  clearSessionCookies(response);
  return response;
}