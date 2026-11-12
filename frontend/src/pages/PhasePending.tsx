import { Link } from "react-router-dom";
import { Navbar } from "../components/Navbar";

/**
 * Honest placeholder for routes whose feature has not been built yet.
 * Each one is replaced by the real page in its phase; nothing here pretends to work.
 */
export default function PhasePending({ title, phase }: { title: string; phase: number }) {
  return (
    <>
      <Navbar />
      <main className="mx-auto flex min-h-[70vh] max-w-xl flex-col items-start justify-center px-6">
        <h1 className="text-3xl font-semibold tracking-tight">{title} isn’t built yet</h1>
        <p className="mt-3 text-muted">
          This page is scheduled for phase {phase} of the build. Until then, the landing page is the only finished screen.
        </p>
        <Link to="/" className="btn-ghost mt-6">
          Back to home
        </Link>
      </main>
    </>
  );
}
