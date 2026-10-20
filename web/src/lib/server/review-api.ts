import "server-only";

import { ApiError } from "@/lib/server/api-client";
import { authedRequest } from "@/lib/server/authed-api";
import { isValidClaimId } from "@/lib/server/claims-api";
import type { ClaimReviewResponse } from "@/types/claim-review";

/** Latest AI review for a claim, or null when none exists or the user may not see it. */
export async function getLatestReview(claimId: string): Promise<ClaimReviewResponse | null> {
  if (!isValidClaimId(claimId)) {
    return null;
  }
  try {
    return await authedRequest<ClaimReviewResponse>(`/claims/${claimId}/ai-reviews/latest`);
  } catch (error) {
    if (error instanceof ApiError && (error.status === 403 || error.status === 404)) {
      return null;
    }
    throw error;
  }
}