"use client";

import { AnimatePresence, MotionConfig, motion } from "motion/react";
import type { Variants } from "motion/react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import {
  MAX_AMOUNT,
  TEXT_LIMITS,
  validateClaimInput,
  type ClaimField,
  type ClaimFieldErrors,
} from "@/lib/utils/claim-validation";
import { GENERIC_ERROR_MESSAGE, readErrorMessage } from "@/lib/utils/read-error-message";

type FormValues = Record<ClaimField, string>;

const EMPTY_VALUES: FormValues = {
  patient_name: "",
  policy_number: "",
  hospital_name: "",
  diagnosis: "",
  procedure: "",
  amount_claimed: "",
};

const containerVariants: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut", staggerChildren: 0.06, delayChildren: 0.1 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

const INPUT_CLASS =
  "w-full rounded-xl border bg-white/5 px-4 py-3 text-sm outline-none transition placeholder:text-foreground/30 focus:bg-white/[0.07] focus:ring-4 disabled:opacity-60";

function inputStateClass(hasError: boolean): string {
  return hasError
    ? "border-rose-400/60 focus:border-rose-400 focus:ring-rose-400/15"
    : "border-white/10 focus:border-accent-cyan/70 focus:ring-accent-cyan/15";
}

function readFieldErrors(data: unknown): ClaimFieldErrors {
  if (typeof data === "object" && data !== null && "fields" in data) {
    const { fields } = data as { fields: unknown };
    if (typeof fields === "object" && fields !== null) {
      return fields as ClaimFieldErrors;
    }
  }
  return {};
}

interface FieldProps {
  field: ClaimField;
  label: string;
  placeholder: string;
  values: FormValues;
  errors: ClaimFieldErrors;
  disabled: boolean;
  onChange: (field: ClaimField, value: string) => void;
  multiline?: boolean;
  inputMode?: "text" | "numeric";
  className?: string;
}

function Field({
  field,
  label,
  placeholder,
  values,
  errors,
  disabled,
  onChange,
  multiline = false,
  inputMode = "text",
  className = "",
}: FieldProps) {
  const error = errors[field];
  const errorId = `${field}-error`;
  const maxLength =
    field === "amount_claimed" ? String(MAX_AMOUNT).length + 4 : TEXT_LIMITS[field][1];
  const common = {
    id: field,
    name: field,
    value: values[field],
    placeholder,
    disabled,
    maxLength,
    "aria-invalid": error !== undefined,
    "aria-describedby": error !== undefined ? errorId : undefined,
    className: `${INPUT_CLASS} ${inputStateClass(error !== undefined)}`,
  };

  return (
    <motion.div variants={itemVariants} className={`space-y-2 ${className}`}>
      <label htmlFor={field} className="text-sm font-medium text-foreground/80">
        {label}
      </label>
      {multiline ? (
        <textarea
          {...common}
          rows={3}
          onChange={(event) => onChange(field, event.target.value)}
          className={`${common.className} resize-none`}
        />
      ) : (
        <input
          {...common}
          type="text"
          inputMode={inputMode}
          autoComplete="off"
          onChange={(event) => onChange(field, event.target.value)}
        />
      )}
      <AnimatePresence>
        {error !== undefined && (
          <motion.p
            id={errorId}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden text-xs text-rose-300"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/** Claim submission form. Validates locally first, then submits through the BFF route. */
export function NewClaimForm() {
  const router = useRouter();
  const [values, setValues] = useState<FormValues>(EMPTY_VALUES);
  const [errors, setErrors] = useState<ClaimFieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(field: ClaimField, value: string): void {
    setValues((current) => ({ ...current, [field]: value }));
    if (errors[field] !== undefined) {
      setErrors((current) => ({ ...current, [field]: undefined }));
    }
  }

  async function postClaim(body: unknown): Promise<Response> {
    return fetch("/api/claims", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "same-origin",
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }
    setFormError(null);

    const result = validateClaimInput(values);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    setErrors({});
    setIsSubmitting(true);

    try {
      let response = await postClaim(result.value);

      if (response.status === 401) {
        // The access token may have expired; refresh once and retry.
        const refreshed = await fetch("/api/auth/refresh", {
          method: "POST",
          credentials: "same-origin",
        });
        if (!refreshed.ok) {
          router.replace(`/login?next=${encodeURIComponent("/claims/new")}`);
          return;
        }
        response = await postClaim(result.value);
      }

      const data: unknown = await response.json().catch(() => null);
      if (response.ok && typeof data === "object" && data !== null && "id" in data) {
        router.push(`/claims/${String((data as { id: unknown }).id)}`);
        return;
      }
      setErrors(readFieldErrors(data));
      setFormError(readErrorMessage(data));
    } catch {
      setFormError(GENERIC_ERROR_MESSAGE);
    }
    setIsSubmitting(false);
  }

  const fieldProps = { values, errors, disabled: isSubmitting, onChange: handleChange };

  return (
    <MotionConfig reducedMotion="user">
      <motion.form
        onSubmit={handleSubmit}
        noValidate
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl sm:p-8"
      >
        <div className="grid gap-5 sm:grid-cols-2">
          <Field field="patient_name" label="Patient name" placeholder="Ali Khan" {...fieldProps} />
          <Field
            field="policy_number"
            label="Policy number"
            placeholder="POL-12345"
            {...fieldProps}
          />
          <Field
            field="hospital_name"
            label="Hospital"
            placeholder="City Hospital"
            {...fieldProps}
          />
          <Field field="procedure" label="Procedure" placeholder="Appendectomy" {...fieldProps} />
          <Field
            field="diagnosis"
            label="Diagnosis"
            placeholder="Acute appendicitis with severe abdominal pain"
            multiline
            className="sm:col-span-2"
            {...fieldProps}
          />
          <Field
            field="amount_claimed"
            label="Amount claimed"
            placeholder="150000"
            inputMode="numeric"
            {...fieldProps}
          />
        </div>

        <AnimatePresence>
          {formError !== null && (
            <motion.p
              role="alert"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 overflow-hidden rounded-xl border border-accent-pink/30 bg-accent-pink/10 px-4 py-3 text-sm text-accent-pink"
            >
              {formError}
            </motion.p>
          )}
        </AnimatePresence>

        <motion.div variants={itemVariants} className="mt-8 flex justify-end">
          <motion.button
            type="submit"
            disabled={isSubmitting}
            whileHover={isSubmitting ? undefined : { scale: 1.02 }}
            whileTap={isSubmitting ? undefined : { scale: 0.98 }}
            className="flex items-center gap-2 rounded-xl bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-accent-violet/25 disabled:cursor-wait disabled:opacity-70"
          >
            {isSubmitting && (
              <motion.span
                aria-hidden="true"
                className="inline-block h-4 w-4 rounded-full border-2 border-white/30 border-t-white"
                animate={{ rotate: 360 }}
                transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
              />
            )}
            {isSubmitting ? "Submitting..." : "Submit claim"}
          </motion.button>
        </motion.div>
      </motion.form>
    </MotionConfig>
  );
}