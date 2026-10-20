"use client";

import { motion } from "motion/react";
import { useRouter } from "next/navigation";

import { RiskBadge } from "@/components/claims/risk-badge";
import { StatusBadge } from "@/components/claims/status-badge";
import { formatAmount, formatDate } from "@/lib/utils/format";
import type { ClaimResponse } from "@/types/claims";

interface ClaimsTableProps {
  claims: ClaimResponse[];
  showRisk: boolean;
}

export function ClaimsTable({ claims, showRisk }: ClaimsTableProps) {
  const router = useRouter();

  if (claims.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] px-6 py-16 text-center text-sm text-foreground/50">
        No claims found.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="border-b border-white/10 text-xs uppercase tracking-wider text-foreground/45">
          <tr>
            <th className="px-5 py-3 font-medium">Claim</th>
            <th className="px-5 py-3 font-medium">Patient</th>
            <th className="px-5 py-3 font-medium">Hospital</th>
            <th className="px-5 py-3 text-right font-medium">Amount</th>
            <th className="px-5 py-3 font-medium">Status</th>
            {showRisk && <th className="px-5 py-3 font-medium">Risk</th>}
            <th className="px-5 py-3 font-medium">Submitted</th>
          </tr>
        </thead>
        <tbody>
          {claims.map((claim, index) => (
            <motion.tr
              key={claim.id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35, delay: index * 0.04, ease: "easeOut" }}
              onClick={() => router.push(`/claims/${claim.id}`)}
              className="cursor-pointer border-b border-white/5 transition-colors last:border-0 hover:bg-white/[0.05]"
            >
              <td className="px-5 py-4 font-mono text-xs text-accent-cyan">
                {claim.claim_number}
              </td>
              <td className="px-5 py-4">
                <p className="font-medium">{claim.patient_name}</p>
                <p className="text-xs text-foreground/45">{claim.diagnosis}</p>
              </td>
              <td className="px-5 py-4 text-foreground/70">{claim.hospital_name}</td>
              <td className="px-5 py-4 text-right tabular-nums">
                {formatAmount(claim.amount_claimed)}
              </td>
              <td className="px-5 py-4">
                <StatusBadge status={claim.status} />
              </td>
              {showRisk && (
                <td className="px-5 py-4">
                  <RiskBadge score={claim.risk_score} />
                </td>
              )}
              <td className="px-5 py-4 text-foreground/55">{formatDate(claim.created_at)}</td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}