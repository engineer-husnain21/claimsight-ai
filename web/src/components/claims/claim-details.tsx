import { GlassCard } from "@/components/ui/glass-card";
import { formatAmount, formatDate } from "@/lib/utils/format";
import type { ClaimResponse } from "@/types/claims";

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-foreground/45">{label}</dt>
      <dd className={`mt-1 text-sm ${mono ? "font-mono text-accent-cyan" : ""}`}>{value}</dd>
    </div>
  );
}

export function ClaimDetails({ claim }: { claim: ClaimResponse }) {
  return (
    <GlassCard title="Claim details">
      <dl className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <Field label="Patient" value={claim.patient_name} />
        <Field label="Policy number" value={claim.policy_number} mono />
        <Field label="Hospital" value={claim.hospital_name} />
        <Field label="Amount claimed" value={formatAmount(claim.amount_claimed)} />
        <Field label="Diagnosis" value={claim.diagnosis} />
        <Field label="Procedure" value={claim.procedure} />
        <Field label="Submitted" value={formatDate(claim.created_at)} />
        <Field label="Last updated" value={formatDate(claim.updated_at)} />
      </dl>
    </GlassCard>
  );
}