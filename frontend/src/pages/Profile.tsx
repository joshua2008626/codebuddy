import { useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Field } from "../components/Field";
import { ApiError, changePasswordRequest, deleteAccountRequest, updateDisplayName } from "../lib/api";
import { nameProblem, passwordProblem } from "../lib/validation";
import { useAuth } from "../hooks/useAuth";

const msg = (e: unknown) => (e instanceof ApiError ? e.message : "Something went wrong. Try again.");

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel mt-6 p-5">
      <h2 className="font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Status({ ok, error }: { ok: string | null; error: string | null }) {
  return (
    <>
      {ok && <p role="status" className="mt-3 text-sm text-ok">{ok}</p>}
      {error && <p role="alert" className="mt-3 text-sm text-danger">{error}</p>}
    </>
  );
}

export default function Profile() {
  const { user, setUser, clear, logout } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState(user?.display_name ?? "");
  const [nameOk, setNameOk] = useState<string | null>(null);
  const [nameErr, setNameErr] = useState<string | null>(null);
  const [nameBusy, setNameBusy] = useState(false);

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [pwOk, setPwOk] = useState<string | null>(null);
  const [pwErr, setPwErr] = useState<string | null>(null);
  const [pwBusy, setPwBusy] = useState(false);

  const [confirming, setConfirming] = useState(false);
  const [delPw, setDelPw] = useState("");
  const [delErr, setDelErr] = useState<string | null>(null);
  const [delBusy, setDelBusy] = useState(false);

  const [logoutErr, setLogoutErr] = useState<string | null>(null);

  if (!user) return null; // ProtectedRoute guarantees a user; this only satisfies the type checker

  async function saveName(e: FormEvent) {
    e.preventDefault();
    setNameOk(null);
    const problem = nameProblem(name);
    setNameErr(problem);
    if (problem || nameBusy) return;
    setNameBusy(true);
    try {
      setUser(await updateDisplayName(name.trim()));
      setNameOk("Name saved.");
    } catch (err) {
      setNameErr(msg(err));
    } finally {
      setNameBusy(false);
    }
  }

  async function savePassword(e: FormEvent) {
    e.preventDefault();
    setPwOk(null);
    setPwErr(null);
    if (current === "") return setPwErr("Enter your current password.");
    const problem = passwordProblem(next);
    if (problem) return setPwErr(problem);
    if (pwBusy) return;
    setPwBusy(true);
    try {
      await changePasswordRequest({ currentPassword: current, newPassword: next });
      setCurrent("");
      setNext("");
      setPwOk("Password changed. You’ve been logged out on your other devices.");
    } catch (err) {
      setPwErr(msg(err));
    } finally {
      setPwBusy(false);
    }
  }

  async function deleteAccount(e: FormEvent) {
    e.preventDefault();
    setDelErr(null);
    if (delPw === "") return setDelErr("Enter your password to confirm.");
    if (delBusy) return;
    setDelBusy(true);
    try {
      await deleteAccountRequest(delPw);
      clear();
      navigate("/", { replace: true });
    } catch (err) {
      setDelErr(msg(err));
      setDelBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-xl px-5 py-12">
        <h1 className="text-2xl font-semibold tracking-tight">Your profile</h1>
        <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
          <dt className="text-muted">Email</dt><dd>{user.email}</dd>
          <dt className="text-muted">Joined</dt><dd>{new Date(user.created_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}</dd>
        </dl>

        <Section title="Name">
          <form onSubmit={saveName} noValidate className="mt-3 space-y-3">
            <Field label="Display name" value={name} onChange={(e) => { setName(e.target.value); setNameOk(null); }} maxLength={60} error={nameErr} autoComplete="name" />
            <button type="submit" disabled={nameBusy} className="btn-primary">{nameBusy && <Loader2 size={14} className="animate-spin" aria-hidden />} Save name</button>
            <Status ok={nameOk} error={null} />
          </form>
        </Section>

        <Section title="Change password">
          <form onSubmit={savePassword} noValidate className="mt-3 space-y-3">
            <Field label="Current password" type="password" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} />
            <Field label="New password" type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} hint="At least 10 characters." />
            <button type="submit" disabled={pwBusy} className="btn-primary">{pwBusy && <Loader2 size={14} className="animate-spin" aria-hidden />} Change password</button>
            <Status ok={pwOk} error={pwErr} />
          </form>
        </Section>

        <Section title="Log out">
          <p className="mt-2 text-sm text-muted">This ends your session in this browser.</p>
          <button type="button" className="btn-ghost mt-3" onClick={async () => { const err = await logout(); if (err) setLogoutErr(err); else navigate("/", { replace: true }); }}>Log out</button>
          <Status ok={null} error={logoutErr} />
        </Section>

        <Section title="Delete account">
          <p className="mt-2 text-sm text-muted">This permanently deletes your account. It can’t be undone.</p>
          {!confirming ? (
            <button type="button" className="btn-ghost mt-3 !border-danger !text-danger" onClick={() => setConfirming(true)}>Delete my account…</button>
          ) : (
            <form onSubmit={deleteAccount} noValidate className="mt-3 space-y-3">
              <Field label="Enter your password to confirm" type="password" autoComplete="current-password" value={delPw} onChange={(e) => setDelPw(e.target.value)} />
              <div className="flex gap-2">
                <button type="submit" disabled={delBusy} className="btn bg-danger text-white hover:bg-danger/90">{delBusy && <Loader2 size={14} className="animate-spin" aria-hidden />} Delete account for good</button>
                <button type="button" className="btn-ghost" onClick={() => { setConfirming(false); setDelPw(""); setDelErr(null); }}>Cancel</button>
              </div>
              <Status ok={null} error={delErr} />
            </form>
          )}
        </Section>
      </main>
    </>
  );
}
