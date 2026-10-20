import { NextResponse, type NextRequest } from "next/server";

import { ApiError, apiRequest } from "@/lib/server/api-client";
import { isValidClaimId } from "@/lib/server/claims-api";
import { isSameOriginRequest } from "@/lib/server/request-guards";
import { jsonError } from "@/lib/server/route-responses";
import { ACCESS_COOKIE } from "@/lib/server/session-cookies";
import type { ReviewDecision } from "@/types/claims";

interface ClaimRouteContext {
  params: Promise<{ id: string }>;
}

interface DecisionBody {
  status: ReviewDecision;
  note: string | null;
}

const REVIEW_DECISIONS: readonly ReviewDecision[] = ["approved", "rejected", "needs_review"];
// Matches backend ReviewClaimRequest.note max_length.
const MAX_NOTE_LENGTH = 1000;

function parseDecisionBody(value: unknown): DecisionBody | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const { status, note } = value as Record<string, unknown>;
  if (typeof status !== "string" || !(REVIEW_DECISIONS as readonly string[]).includes(status)) {
    return null;
  }
  if (note !== undefined && note !== null && typeof note !== "string") {
    return null;
  }
  const trimmedNote = typeof note === "string" ? note.trim() : "";
  if (trimmedNote.length > MAX_NOTE_LENGTH) {
    return null;
  }
  return {
    status: status as ReviewDecision,
    note: trimmedNote.length > 0 ? trimmedNote : null,
  };
}

function mapBackendError(status: number): NextResponse {
  switch (status) {
    case 401:
      return jsonError(401, "Session expired. Please sign in again.");
    case 403:
      return jsonError(403, "You cannot decide on this claim.");
    case 404:
      return jsonError(404, "Claim not found.");
    case 422:
      return jsonError(400, "Invalid decision.");
    case 429:
      return jsonError(429, "Too many requests. Please wait a moment.");
    default:
      return jsonError(502, "Could not save the decision. Please try again.");
  }
}

/** Saves the human reviewer's decision on a claim. */
export async function PATCH(
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

  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return jsonError(400, "Invalid decision.");
  }

  const body = parseDecisionBody(raw);
  if (body === null) {
    return jsonError(400, "Invalid decision.");
  }

  try {
    await apiRequest<unknown>(`/claims/${id}/status`, {
      method: "PATCH",
      body,
      accessToken,
    });
    return NextResponse.json({ ok: true });
  } catch (error) {
    if (error instanceof ApiError) {
      return mapBackendError(error.status);
    }
    return jsonError(502, "Could not save the decision. Please try again.");
  }
}