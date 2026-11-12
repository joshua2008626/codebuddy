import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { LANGS, LANG_LIST, langFromName, type LangId } from "../lib/languages";
import { formatCode } from "../lib/format";

/**
 * Workspace state: open files, the active file and stdin.
 *
 * Persistence for now is this browser's localStorage only. Account-backed projects
 * (database storage) replace it in later phases, and the UI says so honestly.
 */
export interface WsFile {
  id: string;
  name: string;
  language: LangId;
  content: string;
}

interface Persisted {
  files: WsFile[];
  activeId: string;
  stdin: string;
}

export type SaveStatus = "saved" | "saving" | "unavailable" | "failed";

/** File operations may be answered at once (browser storage) or after a server round trip (projects). */
export type FileOpResult = string | null | Promise<string | null>;

/** What the workspace screen needs from a file store. Implemented by useWorkspace (browser) and useRemoteWorkspace (account). */
export interface WorkspaceApi {
  files: WsFile[];
  active: WsFile;
  stdin: string;
  saveStatus: SaveStatus;
  /** Where files are kept, used for honest wording in the toolbar. */
  storage: "browser" | "account";
  /** Extra detail to show beside the save status, such as why a save failed. */
  saveNote: string | null;
  setActive: (id: string) => void;
  setContent: (id: string, content: string) => void;
  setStdin: (v: string) => void;
  /** Each returns an error message to show, or null on success. */
  createFile: (name: string, content?: string) => FileOpResult;
  renameFile: (id: string, name: string) => FileOpResult;
  deleteFile: (id: string) => FileOpResult | void;
  resetActive: () => void;
  switchLanguage: (lang: LangId) => void;
  formatActive: () => void;
}

const KEY = "codebuddy-workspace-v1";
export const NAME_RE = /^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$/;

function newId(): string {
  return globalThis.crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function starterFile(lang: LangId): WsFile {
  const cfg = LANGS[lang];
  return { id: newId(), name: cfg.defaultName, language: lang, content: cfg.template };
}

function defaults(): Persisted {
  const files = LANG_LIST.map((l) => starterFile(l.id));
  return { files, activeId: files[0].id, stdin: "" };
}

/** Reads and validates saved state. Anything malformed falls back to the starter files. */
function load(): Persisted {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return defaults();
    const p = JSON.parse(raw) as Partial<Persisted>;
    const files = Array.isArray(p.files)
      ? p.files.filter(
          (f): f is WsFile =>
            !!f &&
            typeof f.id === "string" &&
            typeof f.name === "string" &&
            typeof f.content === "string" &&
            (f.language === "python" || f.language === "c" || f.language === "java"),
        )
      : [];
    if (files.length === 0) return defaults();
    const activeId = files.some((f) => f.id === p.activeId) ? (p.activeId as string) : files[0].id;
    return { files, activeId, stdin: typeof p.stdin === "string" ? p.stdin : "" };
  } catch {
    return defaults();
  }
}

/** The files currently saved in this browser's scratch workspace (starter files if none), for saving them as a project. */
export function readLocalFiles(): WsFile[] {
  return load().files;
}

/** Returns an error message, or null when the name is valid and unused. */
export function validateName(name: string, files: WsFile[], exceptId?: string): string | null {
  if (!NAME_RE.test(name)) return "Use letters, numbers, dots, dashes or underscores (up to 64 characters).";
  if (!langFromName(name)) return "File names must end in .py, .c or .java.";
  if (files.some((f) => f.id !== exceptId && f.name.toLowerCase() === name.toLowerCase())) return "A file with that name already exists.";
  return null;
}

export function useWorkspace(): WorkspaceApi {
  const [state, setState] = useState<Persisted>(load);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("saved");
  const firstRun = useRef(true);

  // Debounced save so typing does not write on every keystroke.
  useEffect(() => {
    if (firstRun.current) {
      firstRun.current = false;
      return;
    }
    setSaveStatus("saving");
    const t = window.setTimeout(() => {
      try {
        localStorage.setItem(KEY, JSON.stringify(state));
        setSaveStatus("saved");
      } catch {
        setSaveStatus("unavailable"); // storage blocked or full; work continues in memory
      }
    }, 400);
    return () => window.clearTimeout(t);
  }, [state]);

  const active = useMemo(() => state.files.find((f) => f.id === state.activeId) ?? state.files[0], [state]);

  const setActive = useCallback((id: string) => setState((s) => ({ ...s, activeId: id })), []);

  const setContent = useCallback(
    (id: string, content: string) =>
      setState((s) => ({ ...s, files: s.files.map((f) => (f.id === id ? { ...f, content } : f)) })),
    [],
  );

  const setStdin = useCallback((stdin: string) => setState((s) => ({ ...s, stdin })), []);

  const createFile = useCallback(
    (name: string, content?: string): string | null => {
      const trimmed = name.trim();
      const err = validateName(trimmed, state.files);
      if (err) return err;
      const language = langFromName(trimmed)!;
      const file: WsFile = { id: newId(), name: trimmed, language, content: content ?? LANGS[language].template };
      setState((s) => ({ files: [...s.files, file], activeId: file.id, stdin: s.stdin }));
      return null;
    },
    [state.files],
  );

  const renameFile = useCallback(
    (id: string, name: string): string | null => {
      const trimmed = name.trim();
      const err = validateName(trimmed, state.files, id);
      if (err) return err;
      const language = langFromName(trimmed)!;
      setState((s) => ({ ...s, files: s.files.map((f) => (f.id === id ? { ...f, name: trimmed, language } : f)) }));
      return null;
    },
    [state.files],
  );

  const deleteFile = useCallback((id: string) => {
    setState((s) => {
      const remaining = s.files.filter((f) => f.id !== id);
      // Never leave the workspace without a file.
      if (remaining.length === 0) {
        const fresh = starterFile("python");
        return { ...s, files: [fresh], activeId: fresh.id };
      }
      return { ...s, files: remaining, activeId: s.activeId === id ? remaining[0].id : s.activeId };
    });
  }, []);

  /** Restores the active file to its language's starter template. */
  const resetActive = useCallback(() => {
    setState((s) => {
      const f = s.files.find((x) => x.id === s.activeId);
      if (!f) return s;
      return { ...s, files: s.files.map((x) => (x.id === f.id ? { ...x, content: LANGS[x.language].template } : x)) };
    });
  }, []);

  /** Switches to the first file of that language, creating one from the template if none exists. */
  const switchLanguage = useCallback((lang: LangId) => {
    setState((s) => {
      const existing = s.files.find((f) => f.language === lang);
      if (existing) return { ...s, activeId: existing.id };
      const file = starterFile(lang);
      return { ...s, files: [...s.files, file], activeId: file.id };
    });
  }, []);

  const formatActive = useCallback(() => {
    setState((s) => {
      const f = s.files.find((x) => x.id === s.activeId);
      if (!f) return s;
      const formatted = formatCode(f.content, f.language);
      return formatted === f.content ? s : { ...s, files: s.files.map((x) => (x.id === f.id ? { ...x, content: formatted } : x)) };
    });
  }, []);

  return {
    files: state.files,
    active,
    stdin: state.stdin,
    saveStatus,
    storage: "browser",
    saveNote: null,
    setActive,
    setContent,
    setStdin,
    createFile,
    renameFile,
    deleteFile,
    resetActive,
    switchLanguage,
    formatActive,
  };
}
