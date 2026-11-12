import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import type { RunState } from "../../hooks/useRunner";
import type { ExecuteResult, Outcome } from "../../lib/api";

type Tab = "output" | "input" | "tests";
const TABS: { id: Tab; label: string }[] = [
  { id: "output", label: "Output" },
  { id: "input", label: "Input (stdin)" },
  { id: "tests", label: "Test cases" },
];

const OUTCOME_LABEL: Record<Outcome, string> = {
  success: "Finished",
  compile_error: "Compilation failed",
  runtime_error: "Runtime error",
  time_limit: "Time limit exceeded",
  internal_error: "Execution service error",
};

function formatMemory(kb: number): string {
  return kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;
}

function Stream({ title, text, tone }: { title: string; text: string; tone: "normal" | "error" }) {
  if (!text) return null;
  return (
    <section className="mt-3 first:mt-0">
      <h3 className="mb-1 text-xs text-muted">{title}</h3>
      <pre className={`whitespace-pre-wrap break-words font-mono text-xs leading-5 ${tone === "error" ? "text-danger" : "text-fg"}`}>{text}</pre>
    </section>
  );
}

function ResultView({ fileName, r }: { fileName: string; r: ExecuteResult }) {
  const ok = r.outcome === "success";
  const meta = [r.status_text, r.time_seconds !== null && `${r.time_seconds} s`, r.memory_kb !== null && formatMemory(r.memory_kb)].filter(Boolean);
  const printedNothing = !r.stdout && !r.stderr && !r.compile_output && !r.message;

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
        <span className={`rounded-chip px-2 py-0.5 font-medium ${ok ? "bg-ok/15 text-ok" : "bg-danger/15 text-danger"}`}>{OUTCOME_LABEL[r.outcome]}</span>
        <span className="text-muted">{fileName}</span>
        <span className="text-muted">{meta.join(" · ")}</span>
      </div>
      <Stream title="Compiler output" text={r.compile_output} tone="error" />
      <Stream title="Output" text={r.stdout} tone="normal" />
      <Stream title="Errors" text={r.stderr} tone="error" />
      <Stream title="Message" text={r.message} tone="error" />
      {printedNothing && <p className="text-xs text-muted">The program finished without printing anything.</p>}
    </div>
  );
}

export function OutputView({ state }: { state: RunState }) {
  if (state.phase === "running") {
    return (
      <p className="flex items-center gap-2 text-xs text-muted" role="status">
        <Loader2 size={14} className="animate-spin" aria-hidden /> Running {state.fileName}…
      </p>
    );
  }
  if (state.phase === "error") {
    return (
      <div role="alert" className="rounded-chip border border-danger/40 bg-danger/10 p-3 text-xs leading-relaxed">
        <p className="font-medium text-danger">Couldn’t run your code</p>
        <p className="mt-1">{state.message}</p>
      </div>
    );
  }
  if (state.phase === "done") return <ResultView fileName={state.fileName} r={state.result} />;
  return <p className="text-xs text-muted">Press Run (or Ctrl+Enter) to see your program’s output here.</p>;
}

interface Props {
  stdin: string;
  onStdin: (v: string) => void;
  runState: RunState;
  /** Increments on every run; the panel jumps to the Output tab when it changes. */
  runCount: number;
}

export function BottomPanel({ stdin, onStdin, runState, runCount }: Props) {
  const [tab, setTab] = useState<Tab>("output");
  useEffect(() => {
    if (runCount > 0) setTab("output");
  }, [runCount]);

  return (
    <div className="flex h-full flex-col">
      <div role="tablist" aria-label="Panel" className="flex shrink-0 gap-1 border-b border-line px-2 pt-1.5">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={tab === t.id}
            aria-controls={`bottom-panel-${t.id}`}
            onClick={() => setTab(t.id)}
            className={`rounded-t-chip px-3 py-1.5 text-xs transition-colors ${tab === t.id ? "bg-raised text-fg" : "text-muted hover:text-fg"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div id={`bottom-panel-${tab}`} role="tabpanel" className="min-h-0 flex-1 overflow-auto p-3 text-sm">
        {tab === "output" && <OutputView state={runState} />}

        {tab === "input" && (
          <div className="flex h-full flex-col">
            <label htmlFor="stdin" className="text-xs text-muted">
              Text your program reads from standard input. Saved with your workspace.
            </label>
            <textarea
              id="stdin"
              value={stdin}
              onChange={(e) => onStdin(e.target.value)}
              spellCheck={false}
              maxLength={16000}
              className="mt-2 min-h-[80px] flex-1 resize-none rounded-chip border border-line bg-ink/60 p-2 font-mono text-xs"
              placeholder="One value per line, for example: Asha"
            />
          </div>
        )}

        {tab === "tests" && (
          <p className="text-xs text-muted">Test cases come with the practice challenges. Open a challenge to run your code against them.</p>
        )}
      </div>
    </div>
  );
}
