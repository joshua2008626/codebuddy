import { useId, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { highlightLine, type Lang } from "../lib/highlight";

/** Small read-only code block for the demo pane. */
function Code({ code, lang }: { code: string; lang: Lang }) {
  return (
    <pre className="overflow-x-auto rounded-chip border border-line bg-ink/60 p-3 font-mono text-[13px] leading-6">
      {code.split("\n").map((l, i) => {
        const parts = highlightLine(l, lang);
        // An empty array is truthy, so check length explicitly to keep blank lines from collapsing.
        return <div key={i}>{parts.length > 0 ? parts : " "}</div>;
      })}
    </pre>
  );
}

function Caption({ children }: { children: ReactNode }) {
  return <p className="mt-3 text-xs text-muted">{children}</p>;
}

type Feature = { id: string; title: string; summary: string; demo: ReactNode };

const FEATURES: Feature[] = [
  {
    id: "run",
    title: "Run C, Python and Java",
    summary: "Press run and your program executes in a sandbox. You get stdout, compiler errors, runtime errors, time and memory.",
    demo: (
      <>
        <Code lang="python" code={'name = input()\nprint("Hello,", name)'} />
        <div className="mt-3 rounded-chip border border-line bg-ink/60 p-3 font-mono text-[13px]">
          <div className="text-muted">stdin: <span className="text-fg">Asha</span></div>
          <div className="mt-2 text-fg">Hello, Asha</div>
        </div>
        <Caption>Layout illustration. In the workspace this panel shows the real status, time and memory returned by the execution service.</Caption>
      </>
    ),
  },
  {
    id: "explain",
    title: "Explain any selection",
    summary: "Highlight code and ask. Buddy AI answers about exactly what you selected, in the language you are writing.",
    demo: (
      <>
        <Code lang="c" code={"for (int i = 0; i < n; i++) {\n    sum += arr[i];\n}"} />
        <div className="mt-3 rounded-chip border border-violet/30 bg-violet/10 p-3 text-sm leading-relaxed">
          This loop starts at index 0 and moves through the array until i reaches n. Each pass adds the current element to sum.
        </div>
        <Caption>Sample explanation written for this page.</Caption>
      </>
    ),
  },
  {
    id: "debug",
    title: "Debug with context",
    summary: "Buddy AI reads your code and the error together, then points at the cause and suggests a fix you can apply.",
    demo: (
      <>
        <Code lang="python" code={"scores = [90, 82, 77]\nprint(scores[3])"} />
        <div className="mt-3 rounded-chip border border-danger/40 bg-danger/10 p-3 font-mono text-[13px] text-danger">
          IndexError: list index out of range
        </div>
        <div className="mt-3 rounded-chip border border-violet/30 bg-violet/10 p-3 text-sm leading-relaxed">
          The list has three items, so valid indexes are 0, 1 and 2. Use scores[2] for the last one, or scores[-1].
        </div>
        <Caption>Sample session written for this page.</Caption>
      </>
    ),
  },
  {
    id: "convert",
    title: "Convert between languages",
    summary: "Move a solution from Python to Java or C and compare the two versions side by side.",
    demo: (
      <>
        <div className="grid gap-3 sm:grid-cols-2">
          <Code lang="python" code={"total = 0\nfor n in nums:\n    total += n"} />
          <Code lang="java" code={"int total = 0;\nfor (int n : nums) {\n    total += n;\n}"} />
        </div>
        <Caption>Sample conversion written for this page.</Caption>
      </>
    ),
  },
  {
    id: "practice",
    title: "Practice with real tests",
    summary: "Challenges come in beginner, intermediate and advanced levels. Every submission runs against test cases.",
    demo: (
      <>
        <div className="rounded-chip border border-line bg-ink/60 p-3 text-sm">
          <div className="font-medium">Sum of two numbers</div>
          <p className="mt-1 text-muted">Read two integers and print their sum.</p>
        </div>
        <ul className="mt-3 space-y-2 text-sm">
          {["Test 1", "Test 2", "Test 3"].map((t) => (
            <li key={t} className="flex items-center justify-between rounded-chip border border-line px-3 py-2">
              <span>{t}</span>
              <span className="text-muted">Not run</span>
            </li>
          ))}
        </ul>
        <Caption>Results appear only after a real run. Nothing is pre-filled.</Caption>
      </>
    ),
  },
];

export function Features() {
  const [index, setIndex] = useState(0);
  const panelId = useId();
  const current = FEATURES[index];

  return (
    <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-5 py-20">
      <h2 className="max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">Everything between a blank file and a working program</h2>

      <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_1.1fr]">
        <div role="tablist" aria-label="Features" aria-orientation="vertical" className="flex flex-col gap-2">
          {FEATURES.map((f, i) => {
            const selected = i === index;
            return (
              <button
                key={f.id}
                role="tab"
                type="button"
                id={`${panelId}-tab-${f.id}`}
                aria-selected={selected}
                aria-controls={`${panelId}-panel`}
                tabIndex={selected ? 0 : -1}
                onClick={() => setIndex(i)}
                onKeyDown={(e) => {
                  // Arrow-key navigation, per the ARIA tabs pattern.
                  if (e.key === "ArrowDown") setIndex((index + 1) % FEATURES.length);
                  if (e.key === "ArrowUp") setIndex((index - 1 + FEATURES.length) % FEATURES.length);
                }}
                className={`rounded-panel border px-4 py-3.5 text-left transition-colors ${
                  selected ? "border-volt/60 bg-panel" : "border-transparent hover:bg-panel/60"
                }`}
              >
                <span className={`block font-medium ${selected ? "text-fg" : "text-fg/80"}`}>{f.title}</span>
                {selected && <span className="mt-1 block text-sm leading-relaxed text-muted">{f.summary}</span>}
              </button>
            );
          })}
        </div>

        <div id={`${panelId}-panel`} role="tabpanel" aria-labelledby={`${panelId}-tab-${current.id}`} className="panel min-h-[320px] p-5">
          <AnimatePresence mode="wait">
            <motion.div
              key={current.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              {current.demo}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
