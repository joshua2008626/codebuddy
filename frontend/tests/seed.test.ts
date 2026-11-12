import assert from "node:assert/strict";
import { test } from "node:test";
import { parseSeed } from "../src/lib/seed";

test("parseSeed accepts a well-formed seed", () => {
  const s = parseSeed({ name: "lesson_loops.py", language: "python", content: "print(1)\n", stdin: "x" });
  assert.deepEqual(s, { name: "lesson_loops.py", language: "python", content: "print(1)\n", stdin: "x" });
});

test("parseSeed rejects bad shapes, unknown languages, mismatched extensions and oversize code", () => {
  assert.equal(parseSeed(null), null);
  assert.equal(parseSeed("x"), null);
  assert.equal(parseSeed({ name: "a.py", language: "ruby", content: "" }), null);
  assert.equal(parseSeed({ name: "a.c", language: "python", content: "" }), null);
  assert.equal(parseSeed({ name: "a.py", language: "python", content: "x".repeat(64001) }), null);
  assert.equal(parseSeed({ name: 5, language: "python", content: "" }), null);
});

test("parseSeed drops a non-string stdin and trims oversize stdin", () => {
  assert.equal(parseSeed({ name: "a.py", language: "python", content: "", stdin: 3 })?.stdin, "");
  assert.equal(parseSeed({ name: "a.py", language: "python", content: "", stdin: "y".repeat(20000) })?.stdin.length, 16000);
});
