import { RiskBadge } from "@/components/claims/risk-badge";
import { GlassCard } from "@/components/ui/glass-card";
import { formatAmount } from "@/lib/utils/format";
import type {
  ExtractionResult,
  FraudResult,
  IssueSeverity,
  ValidationResult,
} from "@/types/claim-review";

const SEVERITY_STYLES: Record<IssueSeverity, string> = {
  info: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  warning: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  critical: "border-rose-400/40 bg-rose-400/15 text-rose-300",
};

const UNKNOWN_STYLE = "border-white/15 bg-white/5 text-foreground/70";

function textOrDash(value: string | null | undefined): string {
  return value === null || value === undefined || value.trim() === "" ? "-" : value;
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-foreground/45">{label}</dt>
      <dd className="mt-1 text-sm">{value}</dd>
    </div>
  );
}

function RuleCode({ code }: { code: string }) {
  return (
    <span className="shrink-0 rounded-md border border-accent-cyan/30 bg-accent-cyan/10 px-2 py-0.5 font-mono text-xs text-accent-cyan">
      {code}
    </span>
  );
}

function ChipList({ items, empty }: { items: string[]; empty: string }) {
  if (items.length === 0) {
    return <p className="text-sm text-foreground/45">{empty}</p>;
  }
  return (
    <ul className="flex flex-wrap gap-2">
      {items.map((item, index) => (
        <li
          key={`${item}-${index}`}
          className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs"
        >
          {item}
        </li>
      ))}
    </ul>
  );
}

export function ExtractionPanel({ extraction }: { extraction: ExtractionResult }) {
  const lineItems = extraction.line_items ?? [];
  const preauth =
    extraction.has_preauthorization === null || extraction.has_preauthorization === undefined
      ? "Unknown"
      : extraction.has_preauthorization
        ? "Yes"
        : "No";

  return (
    <GlassCard title="Extraction agent">
      <dl className="grid grid-cols-2 gap-4">
        <Field label="Admission type" value={textOrDash(extraction.admission_type)} />
        <Field label="Pre-authorization" value={preauth} />
        <Field label="Admission date" value={textOrDash(extraction.admission_date)} />
        <Field label="Discharge date" value={textOrDash(extraction.discharge_date)} />
        <Field
          label="Total amount"
          value={
            extraction.total_amount === null || extraction.total_amount === undefined
              ? "-"
              : formatAmount(extraction.total_amount)
          }
        />
      </dl>

      <div className="mt-5 space-y-2">
        <h3 className="text-xs text-foreground/45">Procedures</h3>
        <ChipList items={extraction.procedures ?? []} empty="None extracted." />
      </div>

      <div className="mt-5 space-y-2">
        <h3 className="text-xs text-foreground/45">Documents provided</h3>
        <ChipList items={extraction.documents_provided ?? []} empty="No documents listed." />
      </div>

      {lineItems.length > 0 && (
        <div className="mt-5 space-y-2">
          <h3 className="text-xs text-foreground/45">Line items</h3>
          <ul className="divide-y divide-white/5 rounded-xl border border-white/10">
            {lineItems.map((item, index) => (
              <li
                key={`${item.description}-${index}`}
                className="flex justify-between gap-4 px-4 py-2 text-sm"
              >
                <span>{item.description}</span>
                <span className="tabular-nums text-foreground/70">{formatAmount(item.amount)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </GlassCard>
  );
}

export function ValidationPanel({ validation }: { validation: ValidationResult }) {
  const issues = validation.issues ?? [];

  return (
    <GlassCard title="Validation agent">
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={`rounded-full border px-3 py-1 text-xs font-medium ${
            validation.is_compliant
              ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
              : "border-amber-400/30 bg-amber-400/10 text-amber-300"
          }`}
        >
          {validation.is_compliant ? "Policy compliant" : "Policy issues found"}
        </span>
        <span className="text-xs text-foreground/50">
          Eligible amount:{" "}
          <span className="text-foreground/80">
            {validation.eligible_amount === null || validation.eligible_amount === undefined
              ? "-"
              : formatAmount(validation.eligible_amount)}
          </span>
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {issues.length === 0 ? (
          <p className="text-sm text-foreground/45">No policy issues.</p>
        ) : (
          issues.map((issue, index) => (
            <div
              key={`${issue.rule_code}-${index}`}
              className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3"
            >
              <RuleCode code={issue.rule_code} />
              <p className="flex-1 text-sm text-foreground/80">{issue.message}</p>
              <span
                className={`shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize ${
                  SEVERITY_STYLES[issue.severity] ?? UNKNOWN_STYLE
                }`}
              >
                {issue.severity}
              </span>
            </div>
          ))
        )}
      </div>

      <p className="mt-5 text-sm leading-relaxed text-foreground/65">
        {textOrDash(validation.reasoning)}
      </p>
    </GlassCard>
  );
}

export function FraudPanel({ fraud }: { fraud: FraudResult }) {
  const flags = fraud.flags ?? [];

  return (
    <GlassCard title="Fraud agent">
      <RiskBadge score={fraud.risk_score} />

      <div className="mt-5 space-y-3">
        {flags.length === 0 ? (
          <p className="text-sm text-foreground/45">No fraud indicators found.</p>
        ) : (
          flags.map((flag, index) => (
            <div
              key={`${flag.rule_code}-${index}`}
              className="flex items-start gap-3 rounded-xl border border-rose-400/20 bg-rose-400/[0.05] p-3"
            >
              <RuleCode code={flag.rule_code} />
              <p className="text-sm text-foreground/80">{flag.message}</p>
            </div>
          ))
        )}
      </div>

      <p className="mt-5 text-sm leading-relaxed text-foreground/65">
        {textOrDash(fraud.reasoning)}
      </p>
    </GlassCard>
  );
}