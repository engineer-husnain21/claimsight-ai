/** Mirrors backend ClaimStatus. */
export type ClaimStatus = "submitted" | "processing" | "needs_review" | "approved" | "rejected";

/** Statuses a reviewer may set (backend REVIEW_DECISIONS). */
export type ReviewDecision = "approved" | "rejected" | "needs_review";

/** Mirrors backend ClaimResponse. */
export interface ClaimResponse {
  id: string;
  claim_number: string;
  patient_name: string;
  policy_number: string;
  hospital_name: string;
  diagnosis: string;
  procedure: string;
  amount_claimed: number;
  status: ClaimStatus;
  risk_score: number | null;
  ai_summary: string | null;
  submitted_by: string;
  created_at: string;
  updated_at: string;
}

/** Mirrors backend paginated claim list response. */
export interface ClaimListResponse {
  items: ClaimResponse[];
  total: number;
  limit: number;
  offset: number;
}