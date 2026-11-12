import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Field } from "../components/Field";
import { ApiError } from "../lib/api";
import { emailProblem, nameProblem, passwordProblem } from "../lib/validation";
import { useAuth } from "../hooks/useAuth";

export default function Signup() {
  const { state, signup } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? "/workspace";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [errors, setErrors] = useState<{ name?: string | null; email?: string | null; password?: string | null }>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (state.status === "authenticated") return <Navigate to={from} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    const next = { name: nameProblem(name), email: emailProblem(email), password: passwordProblem(password) };
    setErrors(next);
    setError(null);
    if (next.name || next.email || next.password) return;

    setBusy(true);
    try {
      await signup(email.trim(), name.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-sm px-5 py-16">
        <h1 className="text-2xl font-semibold tracking-tight">Create your account</h1>
        <p className="mt-1 text-sm text-muted">Save your projects and keep your practice progress.</p>

        <form onSubmit={submit} noValidate className="mt-6 space-y-4">
          <Field label="Name" name="name" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} error={errors.name} maxLength={60} autoFocus />
          <Field label="Email" type="email" name="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} />
          <Field
            label="Password"
            type={show ? "text" : "password"}
            name="new-password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            hint="At least 10 characters. A few random words make a strong password."
          />
          <label className="flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" checked={show} onChange={(e) => setShow(e.target.checked)} /> Show password
          </label>

          {error && <p role="alert" className="rounded-chip border border-danger/40 bg-danger/10 p-2.5 text-sm text-danger">{error}</p>}

          <button type="submit" disabled={busy} className="btn-primary w-full !py-2.5">
            {busy && <Loader2 size={14} className="animate-spin" aria-hidden />} {busy ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-sm text-muted">Already have an account? <Link to="/login" state={{ from }} className="text-volt hover:underline">Log in</Link></p>
      </main>
    </>
  );
}
