/**
 * Product-scope facts, not usage metrics. CodeBuddy has no real users yet, so no audience numbers are shown.
 * Keep these in sync with what is actually built.
 */
const FACTS = [
  { value: "3", label: "languages: C, Python, Java" },
  { value: "8", label: "Buddy AI modes, from explain to complexity" },
  { value: "3", label: "challenge levels: beginner to advanced" },
  { value: "12", label: "learning topics, each with exercises" },
];

export function DemoStats() {
  return (
    <section className="border-y border-line bg-panel/40">
      <div className="mx-auto max-w-6xl px-5 py-12">
        <dl className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {FACTS.map((f) => (
            <div key={f.label}>
              <dt className="sr-only">{f.label}</dt>
              <dd className="text-4xl font-semibold tracking-tight">{f.value}</dd>
              <p className="mt-1 text-sm text-muted" aria-hidden>{f.label}</p>
            </div>
          ))}
        </dl>
        <p className="mt-8 text-xs text-muted">These describe what CodeBuddy includes. They are not user statistics.</p>
      </div>
    </section>
  );
}
