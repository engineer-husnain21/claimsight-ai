import Link from "next/link";

import { LogoutButton } from "@/components/layout/logout-button";
import { NavLinks } from "@/components/layout/nav-links";
import type { UserResponse, UserRole } from "@/types/auth";

const ROLE_STYLES: Record<UserRole, string> = {
  submitter: "border-accent-cyan/30 bg-accent-cyan/10 text-accent-cyan",
  reviewer: "border-accent-violet/30 bg-accent-violet/10 text-accent-violet",
  admin: "border-accent-pink/30 bg-accent-pink/10 text-accent-pink",
};

interface AppHeaderProps {
  user: UserResponse;
}

export function AppHeader({ user }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-background/60 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex items-center gap-6">
          <Link
            href="/dashboard"
            className="bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink bg-clip-text text-lg font-bold tracking-tight text-transparent"
          >
            ClaimSight AI
          </Link>
          <NavLinks />
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium leading-tight">{user.full_name}</p>
            <p className="text-xs text-foreground/50">{user.email}</p>
          </div>
          <span
            className={`rounded-full border px-3 py-1 text-xs font-medium capitalize ${ROLE_STYLES[user.role]}`}
          >
            {user.role}
          </span>
          <LogoutButton />
        </div>
      </div>
    </header>
  );
}