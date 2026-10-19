import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="bg-linear-to-r from-accent-cyan via-accent-violet to-accent-pink bg-clip-text text-7xl font-bold text-transparent">
        404
      </p>
      <p className="text-foreground/70">This page could not be found.</p>
      <Link
        href="/"
        className="rounded-full border border-white/15 bg-white/5 px-5 py-2 text-sm backdrop-blur transition hover:bg-white/10"
      >
        Go home
      </Link>
    </main>
  );
}