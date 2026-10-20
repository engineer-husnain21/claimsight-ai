export type Recommendation = "approved" | "rejected" | "needs_review";
export type IssueSeverity = "info" | "warning" | "critical";
export type RiskLevel = "low" | "medium" | "high";

export interface LineItem {
  description: string;
  amount: number;
}

export interface ExtractionResult {
  patient_name: string | null;
  diagnosis: string | null;
  procedures: string[];
  admission_type: string | null;
  admission_date: string | null;
  discharge_date: string | null;
  line_items: LineItem[];
  total_amount: number | null;
  documents_provided: string[];
  has_preauthorization: boolean | null;
}

export interface ValidationIssue {
  rule_code: string;
  severity: IssueSeverity;
  message: string;
}

export interface ValidationResult {
  is_compliant: boolean;
  issues: ValidationIssue[];
  eligible_amount: number | null;
  reasoning: string;
}

export interface FraudFlag {
  rule_code: string;
  message: string;
}

export interface FraudResult {
  risk_score: number;
  flags: FraudFlag[];
  reasoning: string;
  risk_level: RiskLevel;
}

export interface SummaryResult {
  summary: string;
  key_points: string[];
  recommendation: Recommendation;
}

export interface AgentStep {
  agent: string;
  duration_ms: number;
}

export interface ClaimReviewResult {
  extraction: ExtractionResult;
  validation: ValidationResult;
  fraud: FraudResult;
  summary: SummaryResult;
  steps: AgentStep[];
}

/** Mirrors backend ClaimReviewResponse. */
export interface ClaimReviewResponse {
  id: string;
  claim_id: string;
  requested_by: string;
  recommendation: Recommendation;
  risk_score: number;
  eligible_amount: number | null;
  llm_model: string;
  created_at: string;
  result: ClaimReviewResult;
}