import assert from "node:assert/strict";
import { test } from "node:test";
import { emailProblem, nameProblem, passwordProblem } from "../src/lib/validation";

test("email: accepts ordinary addresses, rejects obvious mistakes", () => {
  for (const ok of ["a@b.co", " asha.rao+lab@example.com "]) assert.equal(emailProblem(ok), null, ok);
  for (const bad of ["", "   ", "plain", "a@b", "@b.com", "a b@c.com", "a@b@c.com", "x".repeat(250) + "@b.com"]) {
    assert.notEqual(emailProblem(bad), null, bad);
  }
});

test("password: length boundaries", () => {
  assert.match(passwordProblem("123456789")!, /at least 10/);
  assert.equal(passwordProblem("1234567890"), null);
  assert.equal(passwordProblem("x".repeat(128)), null);
  assert.match(passwordProblem("x".repeat(129))!, /at most 128/);
});

test("name: trimmed, 1 to 60 characters", () => {
  assert.notEqual(nameProblem("   "), null);
  assert.equal(nameProblem(" Asha "), null);
  assert.equal(nameProblem("x".repeat(60)), null);
  assert.notEqual(nameProblem("x".repeat(61)), null);
});
