import type { LangId } from "./languages";

/**
 * Minimal Markdown parser for Buddy AI answers.
 *
 * It only produces data (blocks and inline spans). The UI renders them as React text nodes, so any HTML
 * in a model answer is shown as plain text and never executed. Supported: fenced code, headings,
 * bullet and numbered lists, paragraphs, `inline code` and **bold**.
 */
export type Block =
  | { type: "code"; lang: string; code: string }
  | { type: "heading"; text: string }
  | { type: "p"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] };

export type Inline = { type: "text" | "code" | "bold"; text: string };

const FENCE_OPEN = /^\s*```(\w*)[^`]*$/;
const FENCE_CLOSE = /^\s*```\s*$/;
const UL = /^\s*[-*]\s+(.*)$/;
const OL = /^\s*\d+[.)]\s+(.*)$/;

export function parseBlocks(src: string): Block[] {
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const blocks: Block[] = [];
  let para: string[] = [];
  let i = 0;

  const flushPara = () => {
    if (para.length) blocks.push({ type: "p", text: para.join(" ") });
    para = [];
  };

  while (i < lines.length) {
    const line = lines[i];

    const fence = line.match(FENCE_OPEN);
    if (fence) {
      flushPara();
      const code: string[] = [];
      i++;
      while (i < lines.length && !FENCE_CLOSE.test(lines[i])) code.push(lines[i++]);
      i++; // skip the closing fence; if it is missing we simply reached the end of the answer
      blocks.push({ type: "code", lang: fence[1].toLowerCase(), code: code.join("\n") });
      continue;
    }

    const heading = line.match(/^#{1,6}\s+(.*)$/);
    if (heading) {
      flushPara();
      blocks.push({ type: "heading", text: heading[1].trim() });
      i++;
      continue;
    }

    const ordered = OL.test(line);
    if (ordered || UL.test(line)) {
      flushPara();
      const re = ordered ? OL : UL;
      const items: string[] = [];
      for (let m = lines[i]?.match(re); m; m = lines[i]?.match(re)) {
        items.push(m[1]);
        i++;
      }
      blocks.push({ type: ordered ? "ol" : "ul", items });
      continue;
    }

    if (line.trim() === "") flushPara();
    else para.push(line.trim());
    i++;
  }
  flushPara();
  return blocks;
}

export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  const re = /`([^`]+)`|\*\*([^*]+)\*\*/g;
  let last = 0;
  for (let m = re.exec(text); m; m = re.exec(text)) {
    if (m.index > last) out.push({ type: "text", text: text.slice(last, m.index) });
    out.push(m[1] !== undefined ? { type: "code", text: m[1] } : { type: "bold", text: m[2] });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ type: "text", text: text.slice(last) });
  return out;
}

/** Maps a code fence label to a supported language, or null. */
export function langFromFence(label: string): LangId | null {
  switch (label.toLowerCase()) {
    case "python":
    case "py":
      return "python";
    case "c":
      return "c";
    case "java":
      return "java";
    default:
      return null;
  }
}
