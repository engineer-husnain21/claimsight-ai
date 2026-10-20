interface GlassCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function GlassCard({ title, children, className = "" }: GlassCardProps) {
  return (
    <section
      className={`rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl ${className}`}
    >
      {title !== undefined && (
        <h2 className="mb-5 text-xs font-semibold uppercase tracking-wider text-foreground/50">
          {title}
        </h2>
      )}
      {children}
    </section>
  );
}