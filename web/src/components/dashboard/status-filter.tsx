import Link from "next/link";

import { statusLabel } from "@/components/claims/status-badge";
import type { ClaimStatus } from "@/types/claims";

interface StatusFilterProps {
  statuses: readonly ClaimStatus[];
  active: ClaimStatus | undefined;
}

export function StatusFilter({ statuses, active }: StatusFilterProps) {
  const options: { href: string; label: string; isActive: boolean }[] = [
    { href: "/dashboard", label: "All", isActive: active === undefined },
    ...statuses.map((status) => ({
      href: `/dashboard?status=${status}`,
      label: statusLabel(status),
      isActive: active === status,
    })),
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <Link
          key={option.href}
          href={option.href}
          className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
            option.isActive
              ? "border-accent-violet/50 bg-accent-violet/15 text-foreground"
              : "border-white/10 bg-white/5 text-foreground/60 hover:text-foreground"
          }`}
        >
          {option.label}
        </Link>
      ))}
    </div>
  );
}