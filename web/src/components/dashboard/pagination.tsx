import Link from "next/link";

interface PaginationProps {
  page: number;
  pageCount: number;
  buildHref: (page: number) => string;
}

export function Pagination({ page, pageCount, buildHref }: PaginationProps) {
  if (pageCount <= 1) {
    return null;
  }

  const linkClass =
    "rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs transition hover:bg-white/10";
  const disabledClass =
    "rounded-full border border-white/5 px-4 py-1.5 text-xs text-foreground/30";

  return (
    <div className="flex items-center justify-between text-xs text-foreground/50">
      <span>
        Page {page} of {pageCount}
      </span>
      <div className="flex gap-2">
        {page > 1 ? (
          <Link href={buildHref(page - 1)} className={linkClass}>
            Previous
          </Link>
        ) : (
          <span className={disabledClass}>Previous</span>
        )}
        {page < pageCount ? (
          <Link href={buildHref(page + 1)} className={linkClass}>
            Next
          </Link>
        ) : (
          <span className={disabledClass}>Next</span>
        )}
      </div>
    </div>
  );
}