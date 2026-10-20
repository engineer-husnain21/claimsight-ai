import type { Metadata } from "next";

import { ClaimsTable } from "@/components/dashboard/claims-table";
import { Pagination } from "@/components/dashboard/pagination";
import { StatCards, type StatCardData } from "@/components/dashboard/stat-cards";
import { StatusFilter } from "@/components/dashboard/status-filter";
import { getCurrentUser } from "@/lib/server/authed-api";
import { CLAIM_STATUSES, getClaimStats, listClaims } from "@/lib/server/claims-api";
import type { ClaimStatus } from "@/types/claims";

export const metadata: Metadata = {
  title: "Dashboard | ClaimSight AI",
};

const PAGE_SIZE = 10;
const MAX_PAGE = 1000;

interface DashboardPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function parseStatus(value: string | string[] | undefined): ClaimStatus | undefined {
  return typeof value === "string" && (CLAIM_STATUSES as readonly string[]).includes(value)
    ? (value as ClaimStatus)
    : undefined;
}

function parsePage(value: string | string[] | undefined): number {
  const page = typeof value === "string" ? Number.parseInt(value, 10) : 1;
  return Number.isInteger(page) && page >= 1 && page <= MAX_PAGE ? page : 1;
}

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const params = await searchParams;
  const status = parseStatus(params.status);
  const page = parsePage(params.page);

  const [user, stats, claims] = await Promise.all([
    getCurrentUser(),
    getClaimStats(),
    listClaims({ status, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE }),
  ]);

  const isReviewer = user.role === "reviewer" || user.role === "admin";
  const pageCount = Math.max(1, Math.ceil(claims.total / PAGE_SIZE));

  const statCards: StatCardData[] = [
    { label: "Total claims", value: stats.total, accent: "bg-accent-violet" },
    { label: "Submitted", value: stats.byStatus.submitted, accent: "bg-sky-400" },
    { label: "Processing", value: stats.byStatus.processing, accent: "bg-violet-400" },
    { label: "Needs review", value: stats.byStatus.needs_review, accent: "bg-amber-400" },
    { label: "Approved", value: stats.byStatus.approved, accent: "bg-emerald-400" },
    { label: "Rejected", value: stats.byStatus.rejected, accent: "bg-rose-400" },
  ];

  const buildPageHref = (target: number): string => {
    const query = new URLSearchParams({ page: String(target) });
    if (status !== undefined) {
      query.set("status", status);
    }
    return `/dashboard?${query.toString()}`;
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome back,{" "}
          <span className="bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink bg-clip-text text-transparent">
            {user.full_name}
          </span>
        </h1>
        <p className="mt-1 text-sm text-foreground/55">
          {isReviewer
            ? "Review incoming claims with AI-assisted insights."
            : "Track the status of the claims you have submitted."}
        </p>
      </div>

      <StatCards stats={statCards} />

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Claims</h2>
          <StatusFilter statuses={CLAIM_STATUSES} active={status} />
        </div>
        <ClaimsTable claims={claims.items} showRisk={isReviewer} />
        <Pagination page={page} pageCount={pageCount} buildHref={buildPageHref} />
      </section>
    </div>
  );
}