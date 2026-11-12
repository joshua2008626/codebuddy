import type { ReactNode } from "react";

/**
 * Tiny single-line highlighter used only for the static code previews on the landing page.
 * The workspace uses Monaco, which has a real tokenizer.
 */
export type Lang = "python" | "c" | "java";

const KEYWORDS: Record<Lang, string[]> = {
  python: ["def", "return", "for", "in", "if", "elif", "else", "while", "import", "from", "class", "print", "True", "False", "None", "and", "or", "not"],
  c: ["int", "char", "float", "double", "void", "return", "for", "while", "if", "else", "struct", "include", "const", "sizeof"],
  java: ["public", "private", "static", "void", "class", "int", "double", "String", "return", "for", "while", "if", "else", "new", "import"],
};

function buildPattern(lang: Lang): RegExp {
  const comment = lang === "python" ? "#.*$" : "\\/\\/.*$";
  // Groups: 1 comment, 2 string, 3 number, 4 identifier
  return new RegExp(`(${comment})|("(?:[^"\\\\]|\\\\.)*"|'(?:[^'\\\\]|\\\\.)*')|(\\b\\d+(?:\\.\\d+)?\\b)|([A-Za-z_]\\w*)`, "g");
}

export function highlightLine(line: string, lang: Lang): ReactNode[] {
  const kw = new Set(KEYWORDS[lang]);
  const re = buildPattern(lang);
  const out: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;

  while ((m = re.exec(line)) !== null) {
    if (m.index > last) out.push(line.slice(last, m.index));
    const [text, comment, str, num, ident] = m;
    const key = `${m.index}-${text}`;

    if (comment) out.push(<span key={key} className="tok-com">{text}</span>);
    else if (str) out.push(<span key={key} className="tok-str">{text}</span>);
    else if (num) out.push(<span key={key} className="tok-num">{text}</span>);
    else if (ident && kw.has(ident)) out.push(<span key={key} className="tok-kw">{text}</span>);
    else if (ident && line[m.index + text.length] === "(") out.push(<span key={key} className="tok-fn">{text}</span>);
    else out.push(text);

    last = m.index + text.length;
    if (text.length === 0) re.lastIndex++; // guard against zero-length matches
  }
  if (last < line.length) out.push(line.slice(last));
  return out;
}
