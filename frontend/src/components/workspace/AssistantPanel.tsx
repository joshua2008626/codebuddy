import { useState, type FormEvent } from "react";
import { Loader2, Send, Sparkles, Trash2 } from "lucide-react";
import { LANGS, LANG_LIST, type LangId } from "../../lib/languages";
import type { AiMode } from "../../lib/api";
import { useBuddy } from "../../hooks/useBuddy";
import { RichAnswer } from "./RichAnswer";
import type { EditorSelection } from "./EditorPane";

interface ModeCfg {
  id: AiMode;
  label: string;
  hint: string;
  /** Present when the mode takes the user's own words. */
  prompt?: { label: string; placeholder: string; required: boolean };
}

/** The eight Buddy AI modes from the product spec. */
const MODES: ModeCfg[] = [
  { id: "explain", label: "Explain", hint: "Explains your selection, or the whole file, line by line." },
  { id: "debug", label: "Debug", hint: "Finds the cause of an error and suggests a fix.", prompt: { label: "What went wrong? (optional)", placeholder: "For example: it prints 0 instead of 10", required: false } },
  { id: "simplify", label: "Simplify", hint: "Rewrites the code in a simpler, beginner-friendly way." },
  { id: "generate", label: "Generate", hint: "Writes a program from your description.", prompt: { label: "Describe the program", placeholder: "For example: read n numbers and print the largest", required: true } },
  { id: "convert", label: "Convert", hint: "Translates the code into another language." },
  { id: "algorithm", label: "Algorithm", hint: "Gives a step-by-step algorithm for a problem.", prompt: { label: "Describe the problem", placeholder: "For example: check whether a string is a palindrome", required: true } },
  { id: "complexity", label: "Complexity", hint: "Explains time and space complexity." },
  { id: "learn", label: "Learn", hint: "Teaches a concept with examples and exercises.", prompt: { label: "Which concept?", placeholder: "For example: while loops", required: true } },
];

const NEEDS_CODE: AiMode[] = ["explain", "debug", "simplify", "convert", "complexity"];

interface Props {
  language: LangId;
  selection: EditorSelection | null;
  /** Full text of the active file. */
  code: string;
  /** Errors from the last run (compiler output, stderr), used as context for Debug. */
  runOutput: string;
  onNewFile: (code: string, lang: LangId) => void;
}

export function AssistantPanel({ language, selection, code, runOutput, onNewFile }: Props) {
  const buddy = useBuddy();
  const [modeId, setModeId] = useState<AiMode>("explain");
  const [prompt, setPrompt] = useState("");
  const [target, setTarget] = useState<LangId>("java");

  const mode = MODES.find((m) => m.id === modeId)!;
  const targets = LANG_LIST.filter((l) => l.id !== language);
  const effectiveTarget = targets.some((t) => t.id === target) ? target : targets[0].id;

  const hasCode = !!selection || code.trim().length > 0;
  const missingCode = NEEDS_CODE.includes(modeId) && !hasCode;
  const missingPrompt = !!mode.prompt?.required && prompt.trim().length === 0;
  const blocked = buddy.asking || missingCode || missingPrompt;
  const lines = selection ? selection.endLine - selection.startLine + 1 : 0;

  function submit(e: FormEvent) {
    e.preventDefault();
    if (blocked) return;
    const scope = selection ? `lines ${selection.startLine}${lines > 1 ? `–${selection.endLine}` : ""}` : "whole file";
    const label = prompt.trim() && mode.prompt ? `${mode.label}: ${prompt.trim().slice(0, 60)}` : `${mode.label} · ${scope}`;
    void buddy.ask(
      {
        mode: modeId,
        language,
        code,
        selection: selection?.text ?? "",
        prompt: mode.prompt ? prompt : "",
        targetLanguage: modeId === "convert" ? effectiveTarget : undefined,
        runOutput: modeId === "debug" ? runOutput : "",
      },
      label,
    );
  }

  const newestFirst = [...buddy.entries].reverse();

  return (
    <div className="flex h-full flex-col overflow-y-auto p-3 text-sm">
      <h2 className="flex items-center gap-2 text-sm font-medium text-cyan">
        <Sparkles size={15} aria-hidden /> Buddy AI
      </h2>

      {/* What Buddy will see: the language, plus the selection if there is one. */}
      <div className="mt-3 rounded-chip border border-line bg-ink/50 p-2.5 text-xs" aria-live="polite">
        <div className="text-muted">Context: {LANGS[language].label}</div>
        {selection ? (
          <>
            <div className="mt-1">Selected lines {selection.startLine}{lines > 1 ? `–${selection.endLine}` : ""}</div>
            <pre className="mt-1.5 max-h-20 overflow-auto whitespace-pre-wrap font-mono text-[11px] text-muted">{selection.text.slice(0, 400)}</pre>
          </>
        ) : (
          <div className="mt-1 text-muted">Nothing selected, so Buddy uses the whole file. Highlight code to ask about just that part.</div>
        )}
      </div>

      <form onSubmit={submit} className="mt-3">
        <div role="radiogroup" aria-label="What should Buddy do?" className="grid grid-cols-4 gap-1.5">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              role="radio"
              aria-checked={m.id === modeId}
              onClick={() => setModeId(m.id)}
              className={`rounded-chip border px-1 py-1.5 text-[11px] transition-colors ${m.id === modeId ? "border-volt bg-volt/15 text-fg" : "border-line text-muted hover:text-fg"}`}
            >
              {m.label}
            </button>
          ))}
        </div>
        <p className="mt-2 text-xs text-muted">{mode.hint}</p>

        {modeId === "convert" && (
          <div className="mt-2">
            <label htmlFor="convert-target" className="text-xs text-muted">Convert {LANGS[language].label} to</label>
            <select id="convert-target" value={effectiveTarget} onChange={(e) => setTarget(e.target.value as LangId)} className="ml-2 rounded-chip border border-line bg-ink px-2 py-1 text-xs">
              {targets.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
          </div>
        )}

        {mode.prompt && (
          <div className="mt-2">
            <label htmlFor="buddy-prompt" className="text-xs text-muted">{mode.prompt.label}</label>
            <textarea
              id="buddy-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={2000}
              rows={3}
              placeholder={mode.prompt.placeholder}
              className="mt-1 w-full resize-none rounded-chip border border-line bg-ink/60 p-2 text-xs"
            />
          </div>
        )}

        {modeId === "debug" && runOutput && <p className="mt-2 text-xs text-cyan">Including the error from your last run.</p>}

        <button type="submit" disabled={blocked} className="btn-primary mt-3 w-full !py-2 text-xs">
          {buddy.asking ? <Loader2 size={13} className="animate-spin" aria-hidden /> : <Send size={13} aria-hidden />}
          {buddy.asking ? "Buddy is thinking…" : `Ask Buddy to ${mode.label.toLowerCase()}`}
        </button>
        {missingCode && <p className="mt-1.5 text-xs text-muted">Write or select some code first.</p>}
        {!missingCode && missingPrompt && <p className="mt-1.5 text-xs text-muted">Describe what you want first.</p>}
      </form>

      <div className="mt-4 flex-1" aria-live="polite">
        {newestFirst.length === 0 && <p className="text-xs text-muted">Answers appear here. Buddy can be wrong, so run the code and check.</p>}

        {newestFirst.map((e) => (
          <article key={e.id} className="mb-3 rounded-chip border border-line bg-raised/40 p-2.5">
            <h3 className="mb-1.5 text-xs font-medium text-muted">{e.label}</h3>
            {e.pending && (
              <p className="flex items-center gap-2 text-xs text-muted" role="status">
                <Loader2 size={13} className="animate-spin" aria-hidden /> Thinking…
              </p>
            )}
            {e.error && (
              <div role="alert" className="rounded-chip border border-danger/40 bg-danger/10 p-2 text-xs leading-relaxed">
                <p className="font-medium text-danger">Buddy couldn’t answer</p>
                <p className="mt-1">{e.error}</p>
              </div>
            )}
            {e.answer && <RichAnswer text={e.answer} fallbackLang={language} onNewFile={onNewFile} />}
          </article>
        ))}

        {newestFirst.length > 0 && (
          <button type="button" onClick={buddy.clear} className="inline-flex items-center gap-1 text-xs text-muted hover:text-fg">
            <Trash2 size={12} aria-hidden /> Clear answers
          </button>
        )}
      </div>
    </div>
  );
}
