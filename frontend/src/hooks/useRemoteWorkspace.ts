import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiError, createProjectFile, deleteProjectFile, getProject, updateProjectFile, type ProjectFile } from "../lib/api";
import { LANGS, langFromName, type LangId } from "../lib/languages";
import { formatCode } from "../lib/format";
import { validateName, type SaveStatus, type WorkspaceApi, type WsFile } from "./useWorkspace";

/**
 * Workspace backed by a project saved in the person's account.
 *
 * Edits appear instantly and are autosaved to the server after a short pause. If a save fails, the unsaved text
 * is kept and retried, and the toolbar says so. Last write wins: editing one project in two tabs at once will
 * overwrite whichever saved first.
 */
export type RemoteLoad =
  | { status: "loading" }
  | { status: "ready"; projectName: string }
  | { status: "error"; message: string; notFound: boolean };

const SAVE_DELAY_MS = 1500;
const RETRY_DELAY_MS = 5000;

const toWsFile = (f: ProjectFile): WsFile => ({ id: f.id, name: f.name, language: f.language, content: f.content });
const message = (e: unknown) => (e instanceof ApiError ? e.message : "Something went wrong. Try again.");

export function useRemoteWorkspace(projectId: string): WorkspaceApi & { load: RemoteLoad } {
  const [load, setLoad] = useState<RemoteLoad>({ status: "loading" });
  const [files, setFiles] = useState<WsFile[]>([]);
  const [activeId, setActiveId] = useState("");
  const [stdin, setStdin] = useState("");
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("saved");
  const [saveNote, setSaveNote] = useState<string | null>(null);

  const pending = useRef(new Map<string, string>()); // file id -> newest unsaved content
  const timer = useRef<number | undefined>(undefined);
  const flushing = useRef(false);

  // ------------------------------------------------------------------------------ loading
  useEffect(() => {
    let cancelled = false;
    pending.current.clear();
    setLoad({ status: "loading" });
    getProject(projectId)
      .then((p) => {
        if (cancelled) return;
        const list = p.files.map(toWsFile);
        setFiles(list);
        setActiveId(list[0]?.id ?? "");
        setSaveStatus("saved");
        setSaveNote(null);
        setLoad({ status: "ready", projectName: p.name });
      })
      .catch((e) => {
        if (!cancelled) setLoad({ status: "error", message: message(e), notFound: e instanceof ApiError && e.status === 404 });
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  // ------------------------------------------------------------------------------ saving
  const flush = useCallback(async () => {
    if (flushing.current) return;
    flushing.current = true;
    window.clearTimeout(timer.current);
    try {
      while (pending.current.size > 0) {
        const [id, content] = pending.current.entries().next().value as [string, string];
        try {
          await updateProjectFile(projectId, id, { content });
          if (pending.current.get(id) === content) pending.current.delete(id); // keep it if typing continued meanwhile
        } catch (e) {
          const err = e instanceof ApiError ? e : null;
          setSaveStatus("failed");
          if (err && [401, 403, 404].includes(err.status)) {
            setSaveNote(err.status === 401 ? "Your login expired. Log in again, then reopen this project. Unsaved changes are shown here only." : err.message);
          } else {
            setSaveNote(`${message(e)} Retrying…`);
            timer.current = window.setTimeout(() => void flush(), RETRY_DELAY_MS);
          }
          return;
        }
      }
      setSaveStatus("saved");
      setSaveNote(null);
    } finally {
      flushing.current = false;
    }
  }, [projectId]);

  const schedule = useCallback(() => {
    setSaveStatus("saving");
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => void flush(), SAVE_DELAY_MS);
  }, [flush]);

  // Save what is pending when leaving the page, and warn if the browser is closed with unsaved changes.
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (pending.current.size > 0) e.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => {
      window.removeEventListener("beforeunload", warn);
      window.clearTimeout(timer.current);
      if (pending.current.size > 0) void flush();
    };
  }, [flush]);

  // ------------------------------------------------------------------------------ editing
  const active = useMemo(() => files.find((f) => f.id === activeId) ?? files[0], [files, activeId]);

  const setContent = useCallback(
    (id: string, content: string) => {
      setFiles((fs) => fs.map((f) => (f.id === id ? { ...f, content } : f)));
      pending.current.set(id, content);
      schedule();
    },
    [schedule],
  );

  const createFile = useCallback(
    async (name: string, content?: string): Promise<string | null> => {
      const trimmed = name.trim();
      const problem = validateName(trimmed, files);
      if (problem) return problem;
      try {
        const f = toWsFile(await createProjectFile(projectId, trimmed, content));
        setFiles((fs) => [...fs, f]);
        setActiveId(f.id);
        return null;
      } catch (e) {
        return message(e);
      }
    },
    [files, projectId],
  );

  const renameFile = useCallback(
    async (id: string, name: string): Promise<string | null> => {
      const trimmed = name.trim();
      const problem = validateName(trimmed, files, id);
      if (problem) return problem;
      try {
        const f = await updateProjectFile(projectId, id, { name: trimmed });
        setFiles((fs) => fs.map((x) => (x.id === id ? { ...x, name: f.name, language: f.language } : x)));
        return null;
      } catch (e) {
        return message(e);
      }
    },
    [files, projectId],
  );

  const deleteFile = useCallback(
    async (id: string): Promise<string | null> => {
      try {
        await deleteProjectFile(projectId, id);
      } catch (e) {
        return message(e); // for example: a project needs at least one file
      }
      pending.current.delete(id);
      setFiles((fs) => fs.filter((f) => f.id !== id));
      setActiveId((cur) => (cur === id ? files.find((f) => f.id !== id)?.id ?? "" : cur));
      return null;
    },
    [files, projectId],
  );

  const resetActive = useCallback(() => {
    if (active) setContent(active.id, LANGS[active.language].template);
  }, [active, setContent]);

  const formatActive = useCallback(() => {
    if (!active) return;
    const formatted = formatCode(active.content, active.language);
    if (formatted !== active.content) setContent(active.id, formatted);
  }, [active, setContent]);

  const switchLanguage = useCallback(
    (lang: LangId) => {
      const existing = files.find((f) => f.language === lang);
      if (existing) setActiveId(existing.id);
      else if (langFromName(LANGS[lang].defaultName) === lang) {
        void createFile(LANGS[lang].defaultName).then((err) => {
          if (err) setSaveNote(err);
        });
      }
    },
    [files, createFile],
  );

  return {
    load,
    files,
    // Callers only render the workspace once `load` is ready, when there is always at least one file.
    active: active ?? { id: "", name: "", language: "python", content: "" },
    stdin,
    saveStatus,
    storage: "account",
    saveNote,
    setActive: setActiveId,
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
