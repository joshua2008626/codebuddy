import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, Loader2, Play, RotateCcw, Send } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { EditorPane } from "../components/workspace/EditorPane";
import { OutputView } from "../components/workspace/BottomPanel";
import { SubmissionResult } from "../components/practice/SubmissionResult";
import { ApiError, getChallenge, submitSolution, type ChallengeDetail, type SubmitResult } from "../lib/api";
import { LANG_LIST, type LangId } from "../lib/languages";
import { useTheme } from "../lib/theme";
import { useRunner } from "../hooks/useRunner";
import { useProgress } from "../hooks/useProgress";
import type { WsFile } from "../hooks/useWorkspace";

const draftKey = (id: string, lang: LangId) => `codebuddy-draft-v1:${id}:${lang}`;

function readDraft(id: string, lang: LangId): string | null {
  try {
    return localStorage.getItem(draftKey(id, lang));
  } catch {
    return null;
  }
}

function writeDraft(id: string, lang: LangId, code: string) {
  try {
    localStorage.setItem(draftKey(id, lang), code);
  } catch {
    /* storage blocked: the draft just isn't kept */
  }
}

function clearDraft(id: string, lang: LangId) {
  try {
    localStorage.removeItem(draftKey(id, lang));
  } catch {
    /* ignore */
  }
}

const DIFFICULTY_LABEL = { beginner: "Beginner", intermediate: "Intermediate", advanced: "Advanced" } as const;

export default function ChallengePage() {
  const { id = "" } = useParams();
  // Lesson exercises reuse this page; ?lesson=<id> makes the back link return to that lesson.
  const [search] = useSearchParams();
  const lessonParam = search.get("lesson") ?? "";
  const lessonId = /^[a-z0-9-]{1,40}$/.test(lessonParam) ? lessonParam : null;
  const { theme } = useTheme();
  const runner = useRunner();
  const progress = useProgress();

  const [challenge, setChallenge] = useState<ChallengeDetail | null>(null);
  const [loadError, setLoadError] = useState<{ message: string; notFound: boolean } | null>(null);
  const [lang, setLang] = useState<LangId>("python");
  const [code, setCode] = useState("");
  const [stdin, setStdin] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<SubmitResult | null>(null);

  const load = useCallback(async () => {
    setChallenge(null);
    setLoadError(null);
    try {
      const c = await getChallenge(id);
      setChallenge(c);
      setStdin(c.samples[0]?.input ?? "");
    } catch (e) {
      const err = e instanceof ApiError ? e : null;
      setLoadError({ message: err?.message ?? "Couldn’t load this challenge.", notFound: err?.status === 404 });
    }
  }, [id]);
  useEffect(() => void load(), [load]);

  // Switching language or challenge loads that language's saved draft, or its starter code.
  useEffect(() => {
    if (!challenge) return;
    setCode(readDraft(challenge.id, lang) ?? challenge.starters[lang]);
    setResult(null);
    setSubmitError(null);
  }, [challenge, lang]);

  const file: WsFile = useMemo(
    () => ({ id: `challenge:${id}:${lang}`, name: lang === "java" ? "Main.java" : lang === "c" ? "main.c" : "main.py", language: lang, content: code }),
    [id, lang, code],
  );

  function onCode(value: string) {
    setCode(value);
    if (challenge) writeDraft(challenge.id, lang, value);
  }

  function resetCode() {
    if (!challenge) return;
    clearDraft(challenge.id, lang);
    setCode(challenge.starters[lang]);
  }

  async function submit() {
    if (!challenge || submitting) return;
    setSubmitting(true);
    setSubmitError(null);
    setResult(null);
    try {
      const r = await submitSolution(challenge.id, lang, code);
      setResult(r);
      progress.record(challenge.id, r.verdict, r.passed, r.total); // only real server verdicts are recorded
    } catch (e) {
      setSubmitError(e instanceof ApiError ? e.message : "Something went wrong while grading your code.");
    } finally {
      setSubmitting(false);
    }
  }

  const solved = challenge ? progress.map[challenge.id]?.solved : false;

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-5 py-8">
        <Link to={lessonId ? `/learn/${lessonId}` : "/practice"} className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg"><ArrowLeft size={14} aria-hidden /> {lessonId ? "Back to the lesson" : "All challenges"}</Link>

        {!challenge && !loadError && <p className="mt-10 flex items-center gap-2 text-sm text-muted" role="status"><Loader2 size={16} className="animate-spin" aria-hidden /> Loading challenge…</p>}

        {loadError && (
          <div role="alert" className="mt-8 rounded-panel border border-danger/40 bg-danger/10 p-4 text-sm">
            <p className="font-medium text-danger">{loadError.notFound ? "That challenge doesn’t exist" : "Couldn’t load this challenge"}</p>
            <p className="mt-1">{loadError.message}</p>
            {loadError.notFound ? <Link to="/practice" className="btn-ghost mt-3">See all challenges</Link> : <button type="button" onClick={load} className="btn-ghost mt-3">Try again</button>}
          </div>
        )}

        {challenge && (
          <div className="mt-4 grid gap-8 lg:grid-cols-[1fr_1.15fr]">
            {/* ---------- problem ---------- */}
            <article>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-semibold tracking-tight">{challenge.title}</h1>
                <span className="rounded-chip bg-raised px-2 py-0.5 text-xs text-muted">{DIFFICULTY_LABEL[challenge.difficulty]}</span>
                {solved && <span className="rounded-chip bg-ok/15 px-2 py-0.5 text-xs text-ok">Solved</span>}
              </div>
              <p className="mt-4 leading-relaxed">{challenge.statement}</p>

              <h2 className="mt-6 text-sm font-semibold">Input</h2>
              <p className="mt-1 text-sm text-muted">{challenge.input_format}</p>
              <h2 className="mt-4 text-sm font-semibold">Output</h2>
              <p className="mt-1 text-sm text-muted">{challenge.output_format}</p>
              <h2 className="mt-4 text-sm font-semibold">Constraints</h2>
              <ul className="mt-1 list-disc pl-5 text-sm text-muted">{challenge.constraints.map((c) => <li key={c}>{c}</li>)}</ul>

              <h2 className="mt-6 text-sm font-semibold">Examples</h2>
              {challenge.samples.map((s, i) => (
                <div key={i} className="mt-2 rounded-panel border border-line bg-panel p-3">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div><div className="text-[11px] text-muted">Input</div><pre className="mt-0.5 whitespace-pre-wrap font-mono text-xs">{s.input}</pre></div>
                    <div><div className="text-[11px] text-muted">Output</div><pre className="mt-0.5 whitespace-pre-wrap font-mono text-xs">{s.output}</pre></div>
                  </div>
                  {s.note && <p className="mt-2 text-xs text-muted">{s.note}</p>}
                  <button type="button" className="mt-2 text-xs text-volt hover:underline" onClick={() => setStdin(s.input)}>Use as test input</button>
                </div>
              ))}
            </article>

            {/* ---------- solve ---------- */}
            <section aria-label="Your solution" className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <label htmlFor="ch-lang" className="sr-only">Language</label>
                <select id="ch-lang" value={lang} onChange={(e) => setLang(e.target.value as LangId)} className="rounded-chip border border-line bg-ink px-2 py-1.5 text-xs">
                  {LANG_LIST.map((l) => <option key={l.id} value={l.id}>{l.label}</option>)}
                </select>
                <button type="button" onClick={resetCode} className="btn-ghost !px-2.5 !py-1.5 text-xs"><RotateCcw size={13} aria-hidden /> Reset code</button>
                <span className="ml-auto text-xs text-muted">Your code is saved in this browser</span>
              </div>

              <div className="mt-2 h-[380px] overflow-hidden rounded-panel border border-line">
                <EditorPane file={file} theme={theme} onChange={onCode} onSelection={() => {}} onRun={() => void runner.run(file, stdin)} />
              </div>

              <div className="mt-4">
                <label htmlFor="ch-stdin" className="text-xs text-muted">Test input for Run (not graded)</label>
                <textarea id="ch-stdin" value={stdin} onChange={(e) => setStdin(e.target.value)} maxLength={16000} spellCheck={false} rows={3} className="mt-1 w-full resize-y rounded-chip border border-line bg-ink/60 p-2 font-mono text-xs" />
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <button type="button" onClick={() => void runner.run(file, stdin)} disabled={runner.running || submitting} className="btn-ghost">
                  {runner.running ? <Loader2 size={14} className="animate-spin" aria-hidden /> : <Play size={14} aria-hidden />} {runner.running ? "Running…" : "Run with this input"}
                </button>
                <button type="button" onClick={submit} disabled={submitting || runner.running} className="btn-primary">
                  {submitting ? <Loader2 size={14} className="animate-spin" aria-hidden /> : <Send size={14} aria-hidden />} {submitting ? "Grading…" : "Submit for grading"}
                </button>
              </div>

              {runner.state.phase !== "idle" && (
                <div className="panel mt-4 p-3"><OutputView state={runner.state} /></div>
              )}

              {submitting && <p className="mt-4 text-sm text-muted" role="status">Running your code against every test. This can take a few seconds.</p>}
              {submitError && (
                <div role="alert" className="mt-4 rounded-panel border border-danger/40 bg-danger/10 p-3 text-sm">
                  <p className="font-medium text-danger">Couldn’t grade your code</p>
                  <p className="mt-1">{submitError}</p>
                </div>
              )}
              {result && <div className="mt-4"><SubmissionResult result={result} /></div>}
              {!progress.storageOk && <p className="mt-3 text-xs text-muted">Browser storage is blocked, so your progress won’t be kept after you leave.</p>}
            </section>
          </div>
        )}
      </main>
    </>
  );
}
