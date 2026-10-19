import "server-only";

import { NextResponse } from "next/server";

/** Builds a JSON error response with a generic, safe message. */
export function jsonError(status: number, message: string): NextResponse {
  return NextResponse.json({ error: message }, { status });
}