import { NextResponse, type NextRequest } from "next/server";

import { ApiError, apiRequest } from "@/lib/server/api-client";
import { isSameOriginRequest } from "@/lib/server/request-guards";
import { jsonError } from "@/lib/server/route-responses";
import { ACCESS_COOKIE } from "@/lib/server/session-cookies";
import { validateClaimInput } from "@/lib/utils/claim-validation";
import type { ClaimResponse } from "@/types/claims";

function mapBackendError(status: number): NextResponse {
  switch (status) {
    case 401:
      return jsonError(401, "Session expired. Please sign in again.");
    case 422:
      return jsonError(400, "Please check the claim details.");
    case 429:
      return jsonError(429, "Too many requests. Please wait a moment.");
    default:
      return jsonError(502, "Could not submit the claim. Please try again.");
  }
}

/** Submits a new claim for the signed-in user. */
export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!isSameOriginRequest(request)) {
    return jsonError(403, "Forbidden.");
  }

  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  if (!accessToken) {
    return jsonError(401, "Session expired. Please sign in again.");
  }

  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return jsonError(400, "Please check the claim details.");
  }
  if (typeof raw !== "object" || raw === null) {
    return jsonError(400, "Please check the claim details.");
  }

  const result = validateClaimInput(raw as Record<string, unknown>);
  if (!result.ok) {
    return NextResponse.json(
      { error: "Please check the claim details.", fields: result.errors },
      { status: 400 },
    );
  }

  try {
    const claim = await apiRequest<ClaimResponse>("/claims", {
      method: "POST",
      body: result.value,
      accessToken,
    });
    return NextResponse.json({ id: claim.id }, { status: 201 });
  } catch (error) {
    if (error instanceof ApiError) {
      return mapBackendError(error.status);
    }
    return jsonError(502, "Could not submit the claim. Please try again.");
  }
}