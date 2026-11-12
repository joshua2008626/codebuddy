import assert from "node:assert/strict";
import { test } from "node:test";
import { langFromFence, parseBlocks, parseInline } from "../src/lib/markdown";

test("fenced code keeps its language and exact contents", () => {
  const blocks = parseBlocks("Here:\n\n```python\nfor i in range(3):\n    print(i)\n```\n\nDone.");
  assert.deepEqual(blocks, [
    { type: "p", text: "Here:" },
    { type: "code", lang: "python", code: "for i in range(3):\n    print(i)" },
    { type: "p", text: "Done." },
  ]);
});

test("an unterminated fence runs to the end instead of losing the code", () => {
  const blocks = parseBlocks("```c\nint x = 1;\nint y = 2;");
  assert.deepEqual(blocks, [{ type: "code", lang: "c", code: "int x = 1;\nint y = 2;" }]);
});

test("markdown syntax inside a code block is not interpreted", () => {
  const [b] = parseBlocks("```\n# not a heading\n- not a list\n```");
  assert.deepEqual(b, { type: "code", lang: "", code: "# not a heading\n- not a list" });
});

test("headings, bullet lists and numbered lists", () => {
  const blocks = parseBlocks("## Steps\n1. Read n\n2) Add them\n\n- fast\n* simple");
  assert.deepEqual(blocks, [
    { type: "heading", text: "Steps" },
    { type: "ol", items: ["Read n", "Add them"] },
    { type: "ul", items: ["fast", "simple"] },
  ]);
});

test("consecutive lines join into one paragraph, blank lines split paragraphs", () => {
  assert.deepEqual(parseBlocks("one\ntwo\n\nthree"), [
    { type: "p", text: "one two" },
    { type: "p", text: "three" },
  ]);
});

test("inline code and bold", () => {
  assert.deepEqual(parseInline("Use `len(x)` for **length** here"), [
    { type: "text", text: "Use " },
    { type: "code", text: "len(x)" },
    { type: "text", text: " for " },
    { type: "bold", text: "length" },
    { type: "text", text: " here" },
  ]);
});

test("HTML in an answer stays plain text, so it can never run", () => {
  const html = '<img src=x onerror="alert(1)"><script>alert(2)</script>';
  assert.deepEqual(parseInline(html), [{ type: "text", text: html }]);
  assert.deepEqual(parseBlocks(html), [{ type: "p", text: html }]);
});

test("fence labels map to supported languages only", () => {
  assert.equal(langFromFence("Python"), "python");
  assert.equal(langFromFence("py"), "python");
  assert.equal(langFromFence("c"), "c");
  assert.equal(langFromFence("java"), "java");
  assert.equal(langFromFence("rust"), null);
  assert.equal(langFromFence(""), null);
});

test("empty input gives no blocks", () => {
  assert.deepEqual(parseBlocks(""), []);
  assert.deepEqual(parseBlocks("\n\n  \n"), []);
});
