/**
 * Quick checks so people get feedback before a request is sent.
 * The server repeats and enforces every rule (and also rejects common passwords), so these are only a convenience.
 */
export const MIN_PASSWORD = 10;
export const MAX_PASSWORD = 128;

export function emailProblem(email: string): string | null {
  const e = email.trim();
  if (e === "") return "Enter your email address.";
  if (e.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) return "Enter a valid email address.";
  return null;
}

export function passwordProblem(password: string): string | null {
  if (password.length < MIN_PASSWORD) return `Use at least ${MIN_PASSWORD} characters.`;
  if (password.length > MAX_PASSWORD) return `Use at most ${MAX_PASSWORD} characters.`;
  return null;
}

export function nameProblem(name: string): string | null {
  const n = name.trim();
  if (n === "") return "Enter a name.";
  if (n.length > 60) return "Use at most 60 characters.";
  return null;
}
