import type { SubmitResult, TestResult, TestStatus } from "../../lib/api";

const VERDICT_TEXT: Record<SubmitResult["verdict"], string> = {
  accepted: "Accepted",
  wrong_answer: "Wrong answer",
  compile_error: "Compilation failed",
  runtime_error: "Runtime error",
  time_limit: "Time limit exceeded",
};

const STATUS_TEXT: Record<TestStatus, string> = {
  passed: "Passed",
  failed: "Wrong answer",
  compile_error: "Compile error",
  runtime_error: "Runtime error",
  time_limit: "Time limit",
  skipped: "Not run",
};

function Detail({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <div className="text-[11px] text-muted">{label}</div>
      <pre className="mt-0.5 max-h-32 overflow-auto whitespace-pre-wrap break-words rounded bg-ink/60 p-1.5 font-mono text-xs">{text === "" ? "(nothing)" : text}</pre>
    </div>
  );
}

function Row({ r, sampleNo }: { r: TestResult; sampleNo: number | null }) {
  const ok = r.status === "passed";
  const name = r.hidden ? `Hidden test ${r.index + 1}` : `Sample ${sampleNo}`;
  return (
    <li className="px-3 py-2 text-sm">
      <div className="flex items-center justify-between gap-3">
        <span>{name}</span>
        <span className="flex items-center gap-3 text-xs">
          {r.time_seconds !== null && <span className="text-muted">{r.time_seconds} s</span>}
          <span className={ok ? "text-ok" : r.status === "skipped" ? "text-muted" : "text-danger"}>{STATUS_TEXT[r.status]}</span>
        </span>
      </div>
      {/* Only sample tests carry details; the server never sends input or output for hidden ones. */}
      {!r.hidden && !ok && r.status !== "skipped" && (
        <div className="mt-2 grid gap-2 sm:grid-cols-3">
          {r.input !== null && <Detail label="Input" text={r.input} />}
          {r.expected !== null && <Detail label="Expected" text={r.expected} />}
          {r.actual !== null && <Detail label="Your output" text={r.actual} />}
          {r.stderr && <div className="sm:col-span-3"><Detail label="Errors" text={r.stderr} /></div>}
        </div>
      )}
    </li>
  );
}

export function SubmissionResult({ result }: { result: SubmitResult }) {
  const ok = result.verdict === "accepted";
  let sampleNo = 0;
  return (
    <section aria-label="Submission result" aria-live="polite" className="panel overflow-hidden">
      <div className={`flex flex-wrap items-center justify-between gap-2 px-4 py-3 ${ok ? "bg-ok/10" : "bg-danger/10"}`}>
        <h3 className={`font-semibold ${ok ? "text-ok" : "text-danger"}`}>{VERDICT_TEXT[result.verdict]}</h3>
        <span className="text-sm">{result.passed} of {result.total} tests passed</span>
      </div>

      {result.verdict === "compile_error" && result.compile_output && (
        <pre className="max-h-48 overflow-auto whitespace-pre-wrap border-b border-line p-3 font-mono text-xs text-danger">{result.compile_output}</pre>
      )}

      {!ok && result.first_failure !== null && result.results[result.first_failure]?.hidden && (
        <p className="border-b border-line px-4 py-2 text-xs text-muted">
          Your code failed a hidden test. Hidden tests don’t show their input, so check edge cases: the smallest and largest values, negatives, and repeated values.
        </p>
      )}

      <ul className="divide-y divide-line">
        {result.results.map((r) => <Row key={r.index} r={r} sampleNo={r.hidden ? null : ++sampleNo} />)}
      </ul>
    </section>
  );
}
