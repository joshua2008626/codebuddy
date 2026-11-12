import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Toolbar } from "../components/workspace/Toolbar";
import { FileExplorer } from "../components/workspace/FileExplorer";
import { EditorPane, type EditorSelection } from "../components/workspace/EditorPane";
import { AssistantPanel } from "../components/workspace/AssistantPanel";
import { BottomPanel } from "../components/workspace/BottomPanel";
import { ResizeHandle } from "../components/workspace/ResizeHandle";
import { useWorkspace, type WorkspaceApi } from "../hooks/useWorkspace";
import { useRunner } from "../hooks/useRunner";
import { useTheme } from "../lib/theme";
import { formatCode } from "../lib/format";
import { LANGS, type LangId } from "../lib/languages";
import { saveBlob } from "../lib/download";
import { parseSeed } from "../lib/seed";

type MobileView = "files" | "editor" | "buddy";
const clamp = (n: number, min: number, max: number) => Math.min(max, Math.max(min, n));

/** The scratch workspace: files live in this browser and need no account. */
export default function Workspace() {
  const ws = useWorkspace();
  const location = useLocation();
  const navigate = useNavigate();
  const seeded = useRef(false);

  // A lesson's "Open in workspace" button passes an example here. It is added as a NEW file, so nothing already written is overwritten.
  useEffect(() => {
    const seed = parseSeed((location.state as { seed?: unknown } | null)?.seed);
    if (!seed || seeded.current) return;
    seeded.current = true;
    let name = seed.name;
    const ext = LANGS[seed.language].ext;
    for (let n = 2; ws.files.some((f) => f.name.toLowerCase() === name.toLowerCase()); n++) name = `${seed.name.slice(0, -ext.length)}_${n}${ext}`;
    void Promise.resolve(ws.createFile(name, seed.content)).then(() => {
      if (seed.stdin) ws.setStdin(seed.stdin);
    });
    navigate(location.pathname, { replace: true, state: null }); // so a refresh does not add the file again
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <WorkspaceView ws={ws} />;
}

/** The full workspace screen, for any file store (browser or saved project). */
export function WorkspaceView({ ws, projectName }: { ws: WorkspaceApi; projectName?: string }) {
  const { theme, toggle } = useTheme();
  const runner = useRunner();
  const runActive = () => void runner.run(ws.active, ws.stdin);

  // Errors from the last run (not normal output) give Buddy's Debug mode something concrete to explain.
  const lastRunErrors =
    runner.state.phase === "done"
      ? [runner.state.result.compile_output, runner.state.result.stderr, runner.state.result.message].filter(Boolean).join("\n").slice(0, 4000)
      : "";

  const [selection, setSelection] = useState<EditorSelection | null>(null);
  const [notice, setNotice] = useState("");
  const [view, setView] = useState<MobileView>("editor"); // only used below the lg breakpoint
  const [leftW, setLeftW] = useState(230);
  const [rightW, setRightW] = useState(300);
  const [bottomH, setBottomH] = useState(220);
  const noticeTimer = useRef<number | undefined>(undefined);

  /** Shows a short status message for a couple of seconds. */
  const say = useCallback((msg: string) => {
    setNotice(msg);
    window.clearTimeout(noticeTimer.current);
    noticeTimer.current = window.setTimeout(() => setNotice(""), 2500);
  }, []);
  useEffect(() => () => window.clearTimeout(noticeTimer.current), []);

  // A selection belongs to the file it was made in, so drop it when the file changes.
  useEffect(() => setSelection(null), [ws.active.id]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(ws.active.content);
      say("Copied to clipboard.");
    } catch {
      say("Couldn’t copy automatically. Select the code and press Ctrl+C.");
    }
  }

  function download() {
    saveBlob(new Blob([ws.active.content], { type: "text/plain" }), ws.active.name);
  }

  /** Puts code from a Buddy AI answer into a new file, leaving the current file untouched. */
  async function newFileFromAnswer(code: string, lang: LangId) {
    const base = lang === "java" ? "Buddy" : "buddy";
    const ext = LANGS[lang].ext;
    let name = `${base}${ext}`;
    for (let n = 2; ws.files.some((f) => f.name.toLowerCase() === name.toLowerCase()); n++) name = `${base}${n}${ext}`;
    const err = await ws.createFile(name, code.endsWith("\n") ? code : code + "\n");
    if (err) say(err);
    else {
      say(`Created ${name}.`);
      setView("editor");
    }
  }

  function format() {
    if (formatCode(ws.active.content, ws.active.language) === ws.active.content) {
      say("Already tidy.");
      return;
    }
    ws.formatActive();
    say("Formatted.");
  }

  // Panel sizes are CSS variables so they only apply from the lg breakpoint up; below it the panels stack.
  const vars = { "--left-w": `${leftW}px`, "--right-w": `${rightW}px`, "--bottom-h": `${bottomH}px` } as CSSProperties;
  const show = (v: MobileView) => (view === v ? "flex" : "hidden");

  return (
    <div className="flex h-[100dvh] flex-col bg-ink">
      <Toolbar
        file={ws.active}
        theme={theme}
        saveStatus={ws.saveStatus}
        notice={notice}
        running={runner.running}
        storage={ws.storage}
        saveNote={ws.saveNote}
        projectName={projectName}
        onRun={runActive}
        onLanguage={ws.switchLanguage}
        onFormat={format}
        onCopy={copy}
        onDownload={download}
        onReset={() => { ws.resetActive(); say("Reset to starter code."); }}
        onToggleTheme={toggle}
      />

      {/* Below lg the three regions become one-at-a-time views. */}
      <div role="tablist" aria-label="Workspace view" className="flex border-b border-line bg-panel lg:hidden">
        {([["files", "Files"], ["editor", "Editor"], ["buddy", "Buddy AI"]] as const).map(([id, label]) => (
          <button
            key={id}
            role="tab"
            type="button"
            aria-selected={view === id}
            onClick={() => setView(id)}
            className={`flex-1 py-2 text-sm ${view === id ? "border-b-2 border-volt text-fg" : "text-muted"}`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="flex min-h-0 flex-1 flex-col lg:flex-row" style={vars}>
        <aside aria-label="Files" className={`${show("files")} min-h-0 flex-1 flex-col bg-panel lg:flex lg:w-[var(--left-w)] lg:flex-none`}>
          <FileExplorer
            files={ws.files}
            activeId={ws.active.id}
            onSelect={(id) => { ws.setActive(id); setView("editor"); }}
            onCreate={async (n) => { const err = await ws.createFile(n); if (!err) setView("editor"); return err; }}
            onRename={ws.renameFile}
            onDelete={async (id) => (await ws.deleteFile(id)) ?? null}
            storage={ws.storage}
          />
        </aside>
        <ResizeHandle direction="vertical" label="Resize file sidebar" onResize={(d) => setLeftW((w) => clamp(w + d, 170, 420))} />

        <section aria-label="Editor and output" className={`${show("editor")} min-h-0 min-w-0 flex-1 flex-col lg:flex`}>
          <div className="relative min-h-0 flex-1 border-y border-line lg:border-t-0">
            <div className="absolute inset-0">
              <EditorPane file={ws.active} theme={theme} onChange={(v) => ws.setContent(ws.active.id, v)} onSelection={setSelection} onRun={runActive} />
            </div>
          </div>
          <ResizeHandle direction="horizontal" label="Resize output panel" onResize={(d) => setBottomH((h) => clamp(h - d, 120, 480))} />
          <div className="h-56 shrink-0 bg-panel lg:h-[var(--bottom-h)]">
            <BottomPanel stdin={ws.stdin} onStdin={ws.setStdin} runState={runner.state} runCount={runner.runCount} />
          </div>
        </section>

        <ResizeHandle direction="vertical" label="Resize Buddy AI sidebar" onResize={(d) => setRightW((w) => clamp(w - d, 240, 480))} />
        <aside aria-label="Buddy AI" className={`${show("buddy")} min-h-0 flex-1 flex-col bg-panel lg:flex lg:w-[var(--right-w)] lg:flex-none`}>
          <AssistantPanel language={ws.active.language} selection={selection} code={ws.active.content} runOutput={lastRunErrors} onNewFile={newFileFromAnswer} />
        </aside>
      </div>
    </div>
  );
}
