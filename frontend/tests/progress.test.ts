import assert from "node:assert/strict";
import { test } from "node:test";
import { parseProgress, recordSubmission, summarize, type ProgressMap } from "../src/lib/progress";

const T = new Date("2026-11-11T10:00:00Z");

test("a wrong attempt counts the attempt and the best score, but is not solved", () => {
  const m = recordSubmission({}, "a", "wrong_answer", 3, 6, T);
  assert.deepEqual(m.a, { solved: false, attempts: 1, bestPassed: 3, total: 6, lastVerdict: "wrong_answer", solvedAt: null });
});

test("an accepted attempt marks it solved and stamps the date", () => {
  const m = recordSubmission({}, "a", "accepted", 6, 6, T);
  assert.equal(m.a.solved, true);
  assert.equal(m.a.solvedAt, T.toISOString());
});

test("solving is never undone, and the first solve date is kept", () => {
  let m: ProgressMap = recordSubmission({}, "a", "accepted", 6, 6, T);
  m = recordSubmission(m, "a", "wrong_answer", 1, 6, new Date("2026-12-01T00:00:00Z"));
  assert.equal(m.a.solved, true);
  assert.equal(m.a.solvedAt, T.toISOString());
  assert.equal(m.a.attempts, 2);
  assert.equal(m.a.lastVerdict, "wrong_answer");
  assert.equal(m.a.bestPassed, 6); // best is kept
});

test("recording does not change the input map or other challenges", () => {
  const before: ProgressMap = recordSubmission({}, "a", "accepted", 6, 6, T);
  const snapshot = JSON.stringify(before);
  const after = recordSubmission(before, "b", "compile_error", 0, 4, T);
  assert.equal(JSON.stringify(before), snapshot);
  assert.deepEqual(after.a, before.a);
  assert.equal(after.b.attempts, 1);
});

test("summary counts solved challenges overall and per difficulty", () => {
  const list = [
    { id: "a", difficulty: "beginner" },
    { id: "b", difficulty: "beginner" },
    { id: "c", difficulty: "advanced" },
  ];
  let m: ProgressMap = recordSubmission({}, "a", "accepted", 2, 2, T);
  m = recordSubmission(m, "c", "time_limit", 1, 5, T);
  assert.deepEqual(summarize(m, list), {
    solved: 1,
    total: 3,
    byDifficulty: { beginner: { solved: 1, total: 2 }, advanced: { solved: 0, total: 1 } },
  });
});

test("progress for a challenge that no longer exists is ignored by the summary", () => {
  const m = recordSubmission({}, "gone", "accepted", 1, 1, T);
  assert.equal(summarize(m, [{ id: "a", difficulty: "beginner" }]).solved, 0);
});

test("corrupted storage never throws and drops only the bad entries", () => {
  assert.deepEqual(parseProgress(null), {});
  assert.deepEqual(parseProgress("not json"), {});
  assert.deepEqual(parseProgress("[1,2]"), {});
  assert.deepEqual(parseProgress("null"), {});
  const good = recordSubmission({}, "ok", "accepted", 1, 1, T);
  const mixed = JSON.stringify({ ...good, bad: { solved: "yes" }, worse: 7 });
  assert.deepEqual(parseProgress(mixed), good);
});

test("round trip through JSON keeps everything", () => {
  const m = recordSubmission(recordSubmission({}, "a", "wrong_answer", 2, 6, T), "a", "accepted", 6, 6, T);
  assert.deepEqual(parseProgress(JSON.stringify(m)), m);
});
