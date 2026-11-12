import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError, fetchMe, loginRequest, logoutRequest, signupRequest, type User } from "../lib/api";

/** "unavailable" means the server couldn't be reached, which is different from being logged out. */
type AuthState =
  | { status: "loading" }
  | { status: "anonymous" }
  | { status: "authenticated"; user: User }
  | { status: "unavailable"; message: string };

interface AuthApi {
  state: AuthState;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, displayName: string, password: string) => Promise<void>;
  /** Resolves to an error message if the server could not confirm the logout, otherwise null. */
  logout: () => Promise<string | null>;
  refresh: () => Promise<void>;
  setUser: (u: User) => void;
  clear: () => void;
}

const Ctx = createContext<AuthApi | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  const refresh = useCallback(async () => {
    try {
      setState({ status: "authenticated", user: await fetchMe() });
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) setState({ status: "anonymous" });
      else setState({ status: "unavailable", message: e instanceof ApiError ? e.message : "Couldn’t check your login." });
    }
  }, []);

  useEffect(() => void refresh(), [refresh]);

  const api = useMemo<AuthApi>(
    () => ({
      state,
      user: state.status === "authenticated" ? state.user : null,
      login: async (email, password) => {
        setState({ status: "authenticated", user: await loginRequest({ email, password }) });
      },
      signup: async (email, displayName, password) => {
        setState({ status: "authenticated", user: await signupRequest({ email, displayName, password }) });
      },
      logout: async () => {
        try {
          await logoutRequest();
          setState({ status: "anonymous" });
          return null;
        } catch (e) {
          // Stay logged in: pretending to be logged out while the server still accepts the cookie would be misleading.
          return e instanceof ApiError ? e.message : "Couldn’t log you out. Try again.";
        }
      },
      refresh,
      setUser: (user) => setState({ status: "authenticated", user }),
      clear: () => setState({ status: "anonymous" }),
    }),
    [state, refresh],
  );

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthApi {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used inside <AuthProvider>");
  return v;
}
