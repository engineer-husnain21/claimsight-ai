"use client";

import dynamic from "next/dynamic";

import type { OrbSegment } from "@/components/three/claims-orb";

// WebGL only exists in the browser, so the 3D scene is never server-rendered.
const ClaimsOrb = dynamic(() => import("@/components/three/claims-orb"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse rounded-full bg-white/5" />,
});

export interface OrbLegendItem extends OrbSegment {
  label: string;
}

export function ClaimsOrbCard({ items }: { items: OrbLegendItem[] }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur-xl">
      <div className="h-40 w-40 shrink-0 sm:h-44 sm:w-44">
        <ClaimsOrb segments={items} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wider text-foreground/50">
          Claim mix
        </p>
        <ul className="mt-3 space-y-1.5">
          {items.map((item) => (
            <li key={item.label} className="flex items-center gap-2 text-xs text-foreground/70">
              <span
                className="h-2 w-2 shrink-0 rounded-full"
                style={{ backgroundColor: item.color, boxShadow: `0 0 8px ${item.color}` }}
              />
              <span className="flex-1">{item.label}</span>
              <span className="tabular-nums text-foreground/90">{item.count}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}