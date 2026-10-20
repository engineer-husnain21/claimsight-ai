/** Mirrors backend CreateClaimRequest validation so users get instant, field-level feedback. */

export interface CreateClaimInput {
  patient_name: string;
  policy_number: string;
  hospital_name: string;
  diagnosis: string;
  procedure: string;
  amount_claimed: number;
}

export type ClaimField = keyof CreateClaimInput;
export type ClaimFieldErrors = Partial<Record<ClaimField, string>>;

export const TEXT_LIMITS: Record<Exclude<ClaimField, "amount_claimed">, [number, number]> = {
  patient_name: [2, 255],
  policy_number: [3, 50],
  hospital_name: [2, 255],
  diagnosis: [2, 2000],
  procedure: [2, 255],
};

export const MAX_AMOUNT = 100_000_000;
const POLICY_NUMBER_PATTERN = /^[A-Za-z0-9-]+$/;
const AMOUNT_PATTERN = /^\d+$/;

const LABELS: Record<ClaimField, string> = {
  patient_name: "Patient name",
  policy_number: "Policy number",
  hospital_name: "Hospital name",
  diagnosis: "Diagnosis",
  procedure: "Procedure",
  amount_claimed: "Amount",
};

export type ValidationResult =
  | { ok: true; value: CreateClaimInput }
  | { ok: false; errors: ClaimFieldErrors };

function readText(raw: Record<string, unknown>, field: ClaimField): string {
  const value = raw[field];
  return typeof value === "string" ? value.trim() : "";
}

function readAmount(raw: unknown): number | null {
  if (typeof raw === "number") {
    return Number.isInteger(raw) ? raw : null;
  }
  if (typeof raw === "string") {
    const cleaned = raw.replace(/[,\s]/g, "");
    return AMOUNT_PATTERN.test(cleaned) ? Number(cleaned) : null;
  }
  return null;
}

export function validateClaimInput(raw: Record<string, unknown>): ValidationResult {
  const errors: ClaimFieldErrors = {};
  const text = {} as Record<Exclude<ClaimField, "amount_claimed">, string>;

  for (const field of Object.keys(TEXT_LIMITS) as (keyof typeof TEXT_LIMITS)[]) {
    const [min, max] = TEXT_LIMITS[field];
    const value = readText(raw, field);
    text[field] = value;
    if (value.length < min) {
      errors[field] = `${LABELS[field]} must be at least ${min} characters.`;
    } else if (value.length > max) {
      errors[field] = `${LABELS[field]} must be at most ${max} characters.`;
    }
  }

  if (errors.policy_number === undefined && !POLICY_NUMBER_PATTERN.test(text.policy_number)) {
    errors.policy_number = "Use only letters, numbers and dashes.";
  }

  const amount = readAmount(raw.amount_claimed);
  if (amount === null) {
    errors.amount_claimed = "Enter a whole number.";
  } else if (amount <= 0 || amount > MAX_AMOUNT) {
    errors.amount_claimed = `Amount must be between 1 and ${MAX_AMOUNT.toLocaleString("en-US")}.`;
  }

  if (Object.keys(errors).length > 0 || amount === null) {
    return { ok: false, errors };
  }
  return { ok: true, value: { ...text, amount_claimed: amount } };
}