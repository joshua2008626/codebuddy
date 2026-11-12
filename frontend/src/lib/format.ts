import type { LangId } from "./languages";

/**
 * Code formatter used by the Format button.
 *
 * Monaco only ships formatters for web languages, so C, Java and Python get none out of the box.
 * This is deliberately modest rather than a full pretty-printer:
 *  - all languages: tabs to 4 spaces, trailing whitespace removed, at most 2 blank lines in a row,
 *    exactly one newline at the end of the file
 *  - C and Java: lines re-indented by brace depth
 *  - Python: indentation is never changed, because it is part of the program's meaning
 *
 * Known limits: Java text blocks (""") and multi-line expressions are not re-indented specially.
 */
const INDENT = "    ";

/** Strips comments and string/char literals from one line so braces inside them are not counted. */
function scan(line: string, inBlockComment: boolean): { code: string; inBlockComment: boolean } {
  let code = "";
  let i = 0;
  let inBlock = inBlockComment;
  while (i < line.length) {
    const c = line[i];
    const n = line[i + 1];
    if (inBlock) {
      if (c === "*" && n === "/") {
        inBlock = false;
        i += 2;
      } else i++;
      continue;
    }
    if (c === "/" && n === "*") { inBlock = true; i += 2; continue; }
    if (c === "/" && n === "/") break;
    if (c === '"' || c === "'") {
      const quote = c;
      i++;
      while (i < line.length && line[i] !== quote) {
        if (line[i] === "\\") i++; // skip the escaped character
        i++;
      }
      i++;
      code += quote + quote;
      continue;
    }
    code += c;
    i++;
  }
  return { code, inBlockComment: inBlock };
}

function reindentBraces(lines: string[]): string[] {
  let depth = 0;
  let inBlock = false;

  return lines.map((raw) => {
    const t = raw.trim();
    const startedInBlock = inBlock;
    const scanned = scan(t, inBlock);
    inBlock = scanned.inBlockComment;

    const opens = (scanned.code.match(/\{/g) ?? []).length;
    const closes = (scanned.code.match(/\}/g) ?? []).length;
    const leadingClosers = (scanned.code.trimStart().match(/^\}+/)?.[0] ?? "").length;

    let result: string;
    if (t === "") result = "";
    else if (startedInBlock) result = INDENT.repeat(depth) + (t.startsWith("*") ? " " : "") + t;
    else if (t.startsWith("#")) result = t; // C preprocessor directives stay at column 0
    else result = INDENT.repeat(Math.max(0, depth - leadingClosers)) + t;

    depth = Math.max(0, depth + opens - closes);
    return result;
  });
}

export function formatCode(code: string, lang: LangId): string {
  const normalized = code
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map((l) => l.replace(/\t/g, INDENT).replace(/[ ]+$/, ""));

  const indented = lang === "python" ? normalized : reindentBraces(normalized);

  // Allow at most two consecutive blank lines (two is normal between Python top-level definitions).
  const out: string[] = [];
  let blanks = 0;
  for (const l of indented) {
    blanks = l === "" ? blanks + 1 : 0;
    if (blanks <= 2) out.push(l);
  }

  const joined = out.join("\n").replace(/^\n+/, "").replace(/\n+$/, "");
  return joined === "" ? "" : joined + "\n";
}

/** "12 Nov 2026" from an ISO timestamp; empty string if it can't be parsed. */
export function formatDate(iso: string): string {
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}
