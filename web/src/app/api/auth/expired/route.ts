import { NextResponse, type NextRequest } from "next/server";

import { clearSessionCookies } from "@/lib/server/session-cookies";

/** Clears a session the backend rejected and sends the user to the login page. */
export function GET(request: NextRequest): NextResponse {
  const response = NextResponse.redirect(new URL("/login", request.url));
  clearSessionCookies(response);
  return response;
}