import "server-only";

import { ApiError } from "@/lib/server/api-client";
import { authedRequest } from "@/lib/server/authed-api";
import type { ClaimListResponse, ClaimResponse, ClaimStatus } from "@/types/claims";

export const CLAIM_STATUSES: readonly ClaimStatus[] = [
  "submitted",
  "processing",
  "needs_review",
  "approved",
  "rejected",
];

const CLAIM_ID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export interface ClaimListQuery {
  status?: ClaimStatus;
  limit: number;
  offset: number;
}

export interface ClaimStats {
  total: number;
  byStatus: Record<ClaimStatus, number>;
}

/** Claim ids are UUIDs; anything else is rejected before reaching the backend. */
export function isValidClaimId(id: string): boolean {
  return CLAIM_ID_PATTERN.test(id);
}

/** Lists claims visible to the current user (submitters only see their own). */
export async function listClaims(query: ClaimListQuery): Promise<ClaimListResponse> {
  const params = new URLSearchParams({
    limit: String(query.limit),
    offset: String(query.offset),
  });
  if (query.status !== undefined) {
    params.set("status", query.status);
  }
  return authedRequest<ClaimListResponse>(`/claims?${params.toString()}`);
}

interface ClaimStatsApiResponse {
  total: number;
  by_status: Partial<Record<ClaimStatus, number>>;
}

/** Claim counts per status from the backend, in a single request. */
export async function getClaimStats(): Promise<ClaimStats> {
  const response = await authedRequest<ClaimStatsApiResponse>("/claims/stats");
  const byStatus = Object.fromEntries(
    CLAIM_STATUSES.map((status) => [status, response.by_status[status] ?? 0]),
  ) as Record<ClaimStatus, number>;

  return { total: response.total, byStatus };
}

/** Returns the claim, or null when it does not exist or the user may not see it. */
export async function getClaim(id: string): Promise<ClaimResponse | null> {
  if (!isValidClaimId(id)) {
    return null;
  }
  try {
    return await authedRequest<ClaimResponse>(`/claims/${id}`);
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 422)) {
      return null;
    }
    throw error;
  }
}