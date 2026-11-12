import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Navbar } from "./Navbar";
import { useAuth } from "../hooks/useAuth";

/** Shows its children only to logged-in people. Everyone else is sent to the login page and returned afterwards. */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { state, refresh } = useAuth();
  const location = useLocation();

  if (state.status === "loading") {
    return (
      <>
        <Navbar />
        <p className="mx-auto mt-24 flex max-w-xl items-center gap-2 px-6 text-sm text-muted" role="status">
          <Loader2 size={16} className="animate-spin" aria-hidden /> Checking your login…
        </p>
      </>
    );
  }

  if (state.status === "unavailable") {
    return (
      <>
        <Navbar />
        <main className="mx-auto mt-20 max-w-xl px-6">
          <div role="alert" className="rounded-panel border border-danger/40 bg-danger/10 p-4 text-sm">
            <p className="font-medium text-danger">Couldn’t reach the server</p>
            <p className="mt-1">{state.message}</p>
            <button type="button" onClick={() => void refresh()} className="btn-ghost mt-3">Try again</button>
          </div>
        </main>
      </>
    );
  }

  if (state.status === "anonymous") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}
