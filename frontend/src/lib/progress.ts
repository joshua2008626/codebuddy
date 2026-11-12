/**
 * Practice progress, kept in this browser's localStorage until accounts arrive (phase 6).
 * The functions here are pure so they can be unit-tested; storage access is at the bottom.
 *
 * Only real grading results are recorded: callers pass the verdict returned by the server.
 */
export type Verdict = "accepted" | "wrong_answer" | "compile_error" | "runtime_error" | "time_limit";

export interface ChallengeProgress {
  solved: boolean;
  attempts: number;
  /** Most tests passed in any one submission, and how many tests there were. */
  bestPassed: number;
  total: number;
  lastVerdict: Verdict | null;
  solvedAt: string | null; // ISO date of the first accepted submission
}

export type ProgressMap = Record<string, ChallengeProgress>;

const EMPTY: ChallengeProgress = { solved: false, attempts: 0, bestPassed: 0, total: 0, lastVerdict: null, solvedAt: null };

export function recordSubmission(map: ProgressMap, id: string, verdict: Verdict, passed: number, total: number, now: Date = new Date()): ProgressMap {
  const prev = map[id] ?? EMPTY;
  const accepted = verdict === "accepted";
  return {
    ...map,
    [id]: {
      solved: prev.solved || accepted, // once solved, a later wrong attempt does not undo it
      attempts: prev.attempts + 1,
      bestPassed: Math.max(prev.bestPassed, passed),
      total,
      lastVerdict: verdict,
      solvedAt: prev.solvedAt ?? (accepted ? now.toISOString() : null),
    },
  };
}

export interface Summary {
  solved: number;
  total: number;
  byDifficulty: Record<string, { solved: number; total: number }>;
}

export function summarize(map: ProgressMap, challenges: { id: string; difficulty: string }[]): Summary {
  const byDifficulty: Summary["byDifficulty"] = {};
  let solved = 0;
  for (const c of challenges) {
    const d = (byDifficulty[c.difficulty] ??= { solved: 0, total: 0 });
    d.total++;
    if (map[c.id]?.solved) {
      d.solved++;
      solved++;
    }
  }
  return { solved, total: challenges.length, byDifficulty };
}

/** Accepts anything from storage and keeps only well-formed entries, so corrupted data can't crash the page. */
export function parseProgress(raw: string | null): ProgressMap {
  if (!raw) return {};
  try {
    const data = JSON.parse(raw) as unknown;
    if (!data || typeof data !== "object" || Array.isArray(data)) return {};
    const out: ProgressMap = {};
    for (const [id, v] of Object.entries(data as Record<string, unknown>)) {
      const p = v as Partial<ChallengeProgress> | null;
      if (p && typeof p === "object" && typeof p.solved === "boolean" && Number.isInteger(p.attempts) && Number.isInteger(p.bestPassed) && Number.isInteger(p.total)) {
        out[id] = {
          solved: p.solved,
          attempts: p.attempts as number,
          bestPassed: p.bestPassed as number,
          total: p.total as number,
          lastVerdict: typeof p.lastVerdict === "string" ? (p.lastVerdict as Verdict) : null,
          solvedAt: typeof p.solvedAt === "string" ? p.solvedAt : null,
        };
      }
    }
    return out;
  } catch {
    return {};
  }
}

const KEY = "codebuddy-progress-v1";

export function loadProgress(): ProgressMap {
  try {
    return parseProgress(localStorage.getItem(KEY));
  } catch {
    return {};
  }
}

/** Returns false when storage is blocked, so the UI can say progress is not being kept. */
export function saveProgress(map: ProgressMap): boolean {
  try {
    localStorage.setItem(KEY, JSON.stringify(map));
    return true;
  } catch {
    return false;
  }
}
