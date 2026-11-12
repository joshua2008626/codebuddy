import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Check, Download, FolderOpen, Loader2, Pencil, Plus, Trash2, X } from "lucide-react";
import { Navbar } from "../components/Navbar";
import {
  ApiError, createProject, deleteProject, downloadProject, listProjects, renameProject, type ProjectSummary,
} from "../lib/api";
import { LANG_LIST, type LangId } from "../lib/languages";
import { saveBlob } from "../lib/download";
import { readLocalFiles } from "../hooks/useWorkspace";
import { formatDate } from "../lib/format";

const msg = (e: unknown) => (e instanceof ApiError ? e.message : "Something went wrong. Try again.");

export default function Projects() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [items, setItems] = useState<ProjectSummary[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [name, setName] = useState("");
  const [lang, setLang] = useState<LangId>("python");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoadError(null);
    listProjects().then(setItems).catch((e) => setLoadError(msg(e)));
  }, []);
  useEffect(load, [load]);

  async function run(action: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (e) {
      setError(msg(e));
    } finally {
      setBusy(false);
    }
  }

  const create = (e: FormEvent) => {
    e.preventDefault();
    void run(async () => {
      const p = await createProject({ name, language: lang });
      navigate(`/projects/${p.id}`);
    });
  };

  const importLocal = () =>
    void run(async () => {
      const files = readLocalFiles().map((f) => ({ name: f.name, content: f.content }));
      const p = await createProject({ name: "Imported from browser", files });
      navigate(`/projects/${p.id}`);
    });

  const rename = (e: FormEvent, id: string) => {
    e.preventDefault();
    void run(async () => {
      await renameProject(id, renameValue);
      setRenamingId(null);
      load();
    });
  };

  const remove = (id: string) =>
    void run(async () => {
      setConfirmId(null);
      await deleteProject(id);
      load();
    });

  const download = (id: string) =>
    void run(async () => {
      const { blob, filename } = await downloadProject(id);
      saveBlob(blob, filename);
    });

  const iconBtn = "rounded-chip p-1.5 text-muted hover:bg-raised hover:text-fg";

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-6 pb-20 pt-24">
        <h1 className="text-3xl font-semibold tracking-tight">My projects</h1>
        <p className="mt-2 text-sm text-muted">Projects are saved to your account and autosaved as you type. Up to 50 projects, 20 files each.</p>

        <form onSubmit={create} className="panel mt-6 flex flex-wrap items-end gap-3 p-4">
          <div className="min-w-[12rem] flex-1">
            <label htmlFor="proj-name" className="text-xs text-muted">New project name</label>
            <input
              id="proj-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={200}
              placeholder="e.g. Sorting practice"
              className="mt-1 w-full rounded-chip border border-line bg-ink px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="proj-lang" className="text-xs text-muted">First file</label>
            <select id="proj-lang" value={lang} onChange={(e) => setLang(e.target.value as LangId)} className="mt-1 block rounded-chip border border-line bg-ink px-2 py-2 text-sm">
              {LANG_LIST.map((l) => <option key={l.id} value={l.id}>{l.label}</option>)}
            </select>
          </div>
          <button type="submit" disabled={busy || !name.trim()} className="btn-primary">
            {busy ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Plus size={15} aria-hidden />} Create
          </button>
        </form>

        {params.get("from") === "workspace" && (
          <div className="panel mt-4 flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
            <span>Want to keep what you wrote in the browser workspace? Copy those files into a new project.</span>
            <button type="button" className="btn-ghost" disabled={busy} onClick={importLocal}>Save browser files as a project</button>
          </div>
        )}

        {error && <p role="alert" className="mt-4 text-sm text-danger">{error}</p>}

        <section aria-label="Your projects" className="mt-8">
          {loadError ? (
            <div role="alert" className="rounded-panel border border-danger/40 bg-danger/10 p-4 text-sm">
              <p>{loadError}</p>
              <button type="button" className="btn-ghost mt-3" onClick={load}>Try again</button>
            </div>
          ) : items === null ? (
            <p className="flex items-center gap-2 text-sm text-muted" role="status"><Loader2 size={16} className="animate-spin" aria-hidden /> Loading projects…</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-muted">No projects yet. Create one above, or <Link to="/workspace" className="text-cyan underline">use the scratch workspace</Link>.</p>
          ) : (
            <ul className="space-y-2">
              {items.map((p) => (
                <li key={p.id} className="panel flex flex-wrap items-center gap-2 p-3">
                  {renamingId === p.id ? (
                    <form onSubmit={(e) => rename(e, p.id)} className="flex min-w-0 flex-1 items-center gap-1">
                      <input autoFocus aria-label={`New name for ${p.name}`} value={renameValue} maxLength={200} onChange={(e) => setRenameValue(e.target.value)} className="min-w-0 flex-1 rounded-chip border border-line bg-ink px-2 py-1 text-sm" />
                      <button type="submit" className={iconBtn} aria-label="Save name"><Check size={15} /></button>
                      <button type="button" className={iconBtn} aria-label="Cancel rename" onClick={() => setRenamingId(null)}><X size={15} /></button>
                    </form>
                  ) : (
                    <>
                      <Link to={`/projects/${p.id}`} className="flex min-w-0 flex-1 items-center gap-3 hover:text-volt">
                        <FolderOpen size={18} className="shrink-0 text-cyan" aria-hidden />
                        <span className="min-w-0">
                          <span className="block truncate font-medium">{p.name}</span>
                          <span className="block text-xs text-muted">{p.file_count} {p.file_count === 1 ? "file" : "files"} · updated {formatDate(p.updated_at)}</span>
                        </span>
                      </Link>
                      {confirmId === p.id ? (
                        <span className="flex items-center gap-1 text-xs">
                          Delete this project and its files?
                          <button type="button" className={iconBtn} aria-label={`Confirm delete ${p.name}`} onClick={() => remove(p.id)}><Check size={15} /></button>
                          <button type="button" className={iconBtn} aria-label="Cancel delete" onClick={() => setConfirmId(null)}><X size={15} /></button>
                        </span>
                      ) : (
                        <span className="flex">
                          <button type="button" className={iconBtn} aria-label={`Download ${p.name} as zip`} onClick={() => download(p.id)}><Download size={15} /></button>
                          <button type="button" className={iconBtn} aria-label={`Rename ${p.name}`} onClick={() => { setRenamingId(p.id); setRenameValue(p.name); }}><Pencil size={15} /></button>
                          <button type="button" className={iconBtn} aria-label={`Delete ${p.name}`} onClick={() => setConfirmId(p.id)}><Trash2 size={15} /></button>
                        </span>
                      )}
                    </>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </>
  );
}
