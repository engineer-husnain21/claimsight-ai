import { getCurrentUser } from "@/lib/server/authed-api";

/** Temporary content; the real dashboard comes in the next part. */
export default async function DashboardPage() {
  const user = await getCurrentUser();

  return (
    <section className="py-20 text-center">
      <h1 className="text-3xl font-semibold">Welcome, {user.full_name}</h1>
      <p className="mt-2 text-foreground/60">Dashboard is coming in the next part.</p>
    </section>
  );
}