import "server-only";

import { authedRequest } from "@/lib/server/authed-api";
import type { ClaimListResponse, ClaimStatus } from "@/types/claims";

export const CLAIM_STATUSES: readonly ClaimStatus[] = [
  "submitted",
  "needs_review",
  "approved",
  "rejected",
];

export interface ClaimListQuery {
  status?: ClaimStatus;
  limit: number;
  offset: number;
}

export interface ClaimStats {
  total: number;
  byStatus: Record<ClaimStatus, number>;
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

/** Counts claims per status using the list endpoint's total, in parallel. */
export async function getClaimStats(): Promise<ClaimStats> {
  const [all, ...perStatus] = await Promise.all([
    listClaims({ limit: 1, offset: 0 }),
    ...CLAIM_STATUSES.map((status) => listClaims({ status, limit: 1, offset: 0 })),
  ]);

  const byStatus = Object.fromEntries(
    CLAIM_STATUSES.map((status, index) => [status, perStatus[index].total]),
  ) as Record<ClaimStatus, number>;

  return { total: all.total, byStatus };
}