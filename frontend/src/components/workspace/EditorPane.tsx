import { useRef } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";
import { LANGS } from "../../lib/languages";
import { setupMonaco } from "../../lib/monacoSetup";
import type { WsFile } from "../../hooks/useWorkspace";
import type { Theme } from "../../lib/theme";

/** What the user has highlighted. Buddy AI uses this as context (phase 4). */
export interface EditorSelection {
  text: string;
  startLine: number;
  endLine: number;
}

interface Props {
  file: WsFile;
  theme: Theme;
  onChange: (value: string) => void;
  onSelection: (sel: EditorSelection | null) => void;
  onRun: () => void;
}

const MAX_SELECTION_CHARS = 20_000;

export function EditorPane({ file, theme, onChange, onSelection, onRun }: Props) {
  // The Monaco command below is registered once at mount, so it reads the latest handler through a ref.
  const runRef = useRef(onRun);
  runRef.current = onRun;

  const handleMount: OnMount = (editor, monaco) => {
    // Ctrl/Cmd+Enter runs the program. Monaco binds it to "insert line below" by default, so override it here.
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => runRef.current());

    editor.onDidChangeCursorSelection(() => {
      const sel = editor.getSelection();
      const model = editor.getModel();
      if (!sel || !model || sel.isEmpty()) {
        onSelection(null);
        return;
      }
      onSelection({
        text: model.getValueInRange(sel).slice(0, MAX_SELECTION_CHARS),
        startLine: sel.startLineNumber,
        endLine: sel.endLineNumber,
      });
    });
  };

  return (
    <Editor
      height="100%"
      // A distinct path per file gives each file its own model, so undo history is kept when switching tabs.
      path={file.id}
      language={LANGS[file.language].monaco}
      value={file.content}
      theme={theme === "dark" ? "codebuddy-dark" : "codebuddy-light"}
      beforeMount={setupMonaco}
      onMount={handleMount}
      onChange={(v) => onChange(v ?? "")}
      loading={<div className="p-4 text-sm text-muted">Loading editor…</div>}
      options={{
        fontFamily: '"JetBrains Mono", ui-monospace, monospace',
        fontSize: 14,
        lineHeight: 22,
        lineNumbers: "on",
        tabSize: 4,
        insertSpaces: true,
        autoIndent: "full",
        detectIndentation: false,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true, // follows panel resizing
        padding: { top: 12, bottom: 12 },
        bracketPairColorization: { enabled: true },
        quickSuggestions: { other: true, comments: false, strings: false },
        suggestOnTriggerCharacters: true,
        smoothScrolling: true,
        renderLineHighlight: "line",
        ariaLabel: `Code editor for ${file.name}`,
      }}
    />
  );
}
