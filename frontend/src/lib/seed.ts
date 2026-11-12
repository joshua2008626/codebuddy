import { LANGS, type LangId } from "./languages";

export interface WorkspaceSeed { name: string; language: LangId; content: string; stdin: string }

/** Validates navigation state before trusting it. */
export function parseSeed(v: unknown): WorkspaceSeed | null {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, unknown>;
  if (typeof o.name !== "string" || typeof o.content !== "string" || (o.language !== "python" && o.language !== "c" && o.language !== "java")) return null;
  if (o.content.length > 64000 || !o.name.endsWith(LANGS[o.language].ext)) return null;
  return { name: o.name, language: o.language, content: o.content, stdin: typeof o.stdin === "string" ? o.stdin.slice(0, 16000) : "" };
}
