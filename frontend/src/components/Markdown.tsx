import { parseBlocks, parseInline } from "../lib/markdown";

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

/** Renders trusted-or-untrusted Markdown as React text nodes only (never HTML). */
export function Markdown({ source }: { source: string }) {
  return (
    <div className="space-y-3 leading-relaxed">
      {parseBlocks(source).map((b, i) => {
        switch (b.type) {
          case "heading": return <h3 key={i} className="font-semibold"><Inline text={b.text} /></h3>;
          case "p": return <p key={i}><Inline text={b.text} /></p>;
          case "ul": return <ul key={i} className="list-disc space-y-1 pl-5">{b.items.map((t, j) => <li key={j}><Inline text={t} /></li>)}</ul>;
          case "ol": return <ol key={i} className="list-decimal space-y-1 pl-5">{b.items.map((t, j) => <li key={j}><Inline text={t} /></li>)}</ol>;
          case "code": return <pre key={i} className="overflow-x-auto rounded-chip border border-line bg-ink/60 p-3 font-mono text-xs"><code>{b.code}</code></pre>;
        }
      })}
    </div>
  );
}
