import { NextResponse, type NextRequest } from "next/server";

import { ApiError, apiRequest } from "@/lib/server/api-client";
import { isValidClaimId } from "@/lib/server/claims-api";
import { isSameOriginRequest } from "@/lib/server/request-guards";
import { jsonError } from "@/lib/server/route-responses";
import { ACCESS_COOKIE } from "@/lib/server/session-cookies";

interface ClaimRouteContext {
  params: Promise<{ id: string }>;
}

const UNAVAILABLE_MESSAGE = "The AI service is unavailable. Please try again.";

function mapBackendError(status: number): NextResponse {
  switch (status) {
    case 401:
      return jsonError(401, "Session expired. Please sign in again.");
    case 403:
      return jsonError(403, "You cannot run an AI review on this claim.");
    case 404:
      return jsonError(404, "Claim not found.");
    case 429:
      return jsonError(429, "Too many requests. Please wait a moment.");
    default:
      return jsonError(502, UNAVAILABLE_MESSAGE);
  }
}

/** Runs the multi-agent AI review for a claim through the backend. */
export async function POST(
  request: NextRequest,
  context: ClaimRouteContext,
): Promise<NextResponse> {
  if (!isSameOriginRequest(request)) {
    return jsonError(403, "Forbidden.");
  }

  const { id } = await context.params;
  if (!isValidClaimId(id)) {
    return jsonError(404, "Claim not found.");
  }

  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  if (!accessToken) {
    return jsonError(401, "Session expired. Please sign in again.");
  }

  try {
    await apiRequest<unknown>(`/claims/${id}/ai-reviews`, { method: "POST", accessToken });
    return NextResponse.json({ ok: true }, { status: 201 });
  } catch (error) {
    if (error instanceof ApiError) {
      return mapBackendError(error.status);
    }
    return jsonError(502, UNAVAILABLE_MESSAGE);
  }
}