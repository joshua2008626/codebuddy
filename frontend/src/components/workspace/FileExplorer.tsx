import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Check, FileCode, FolderOpen, Pencil, Plus, Trash2, X } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import type { WsFile } from "../../hooks/useWorkspace";

interface Props {
  files: WsFile[];
  activeId: string;
  onSelect: (id: string) => void;
  /** Return an error message to show, or null on success. May answer after a server round trip. */
  onCreate: (name: string) => Promise<string | null>;
  onRename: (id: string, name: string) => Promise<string | null> | string | null;
  onDelete: (id: string) => Promise<string | null>;
  storage: "browser" | "account";
}

export function FileExplorer({ files, activeId, onSelect, onCreate, onRename, onDelete, storage }: Props) {
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submitCreate(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    const err = await onCreate(newName);
    setBusy(false);
    setError(err);
    if (!err) {
      setCreating(false);
      setNewName("");
    }
  }

  async function submitRename(e: FormEvent, id: string) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    const err = await onRename(id, renameValue);
    setBusy(false);
    setError(err);
    if (!err) setRenamingId(null);
  }

  const iconBtn = "rounded-chip p-1 text-muted hover:bg-raised hover:text-fg";

  return (
    <div className="flex h-full flex-col overflow-y-auto p-3 text-sm">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-xs font-medium text-muted">Files</h2>
        <button type="button" className={iconBtn} aria-label="New file" onClick={() => { setCreating(true); setError(null); }}>
          <Plus size={15} />
        </button>
      </div>

      <ul className="space-y-0.5">
        {files.map((f) => (
          <li key={f.id}>
            {renamingId === f.id ? (
              <form onSubmit={(e) => submitRename(e, f.id)} className="flex items-center gap-1">
                <input
                  autoFocus
                  aria-label={`New name for ${f.name}`}
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  className="min-w-0 flex-1 rounded-chip border border-line bg-ink px-2 py-1 font-mono text-xs"
                />
                <button type="submit" className={iconBtn} aria-label="Save name"><Check size={14} /></button>
                <button type="button" className={iconBtn} aria-label="Cancel rename" onClick={() => { setRenamingId(null); setError(null); }}><X size={14} /></button>
              </form>
            ) : confirmId === f.id ? (
              <div className="flex items-center justify-between gap-1 rounded-chip bg-danger/10 px-2 py-1">
                <span className="truncate text-xs">Delete {f.name}?</span>
                <span className="flex shrink-0">
                  <button type="button" className={iconBtn} aria-label={`Confirm delete ${f.name}`} onClick={async () => { setConfirmId(null); setError(await onDelete(f.id)); }}><Check size={14} /></button>
                  <button type="button" className={iconBtn} aria-label="Cancel delete" onClick={() => setConfirmId(null)}><X size={14} /></button>
                </span>
              </div>
            ) : (
              <div className={`group flex items-center rounded-chip ${f.id === activeId ? "bg-raised" : "hover:bg-raised/60"}`}>
                <button
                  type="button"
                  onClick={() => onSelect(f.id)}
                  aria-current={f.id === activeId ? "true" : undefined}
                  className="flex min-w-0 flex-1 items-center gap-2 px-2 py-1.5 text-left"
                >
                  <FileCode size={14} className="shrink-0 text-cyan" aria-hidden />
                  <span className="truncate font-mono text-xs">{f.name}</span>
                </button>
                <span className="flex shrink-0 pr-1 opacity-100 lg:opacity-0 lg:group-focus-within:opacity-100 lg:group-hover:opacity-100">
                  <button type="button" className={iconBtn} aria-label={`Rename ${f.name}`} onClick={() => { setRenamingId(f.id); setRenameValue(f.name); setError(null); }}><Pencil size={13} /></button>
                  <button type="button" className={iconBtn} aria-label={`Delete ${f.name}`} onClick={() => setConfirmId(f.id)}><Trash2 size={13} /></button>
                </span>
              </div>
            )}
          </li>
        ))}
      </ul>

      {creating && (
        <form onSubmit={submitCreate} className="mt-2 flex items-center gap-1">
          <input
            autoFocus
            aria-label="New file name"
            placeholder="name.py, name.c or Name.java"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="min-w-0 flex-1 rounded-chip border border-line bg-ink px-2 py-1 font-mono text-xs"
          />
          <button type="submit" className={iconBtn} aria-label="Create file"><Check size={14} /></button>
          <button type="button" className={iconBtn} aria-label="Cancel" onClick={() => { setCreating(false); setError(null); }}><X size={14} /></button>
        </form>
      )}

      {error && <p role="alert" className="mt-2 text-xs text-danger">{error}</p>}

      <h2 className="mb-1 mt-6 text-xs font-medium text-muted">Projects</h2>
      {storage === "account" ? (
        <Link to="/projects" className="flex items-center gap-2 rounded-chip px-2 py-1.5 text-xs text-muted hover:bg-raised hover:text-fg">
          <FolderOpen size={14} aria-hidden /> All my projects
        </Link>
      ) : user ? (
        <>
          <p className="text-xs leading-relaxed text-muted">These files are saved in this browser only. Save them as a project to keep them in your account.</p>
          <Link to="/projects?from=workspace" className="mt-1 flex items-center gap-2 rounded-chip px-2 py-1.5 text-xs text-muted hover:bg-raised hover:text-fg">
            <FolderOpen size={14} aria-hidden /> My projects
          </Link>
        </>
      ) : (
        <p className="text-xs leading-relaxed text-muted">
          Your files are saved in this browser only. <Link to="/login" state={{ from: "/projects" }} className="text-cyan underline">Log in</Link> to keep projects in your account.
        </p>
      )}

      <h2 className="mb-1 mt-6 text-xs font-medium text-muted">Learn</h2>
      <Link to="/learn" className="flex items-center gap-2 rounded-chip px-2 py-1.5 text-xs text-muted hover:bg-raised hover:text-fg">
        <BookOpen size={14} aria-hidden /> Learning hub
      </Link>
    </div>
  );
}
