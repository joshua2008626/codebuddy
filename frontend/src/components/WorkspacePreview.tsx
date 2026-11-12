import { highlightLine } from "../lib/highlight";

const SAMPLE = `#include <stdio.h>

int main(void) {
    int n;
    scanf("%d", &n);
    printf("%d\\n", n * 2);
    return 0;
}`;

/** Static picture of the four-region workspace layout. The real, working workspace arrives in phase 2. */
export function WorkspacePreview() {
  return (
    <section className="mx-auto max-w-6xl px-5 pb-20">
      <h2 className="max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">One screen for writing, running and asking</h2>
      <p className="mt-3 max-w-lg text-muted">Files on the left, code in the middle, Buddy AI on the right, and your output underneath.</p>

      <div className="panel mt-8 overflow-hidden" role="img" aria-label="Layout preview of the CodeBuddy workspace: file explorer, code editor, Buddy AI panel and output panel">
        <div className="grid min-h-[360px] grid-cols-1 md:grid-cols-[180px_1fr_240px]">
          <aside className="hidden border-r border-line p-3 text-sm md:block">
            <div className="mb-2 text-xs font-medium text-muted">Files</div>
            <div className="rounded-chip bg-raised px-2 py-1 font-mono text-xs">double.c</div>
            <div className="mt-1 px-2 py-1 font-mono text-xs text-muted">notes.txt</div>
          </aside>

          <div className="flex flex-col">
            <div className="flex-1 p-4 font-mono text-[13px] leading-6">
              {SAMPLE.split("\n").map((l, i) => (
                <div key={i} className="flex gap-4">
                  <span className="w-4 select-none text-right text-muted/60">{i + 1}</span>
                  <span className="whitespace-pre">{highlightLine(l, "c")}</span>
                </div>
              ))}
            </div>
            <div className="border-t border-line bg-raised/40 p-3 font-mono text-xs text-muted">Output appears here after you press Run.</div>
          </div>

          <aside className="border-t border-line p-3 text-sm md:border-l md:border-t-0">
            <div className="mb-2 text-xs font-medium text-cyan">Buddy AI</div>
            <p className="text-muted">Select code, then ask for an explanation, a fix, or a simpler version.</p>
          </aside>
        </div>
      </div>
    </section>
  );
}
