import assert from "node:assert/strict";
import { test } from "node:test";
import { formatCode, formatDate } from "../src/lib/format";

test("C: re-indents by brace depth", () => {
  const input = "int main(){\nprintf(\"hi\");\nif(x){\ny();\n}\nreturn 0;\n}";
  const expected = "int main(){\n    printf(\"hi\");\n    if(x){\n        y();\n    }\n    return 0;\n}\n";
  assert.equal(formatCode(input, "c"), expected);
});

test("C: braces inside strings, chars and comments are ignored", () => {
  const input = 'int main() {\nprintf("{");\nchar c = \'}\';\n// }\nreturn 0;\n}';
  const expected = 'int main() {\n    printf("{");\n    char c = \'}\';\n    // }\n    return 0;\n}\n';
  assert.equal(formatCode(input, "c"), expected);
});

test("C: preprocessor lines stay at column 0", () => {
  assert.equal(formatCode("   #include <stdio.h>\nint main(){\nreturn 0;\n}", "c"),
    "#include <stdio.h>\nint main(){\n    return 0;\n}\n");
});

test("Java: else-branch closer lines up with the if", () => {
  const input = "public class Main {\npublic static void main(String[] a) {\nif (a.length > 0) {\nf();\n} else {\ng();\n}\n}\n}";
  const expected =
    "public class Main {\n    public static void main(String[] a) {\n        if (a.length > 0) {\n            f();\n        } else {\n            g();\n        }\n    }\n}\n";
  assert.equal(formatCode(input, "java"), expected);
});

test("Java: block comment continuation lines are aligned, not corrupted", () => {
  const input = "class A {\n/**\n* doc\n*/\nvoid f() {}\n}";
  const expected = "class A {\n    /**\n     * doc\n     */\n    void f() {}\n}\n";
  assert.equal(formatCode(input, "java"), expected);
});

test("Python: indentation is preserved, whitespace is tidied", () => {
  const input = "def f():\n\treturn 1   \n\n\n\n\nprint(f())";
  assert.equal(formatCode(input, "python"), "def f():\n    return 1\n\n\nprint(f())\n");
});

test("empty input stays empty", () => {
  assert.equal(formatCode("  \n\n", "c"), "");
});

test("formatting is idempotent", () => {
  const src = "int main(){\nif(1){\nx();\n}\n}";
  const once = formatCode(src, "c");
  assert.equal(formatCode(once, "c"), once);
});

test("CRLF line endings are normalised", () => {
  assert.equal(formatCode("x = 1\r\ny = 2\r\n", "python"), "x = 1\ny = 2\n");
});

test("formatDate: naive server timestamps are read as UTC, bad input gives empty text", () => {
  assert.equal(formatDate("2026-11-12T12:00:00"), formatDate("2026-11-12T12:00:00Z"));
  assert.match(formatDate("2026-11-12T12:00:00Z"), /12 Nov 2026/);
  assert.equal(formatDate("not a date"), "");
});
