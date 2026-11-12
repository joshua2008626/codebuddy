import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, Loader2 } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { ApiError, listChallenges, type ChallengeSummary, type Difficulty } from "../lib/api";
import { useProgress } from "../hooks/useProgress";
import { summarize } from "../lib/progress";

const LEVELS: { id: Difficulty; label: string }[] = [
  { id: "beginner", label: "Beginner" },
  { id: "intermediate", label: "Intermediate" },
  { id: "advanced", label: "Advanced" },
];

export default function Practice() {
  const [items, setItems] = useState<ChallengeSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { map, storageOk } = useProgress();

  async function load() {
    setItems(null);
    setError(null);
    try {
      setItems(await listChallenges());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn’t load the challenges.");
    }
  }
  useEffect(() => void load(), []);

  const summary = items ? summarize(map, items) : null;

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-4xl px-5 py-12">
        <h1 className="text-3xl font-semibold tracking-tight">Practice arena</h1>
        <p className="mt-2 max-w-xl text-muted">Solve each challenge in C, Python or Java. Your code runs against test cases, some of which stay hidden.</p>

        {summary && (
          <p className="mt-4 text-sm" aria-live="polite">
            <span className="font-medium">{summary.solved} of {summary.total}</span> solved
            <span className="text-muted"> · saved in this browser only{storageOk ? "" : ", but storage is blocked so it won’t be kept"}</span>
          </p>
        )}

        {!items && !error && (
          <p className="mt-10 flex items-center gap-2 text-sm text-muted" role="status"><Loader2 size={16} className="animate-spin" aria-hidden /> Loading challenges…</p>
        )}

        {error && (
          <div role="alert" className="mt-10 rounded-panel border border-danger/40 bg-danger/10 p-4 text-sm">
            <p className="font-medium text-danger">Couldn’t load the challenges</p>
            <p className="mt-1">{error}</p>
            <button type="button" onClick={load} className="btn-ghost mt-3">Try again</button>
          </div>
        )}

        {items && items.length === 0 && <p className="mt-10 text-sm text-muted">There are no challenges yet.</p>}

        {items && LEVELS.map(({ id, label }) => {
          const group = items.filter((c) => c.difficulty === id);
          if (group.length === 0) return null;
          return (
            <section key={id} className="mt-10" aria-labelledby={`lvl-${id}`}>
              <h2 id={`lvl-${id}`} className="text-lg font-semibold">{label} <span className="text-sm font-normal text-muted">{summary?.byDifficulty[id]?.solved}/{group.length} solved</span></h2>
              <ul className="mt-3 divide-y divide-line overflow-hidden rounded-panel border border-line bg-panel">
                {group.map((c) => {
                  const p = map[c.id];
                  return (
                    <li key={c.id}>
                      <Link to={`/practice/${c.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-raised">
                        <span className="w-5 shrink-0">
                          {p?.solved && <CheckCircle2 size={18} className="text-ok" aria-label="Solved" />}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block font-medium">{c.title}</span>
                          <span className="block truncate text-sm text-muted">{c.summary}</span>
                        </span>
                        <span className="hidden shrink-0 text-xs text-muted sm:block">
                          {p ? `${p.attempts} ${p.attempts === 1 ? "attempt" : "attempts"}${p.solved ? "" : ` · best ${p.bestPassed}/${p.total}`}` : "Not tried"}
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </section>
          );
        })}
      </main>
      <Footer />
    </>
  );
}
