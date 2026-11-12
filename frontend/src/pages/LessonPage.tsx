import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle2, Clock, Loader2, SquareTerminal } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Markdown } from "../components/Markdown";
import { ApiError, getLesson, listLessons, type LessonDetail, type LessonExample, type LessonSummary } from "../lib/api";
import { LANGS, type LangId } from "../lib/languages";
import { useProgress } from "../hooks/useProgress";

/** "loops" + python -> "lesson_loops.py". Names must satisfy the workspace's file-name rules. */
const seedName = (lessonId: string, lang: LangId) => `lesson_${lessonId.replace(/-/g, "_")}${LANGS[lang].ext}`;

function ExampleBlock({ example, lessonId }: { example: LessonExample; lessonId: string }) {
  const navigate = useNavigate();
  return (
    <figure className="overflow-hidden rounded-chip border border-line">
      <figcaption className="flex items-center justify-between gap-2 border-b border-line bg-panel px-3 py-2 text-xs">
        <span><span className="font-medium">{example.title}</span> <span className="text-muted">· {LANGS[example.language].label}</span></span>
        <button
          type="button"
          className="btn-ghost !px-2 !py-1 text-xs"
          onClick={() => navigate("/workspace", { state: { seed: { name: seedName(lessonId, example.language), language: example.language, content: example.code, stdin: example.stdin } } })}
        >
          <SquareTerminal size={13} aria-hidden /> Open in workspace
        </button>
      </figcaption>
      <pre className="overflow-x-auto bg-ink/60 p-3 font-mono text-xs leading-relaxed"><code>{example.code}</code></pre>
      {example.stdin && (
        <div className="border-t border-line px-3 py-2 text-xs"><span className="text-muted">Input: </span><code className="font-mono">{example.stdin.trimEnd()}</code></div>
      )}
      <div className="border-t border-line bg-panel px-3 py-2 text-xs">
        <span className="text-muted">Prints:</span>
        <pre className="mt-1 whitespace-pre-wrap font-mono">{example.output}</pre>
      </div>
    </figure>
  );
}

export default function LessonPage() {
  const { id = "" } = useParams();
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [all, setAll] = useState<LessonSummary[]>([]);
  const [error, setError] = useState<{ message: string; notFound: boolean } | null>(null);
  const [lang, setLang] = useState<LangId | "all">("all");
  const { map } = useProgress();

  const load = useCallback(() => {
    setLesson(null);
    setError(null);
    setLang("all");
    getLesson(id).then(setLesson).catch((e) => setError({ message: e instanceof ApiError ? e.message : "Couldn’t load the lesson.", notFound: e instanceof ApiError && e.status === 404 }));
  }, [id]);
  useEffect(load, [load]);
  useEffect(() => { listLessons().then(setAll).catch(() => setAll([])); }, []);

  const index = all.findIndex((l) => l.id === id);
  const prev = index > 0 ? all[index - 1] : null;
  const next = index >= 0 && index < all.length - 1 ? all[index + 1] : null;
  const solved = lesson ? !!map[lesson.exercise.id]?.solved : false;
  const langs = lesson ? Array.from(new Set(lesson.examples.map((e) => e.language))) : [];
  const shown = lesson ? lesson.examples.filter((e) => lang === "all" || e.language === lang) : [];

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-6 pb-20 pt-24">
        <Link to="/learn" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg"><ArrowLeft size={14} aria-hidden /> All lessons</Link>

        {!lesson && !error && <p className="mt-10 flex items-center gap-2 text-sm text-muted" role="status"><Loader2 size={16} className="animate-spin" aria-hidden /> Loading lesson…</p>}
        {error && (
          <div role="alert" className="mt-8 rounded-panel border border-danger/40 bg-danger/10 p-4 text-sm">
            <p className="font-medium text-danger">{error.notFound ? "Lesson not found" : "Couldn’t load the lesson"}</p>
            <p className="mt-1">{error.message}</p>
            {error.notFound ? <Link to="/learn" className="btn-ghost mt-3 inline-flex">See all lessons</Link> : <button type="button" className="btn-ghost mt-3" onClick={load}>Try again</button>}
          </div>
        )}

        {lesson && (
          <article>
            <h1 className="mt-6 text-3xl font-semibold tracking-tight">{lesson.title}</h1>
            <p className="mt-2 flex items-center gap-2 text-sm text-muted"><Clock size={14} aria-hidden /> {lesson.minutes} min · {lesson.group}</p>

            {lesson.sections.map((s) => (
              <section key={s.heading} className="mt-8">
                <h2 className="mb-2 text-xl font-semibold">{s.heading}</h2>
                <Markdown source={s.body} />
              </section>
            ))}

            <section className="mt-10" aria-label="Examples">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-xl font-semibold">Examples</h2>
                {langs.length > 1 && (
                  <div role="group" aria-label="Show examples in" className="flex gap-1 text-xs">
                    {(["all", ...langs] as const).map((l) => (
                      <button key={l} type="button" aria-pressed={lang === l} onClick={() => setLang(l)} className={`rounded-chip border px-2.5 py-1 ${lang === l ? "border-volt text-fg" : "border-line text-muted"}`}>
                        {l === "all" ? "All" : LANGS[l].label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="mt-3 space-y-4">{shown.map((e, i) => <ExampleBlock key={`${e.language}-${i}`} example={e} lessonId={lesson.id} />)}</div>
            </section>

            <section className="panel mt-10 p-5" aria-label="Exercise">
              <h2 className="flex items-center gap-2 text-xl font-semibold">
                Exercise: {lesson.exercise.title}
                {solved && <CheckCircle2 size={18} className="text-ok" aria-label="Solved" />}
              </h2>
              <p className="mt-2 text-sm">{lesson.exercise.statement}</p>
              <p className="mt-2 text-xs text-muted">Your code is run against hidden tests by the sandboxed execution service. {solved ? "You have solved this one in this browser." : ""}</p>
              <Link to={`/practice/${lesson.exercise.id}?lesson=${lesson.id}`} className="btn-primary mt-4 inline-flex">{solved ? "Open the exercise again" : "Start the exercise"}</Link>
            </section>

            <nav aria-label="Lesson navigation" className="mt-10 flex justify-between gap-3 text-sm">
              {prev ? <Link to={`/learn/${prev.id}`} className="btn-ghost"><ArrowLeft size={14} aria-hidden /> {prev.title}</Link> : <span />}
              {next ? <Link to={`/learn/${next.id}`} className="btn-ghost">{next.title} <ArrowRight size={14} aria-hidden /></Link> : <span />}
            </nav>
          </article>
        )}
      </main>
    </>
  );
}
