import type { LangId } from "./languages";

/** Empty in development (Vite proxies /api to the backend). Set VITE_API_URL when the API is on another origin. */
const API_BASE: string = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
  ) {
    super(message);
  }
}

/** Shapes the backend returns. Field names match the API (snake_case). */
export type Outcome = "success" | "compile_error" | "runtime_error" | "time_limit" | "internal_error";

export interface ExecuteResult {
  outcome: Outcome;
  status_id: number;
  status_text: string;
  stdout: string;
  stderr: string;
  compile_output: string;
  message: string;
  time_seconds: number | null;
  memory_kb: number | null;
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(API_BASE + path, {
      ...init,
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
    });
  } catch {
    throw new ApiError("Can’t reach the CodeBuddy server. Check that the backend is running.", "network", 0);
  }

  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    /* non-JSON body */
  }

  if (!res.ok) {
    const detail = (body as { detail?: unknown } | null)?.detail;
    if (detail && typeof detail === "object" && !Array.isArray(detail) && "message" in detail) {
      const d = detail as { code?: string; message: string };
      throw new ApiError(d.message, d.code ?? "error", res.status);
    }
    if (res.status === 422) {
      // FastAPI sends a list of validation problems; show the first one in plain words.
      const first = Array.isArray(detail) ? (detail[0] as { msg?: string } | undefined)?.msg : undefined;
      const msg = first?.replace(/^Value error, /, "");
      throw new ApiError(msg ? `${msg.replace(/\.?$/, "")}.` : "That request wasn’t valid.", "validation", 422);
    }
    throw new ApiError(`The server returned an error (${res.status}).`, "error", res.status);
  }
  return body as T;
}

export function executeCode(p: { language: LangId; sourceCode: string; stdin: string }) {
  return request<ExecuteResult>("/api/execute", {
    method: "POST",
    body: JSON.stringify({ language: p.language, source_code: p.sourceCode, stdin: p.stdin }),
  });
}

export type AiMode = "explain" | "debug" | "simplify" | "generate" | "convert" | "algorithm" | "complexity" | "learn";

export interface AskParams {
  mode: AiMode;
  language: LangId;
  code: string;
  selection: string;
  prompt: string;
  targetLanguage?: LangId;
  runOutput: string;
}

export function askBuddy(p: AskParams) {
  return request<{ mode: AiMode; answer: string; model: string }>("/api/ai", {
    method: "POST",
    body: JSON.stringify({
      mode: p.mode,
      language: p.language,
      code: p.code,
      selection: p.selection,
      prompt: p.prompt,
      target_language: p.targetLanguage ?? null,
      run_output: p.runOutput,
    }),
  });
}

// ----------------------------------------------------------------------------- practice arena
export type Difficulty = "beginner" | "intermediate" | "advanced";

export interface ChallengeSummary {
  id: string;
  title: string;
  difficulty: Difficulty;
  summary: string;
  tags: string[];
}

export interface ChallengeDetail extends ChallengeSummary {
  statement: string;
  input_format: string;
  output_format: string;
  constraints: string[];
  samples: { input: string; output: string; note: string }[];
  starters: Record<LangId, string>;
}

export type TestStatus = "passed" | "failed" | "compile_error" | "runtime_error" | "time_limit" | "skipped";

export interface TestResult {
  index: number;
  hidden: boolean;
  status: TestStatus;
  time_seconds: number | null;
  memory_kb: number | null;
  /** Present for sample tests only. */
  input: string | null;
  expected: string | null;
  actual: string | null;
  stderr: string | null;
}

export interface SubmitResult {
  verdict: "accepted" | "wrong_answer" | "compile_error" | "runtime_error" | "time_limit";
  passed: number;
  total: number;
  first_failure: number | null;
  compile_output: string;
  results: TestResult[];
}

export const listChallenges = () => request<ChallengeSummary[]>("/api/challenges", { method: "GET" });
export const getChallenge = (id: string) => request<ChallengeDetail>(`/api/challenges/${encodeURIComponent(id)}`, { method: "GET" });
export const submitSolution = (id: string, language: LangId, sourceCode: string) =>
  request<SubmitResult>(`/api/challenges/${encodeURIComponent(id)}/submit`, {
    method: "POST",
    body: JSON.stringify({ language, source_code: sourceCode }),
  });

// ------------------------------------------------------------------------------------ accounts
export interface User {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

export const fetchMe = () => request<User>("/api/auth/me", { method: "GET" });
export const signupRequest = (p: { email: string; displayName: string; password: string }) =>
  request<User>("/api/auth/signup", { method: "POST", body: JSON.stringify({ email: p.email, display_name: p.displayName, password: p.password }) });
export const loginRequest = (p: { email: string; password: string }) =>
  request<User>("/api/auth/login", { method: "POST", body: JSON.stringify(p) });
export const logoutRequest = () => request<null>("/api/auth/logout", { method: "POST" });
export const updateDisplayName = (displayName: string) =>
  request<User>("/api/auth/me", { method: "PATCH", body: JSON.stringify({ display_name: displayName }) });
export const changePasswordRequest = (p: { currentPassword: string; newPassword: string }) =>
  request<null>("/api/auth/me/password", { method: "POST", body: JSON.stringify({ current_password: p.currentPassword, new_password: p.newPassword }) });
export const deleteAccountRequest = (password: string) =>
  request<null>("/api/auth/me/delete", { method: "POST", body: JSON.stringify({ password }) });

// -------------------------------------------------------------------------------------- projects
export interface ProjectFile {
  id: string;
  name: string;
  language: LangId;
  content: string;
  updated_at: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  file_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  files: ProjectFile[];
}

const enc = encodeURIComponent;
export const listProjects = () => request<ProjectSummary[]>("/api/projects", { method: "GET" });
export const createProject = (p: { name: string; language?: LangId; files?: { name: string; content: string }[] }) =>
  request<ProjectDetail>("/api/projects", { method: "POST", body: JSON.stringify(p) });
export const getProject = (id: string) => request<ProjectDetail>(`/api/projects/${enc(id)}`, { method: "GET" });
export const renameProject = (id: string, name: string) =>
  request<ProjectDetail>(`/api/projects/${enc(id)}`, { method: "PATCH", body: JSON.stringify({ name }) });
export const deleteProject = (id: string) => request<null>(`/api/projects/${enc(id)}`, { method: "DELETE" });
export const createProjectFile = (id: string, name: string, content?: string) =>
  request<ProjectFile>(`/api/projects/${enc(id)}/files`, { method: "POST", body: JSON.stringify({ name, content: content ?? null }) });
export const updateProjectFile = (id: string, fileId: string, patch: { name?: string; content?: string }) =>
  request<ProjectFile>(`/api/projects/${enc(id)}/files/${enc(fileId)}`, { method: "PATCH", body: JSON.stringify(patch) });
export const deleteProjectFile = (id: string, fileId: string) =>
  request<null>(`/api/projects/${enc(id)}/files/${enc(fileId)}`, { method: "DELETE" });

/** Downloads the project's files as a .zip. Uses fetch (not a plain link) so it also works when the API is on another origin. */
export async function downloadProject(id: string): Promise<{ blob: Blob; filename: string }> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/projects/${enc(id)}/download`, { credentials: "include" });
  } catch {
    throw new ApiError("Can’t reach the CodeBuddy server. Check that the backend is running.", "network", 0);
  }
  if (!res.ok) {
    let message = `The server returned an error (${res.status}).`;
    try {
      const d = (await res.json()) as { detail?: { message?: string } };
      if (d.detail?.message) message = d.detail.message;
    } catch {
      /* keep the generic message */
    }
    throw new ApiError(message, "error", res.status);
  }
  const match = /filename="([^"]+)"/.exec(res.headers.get("content-disposition") ?? "");
  return { blob: await res.blob(), filename: match?.[1] ?? "codebuddy-project.zip" };
}

// ------------------------------------------------------------------------------------ learning hub
export interface LessonSummary {
  id: string;
  title: string;
  group: string;
  summary: string;
  minutes: number;
  languages: LangId[];
  exercise_id: string;
}

export interface LessonExample {
  title: string;
  language: LangId;
  code: string;
  /** What the example prints. The backend test suite runs every example with real compilers and checks this text. */
  output: string;
  stdin: string;
}

export interface LessonDetail extends LessonSummary {
  sections: { heading: string; body: string }[];
  examples: LessonExample[];
  exercise: ChallengeDetail;
}

export const listLessons = () => request<LessonSummary[]>("/api/lessons", { method: "GET" });
export const getLesson = (id: string) => request<LessonDetail>(`/api/lessons/${encodeURIComponent(id)}`, { method: "GET" });
