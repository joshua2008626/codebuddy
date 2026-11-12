import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Field } from "../components/Field";
import { ApiError } from "../lib/api";
import { emailProblem } from "../lib/validation";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const { state, login } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? "/workspace";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (state.status === "authenticated") return <Navigate to={from} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    const problem = emailProblem(email);
    setEmailError(problem);
    setError(null);
    if (problem) return;
    if (password === "") {
      setError("Enter your password.");
      return;
    }
    setBusy(true);
    try {
      await login(email.trim(), password);
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
        <h1 className="text-2xl font-semibold tracking-tight">Log in</h1>
        <p className="mt-1 text-sm text-muted">Pick up where you left off.</p>

        <form onSubmit={submit} noValidate className="mt-6 space-y-4">
          <Field label="Email" type="email" name="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} error={emailError} autoFocus />
          <Field label="Password" type="password" name="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />

          {error && <p role="alert" className="rounded-chip border border-danger/40 bg-danger/10 p-2.5 text-sm text-danger">{error}</p>}

          <button type="submit" disabled={busy} className="btn-primary w-full !py-2.5">
            {busy && <Loader2 size={14} className="animate-spin" aria-hidden />} {busy ? "Logging in…" : "Log in"}
          </button>
        </form>

        <p className="mt-6 text-sm text-muted">New here? <Link to="/signup" state={{ from }} className="text-volt hover:underline">Create an account</Link></p>
      </main>
    </>
  );
}
