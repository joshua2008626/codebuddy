import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { highlightLine } from "../lib/highlight";

/* ---------- Sample content for the hero preview (clearly pre-written, see caption below) ---------- */
const CODE = `def average(nums):
    total = 0
    for n in nums:
        total += n
    return total / len(nums)

print(average([4, 8, 15, 16]))`;

/** Notes are keyed by line index. Blank lines have none. */
const NOTES: Record<number, string> = {
  0: "def starts a function. average is its name, and nums is the list it receives.",
  1: "total is a running sum. It starts at 0 before anything is added.",
  2: "The loop visits each number in nums, one at a time, and calls it n.",
  3: "Each pass adds n to total. When the loop ends, total holds the sum of the list.",
  4: "Divides the sum by how many numbers there are. That is the average. It fails on an empty list, because len(nums) would be 0.",
  6: "Calls average with a four-number list and prints the result.",
};

const START_LINE = 4; // the most interesting note, shown automatically after typing

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}

/** The one memorable moment: code types itself, then Buddy annotates the line you select. */
function HeroEditor() {
  const reduced = usePrefersReducedMotion();
  const [shown, setShown] = useState(0);
  const [active, setActive] = useState<number | null>(null);
  const done = shown >= CODE.length;

  // Typing animation. Skipped entirely for reduced-motion users.
  useEffect(() => {
    if (reduced) {
      setShown(CODE.length);
      return;
    }
    const id = window.setInterval(() => setShown((s) => Math.min(s + 2, CODE.length)), 22);
    return () => window.clearInterval(id);
  }, [reduced]);

  // Once typing finishes, select the line with the most useful note.
  useEffect(() => {
    if (done) setActive((a) => (a === null ? START_LINE : a));
  }, [done]);

  const lines = useMemo(() => CODE.slice(0, shown).split("\n"), [shown]);
  const note = active !== null ? NOTES[active] : undefined;

  return (
    <figure className="panel overflow-hidden shadow-[0_30px_80px_-30px_rgb(var(--c-blue)/0.35)]">
      <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
        <div className="flex items-center gap-2 font-mono text-xs text-muted">
          <span className="h-2.5 w-2.5 rounded-full bg-line" aria-hidden />
          <span className="h-2.5 w-2.5 rounded-full bg-line" aria-hidden />
          <span className="h-2.5 w-2.5 rounded-full bg-line" aria-hidden />
          <span className="ml-2">average.py</span>
        </div>
        <span className="rounded-chip bg-raised px-2 py-0.5 text-xs text-muted">Python</span>
      </div>

      <div className="py-3 font-mono text-[13px] leading-6" role="group" aria-label="Sample code. Select a line to see Buddy's note.">
        {lines.map((line, i) => {
          const hasNote = NOTES[i] !== undefined;
          const isActive = active === i;
          const typing = !done && i === lines.length - 1;
          return (
            <button
              key={i}
              type="button"
              disabled={!done || !hasNote}
              onClick={() => setActive(i)}
              aria-pressed={isActive}
              className={`flex w-full cursor-pointer items-start gap-4 px-4 text-left transition-colors disabled:cursor-default ${
                isActive ? "bg-violet/15" : hasNote && done ? "hover:bg-raised" : ""
              }`}
            >
              <span className="w-4 select-none text-right text-muted/60">{i + 1}</span>
              <span className="whitespace-pre">
                {highlightLine(line, "python")}
                {typing && <span className="ml-px inline-block h-4 w-[2px] translate-y-0.5 animate-pulse bg-cyan" aria-hidden />}
              </span>
            </button>
          );
        })}
      </div>

      <div className="min-h-[104px] border-t border-line bg-raised/50 px-4 py-3" aria-live="polite">
        <div className="flex items-center gap-2 text-xs font-medium text-cyan">
          <Sparkles size={14} aria-hidden /> Buddy AI
        </div>
        <p className="mt-1.5 text-sm leading-relaxed text-fg/90">
          {note ?? (done ? "Select a line to see what it does." : "Writing code…")}
        </p>
      </div>
      <figcaption className="border-t border-line px-4 py-2 text-xs text-muted">
        Preview with sample notes. In the workspace, answers come from the live Buddy AI.
      </figcaption>
    </figure>
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Ambient light: two soft glows, kept low so text contrast stays high. */}
      <div aria-hidden className="pointer-events-none absolute -left-40 -top-40 h-[480px] w-[480px] rounded-full bg-volt/20 blur-[120px]" />
      <div aria-hidden className="pointer-events-none absolute -right-32 top-20 h-[420px] w-[420px] rounded-full bg-violet/15 blur-[120px]" />

      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-5 pb-20 pt-16 lg:grid-cols-[1fr_1.05fr] lg:pt-24">
        <div>
          {/* Brightness steps up line by line: thinking, writing, understanding. */}
          <h1 className="text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            <span className="block text-fg/40">Think Code.</span>
            <span className="block text-fg/70">Write Code.</span>
            <span className="block text-fg">Understand Code.</span>
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-muted">
            A workspace for C, Python and Java where your code runs for real and Buddy AI explains every line you point at.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/workspace" className="btn-primary !px-5 !py-3">Start Coding</Link>
            <a href="#features" className="btn-ghost !px-5 !py-3">Explore Features</a>
          </div>
          <ul className="mt-8 flex flex-wrap gap-2 font-mono text-xs text-muted" aria-label="Supported languages">
            {["C", "Python", "Java"].map((l) => (
              <li key={l} className="rounded-chip border border-line bg-panel px-2.5 py-1">{l}</li>
            ))}
          </ul>
        </div>

        <HeroEditor />
      </div>
    </section>
  );
}
