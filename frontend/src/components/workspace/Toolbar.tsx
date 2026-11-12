import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlignLeft, Copy, Download, Loader2, Moon, Play, RotateCcw, Sun } from "lucide-react";
import { LogoMark } from "../Logo";
import { LANG_LIST, type LangId } from "../../lib/languages";
import type { SaveStatus, WsFile } from "../../hooks/useWorkspace";
import type { Theme } from "../../lib/theme";

interface Props {
  file: WsFile;
  theme: Theme;
  saveStatus: SaveStatus;
  /** Short message announced to screen readers and shown briefly (copy result, format result). */
  notice: string;
  running: boolean;
  storage: "browser" | "account";
  /** Detail shown beside the save status, for example why a save failed. */
  saveNote: string | null;
  /** Shown before the file name when working inside a saved project. */
  projectName?: string;
  onRun: () => void;
  onLanguage: (l: LangId) => void;
  onFormat: () => void;
  onCopy: () => void;
  onDownload: () => void;
  onReset: () => void;
  onToggleTheme: () => void;
}

function saveText(status: SaveStatus, storage: "browser" | "account"): string {
  switch (status) {
    case "saved": return storage === "account" ? "Saved to your account" : "Saved in this browser";
    case "saving": return "Saving…";
    case "failed": return "Not saved yet";
    default: return "Can’t save: browser storage is blocked";
  }
}

export function Toolbar(p: Props) {
  // Reset is destructive, so it needs a second click within 3 seconds.
  const [confirmReset, setConfirmReset] = useState(false);
  useEffect(() => {
    if (!confirmReset) return;
    const t = window.setTimeout(() => setConfirmReset(false), 3000);
    return () => window.clearTimeout(t);
  }, [confirmReset]);

  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-line bg-panel px-3 py-2">
      <Link to="/" aria-label="CodeBuddy home" className="mr-1 shrink-0"><LogoMark size={26} /></Link>

      <span className="hidden max-w-[14rem] truncate font-mono text-xs text-muted sm:inline" title={p.projectName ? `${p.projectName} / ${p.file.name}` : p.file.name}>
        {p.projectName ? `${p.projectName} / ` : ""}{p.file.name}
      </span>

      <label className="sr-only" htmlFor="lang-select">Language</label>
      <select
        id="lang-select"
        value={p.file.language}
        onChange={(e) => p.onLanguage(e.target.value as LangId)}
        className="rounded-chip border border-line bg-ink px-2 py-1.5 text-xs"
      >
        {LANG_LIST.map((l) => <option key={l.id} value={l.id}>{l.label}</option>)}
      </select>

      <div className="flex items-center gap-1">
        <button type="button" onClick={p.onRun} disabled={p.running} title="Run (Ctrl+Enter)" className="btn-primary !px-3 !py-1.5 text-xs">
          {p.running ? <Loader2 size={13} className="animate-spin" aria-hidden /> : <Play size={13} aria-hidden />}
          {p.running ? "Running…" : "Run"}
        </button>
        <button type="button" onClick={p.onFormat} className="btn-ghost !px-2.5 !py-1.5 text-xs" title="Tidy whitespace and brace indentation">
          <AlignLeft size={13} aria-hidden /> <span className="hidden sm:inline">Format</span><span className="sr-only sm:hidden">Format</span>
        </button>
        <button type="button" onClick={p.onCopy} className="btn-ghost !px-2.5 !py-1.5 text-xs" aria-label="Copy code">
          <Copy size={13} aria-hidden />
        </button>
        <button type="button" onClick={p.onDownload} className="btn-ghost !px-2.5 !py-1.5 text-xs" aria-label={`Download ${p.file.name}`}>
          <Download size={13} aria-hidden />
        </button>
        <button
          type="button"
          onClick={() => {
            if (confirmReset) { p.onReset(); setConfirmReset(false); }
            else setConfirmReset(true);
          }}
          className={`btn-ghost !px-2.5 !py-1.5 text-xs ${confirmReset ? "!border-danger !text-danger" : ""}`}
          aria-label={confirmReset ? "Confirm reset to starter code" : "Reset to starter code"}
        >
          <RotateCcw size={13} aria-hidden /> {confirmReset && "Reset this file?"}
        </button>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <span className={`hidden text-xs md:inline ${p.saveStatus === "failed" ? "text-danger" : "text-muted"}`} role={p.saveStatus === "failed" ? "alert" : undefined}>
          {saveText(p.saveStatus, p.storage)}{p.saveNote ? `. ${p.saveNote}` : ""}
        </span>
        <button
          type="button"
          onClick={p.onToggleTheme}
          className="btn-ghost !px-2.5 !py-1.5"
          aria-label={p.theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        >
          {p.theme === "dark" ? <Sun size={13} /> : <Moon size={13} />}
        </button>
      </div>

      <p className="w-full text-xs text-cyan empty:hidden" role="status" aria-live="polite">{p.notice}</p>
    </div>
  );
}
