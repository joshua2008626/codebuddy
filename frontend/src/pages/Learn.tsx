import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, Clock, Loader2 } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { ApiError, listLessons, type LessonSummary } from "../lib/api";
import { LANGS } from "../lib/languages";
import { useProgress } from "../hooks/useProgress";

const GROUPS = ["Languages", "Core concepts", "Going further"];

export default function Learn() {
  const [lessons, setLessons] = useState<LessonSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { map } = useProgress();

  const load = useCallback(() => {
    setError(null);
    listLessons().then(setLessons).catch((e) => setError(e instanceof ApiError ? e.message : "Couldn’t load the lessons."));
  }, []);
  useEffect(load, [load]);

  const done = lessons?.filter((l) => map[l.exercise_id]?.solved).length ?? 0;

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-6 pb-20 pt-24">
        <h1 className="text-3xl font-semibold tracking-tight">Learning hub</h1>
        <p className="mt-2 max-w-2xl text-muted">Twelve short lessons in C, Python and Java. Each has an explanation, examples you can open in the workspace, and a small exercise that is graded by really running your code.</p>
        {lessons && <p className="mt-3 text-sm text-muted" role="status">{done} of {lessons.length} exercises solved <span className="text-xs">(tracked in this browser)</span></p>}

        {error && (
          <div role="alert" className="mt-8 rounded-panel border border-danger/40 bg-danger/10 p-4 text-sm">
            <p>{error}</p>
            <button type="button" className="btn-ghost mt-3" onClick={load}>Try again</button>
          </div>
        )}
        {!lessons && !error && <p className="mt-8 flex items-center gap-2 text-sm text-muted" role="status"><Loader2 size={16} className="animate-spin" aria-hidden /> Loading lessons…</p>}

        {lessons && GROUPS.map((g) => (
          <section key={g} className="mt-10" aria-label={g}>
            <h2 className="text-sm font-medium text-muted">{g}</h2>
            <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {lessons.filter((l) => l.group === g).map((l) => (
                <li key={l.id}>
                  <Link to={`/learn/${l.id}`} className="panel flex h-full flex-col p-4 transition hover:border-volt">
                    <span className="flex items-start justify-between gap-2">
                      <span className="font-semibold">{l.title}</span>
                      {map[l.exercise_id]?.solved && <CheckCircle2 size={18} className="shrink-0 text-ok" aria-label="Exercise solved" />}
                    </span>
                    <span className="mt-1 text-sm text-muted">{l.summary}</span>
                    <span className="mt-auto flex items-center gap-3 pt-3 text-xs text-muted">
                      <span className="flex items-center gap-1"><Clock size={12} aria-hidden /> {l.minutes} min</span>
                      <span>{l.languages.map((x) => LANGS[x].label).join(" · ")}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </main>
    </>
  );
}
