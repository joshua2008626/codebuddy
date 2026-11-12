import { useState } from "react";
import { Check, Copy, FilePlus } from "lucide-react";
import { langFromFence, parseBlocks, parseInline } from "../../lib/markdown";
import { LANGS, type LangId } from "../../lib/languages";

/** Everything is rendered as React text, so HTML inside an answer is shown literally and never executed. */
function Inline({ text }: { text: string }) {
  return (
    <>
      {parseInline(text).map((s, i) =>
        s.type === "code" ? (
          <code key={i} className="rounded bg-raised px-1 py-0.5 font-mono text-[0.85em]">{s.text}</code>
        ) : s.type === "bold" ? (
          <strong key={i}>{s.text}</strong>
        ) : (
          <span key={i}>{s.text}</span>
        ),
      )}
    </>
  );
}

function CodeBlock({ lang, code, fallback, onNewFile }: { lang: string; code: string; fallback: LangId; onNewFile: (code: string, lang: LangId) => void }) {
  const [copied, setCopied] = useState(false);
  const fileLang = langFromFence(lang) ?? fallback;

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked: the code is still selectable */
    }
  }

  const btn = "inline-flex items-center gap-1 rounded-chip px-1.5 py-0.5 text-[11px] text-muted hover:bg-raised hover:text-fg";
  return (
    <div className="my-2 overflow-hidden rounded-chip border border-line bg-ink/60">
      <div className="flex items-center justify-between border-b border-line px-2 py-1">
        <span className="font-mono text-[11px] text-muted">{langFromFence(lang) ? LANGS[fileLang].label : lang || "code"}</span>
        <span className="flex gap-1">
          <button type="button" className={btn} onClick={copy}>
            {copied ? <Check size={11} aria-hidden /> : <Copy size={11} aria-hidden />} {copied ? "Copied" : "Copy"}
          </button>
          <button type="button" className={btn} onClick={() => onNewFile(code, fileLang)} title="Put this code in a new file, leaving your current file untouched">
            <FilePlus size={11} aria-hidden /> New file
          </button>
        </span>
      </div>
      <pre className="overflow-x-auto p-2 font-mono text-xs leading-5"><code>{code}</code></pre>
    </div>
  );
}

export function RichAnswer({ text, fallbackLang, onNewFile }: { text: string; fallbackLang: LangId; onNewFile: (code: string, lang: LangId) => void }) {
  return (
    <div className="space-y-2 text-sm leading-relaxed">
      {parseBlocks(text).map((b, i) => {
        switch (b.type) {
          case "code":
            return <CodeBlock key={i} lang={b.lang} code={b.code} fallback={fallbackLang} onNewFile={onNewFile} />;
          case "heading":
            return <h4 key={i} className="pt-1 font-semibold"><Inline text={b.text} /></h4>;
          case "ul":
            return <ul key={i} className="list-disc space-y-1 pl-5">{b.items.map((t, j) => <li key={j}><Inline text={t} /></li>)}</ul>;
          case "ol":
            return <ol key={i} className="list-decimal space-y-1 pl-5">{b.items.map((t, j) => <li key={j}><Inline text={t} /></li>)}</ol>;
          default:
            return <p key={i}><Inline text={b.text} /></p>;
        }
      })}
    </div>
  );
}
