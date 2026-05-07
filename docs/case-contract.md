# Case Contract

This document defines how test cases are organized in `yini-test`.

Its purpose is to make YINI test cases:
- Easy to discover.
- Easy to validate.
- Consistent across parser implementations.
- Predictable for both humans and tooling.

## Purpose

A test case in `yini-test` is a small input/output contract.

Each case tells `yini-test`:
- What YINI input to run.
- In which parser mode it should be run.
- Whether parsing is expected to succeed or fail.
- What output is expected on success.

---

## Directory structure

Test cases are stored under the top-level `cases/` directory.

Example structure:
```text id="wawh7b"
cases/
  golden/
    lenient/
      valid/
      invalid/
    strict/
      valid/
      invalid/
  smoke/
    lenient/
      valid/
      invalid/
    strict/
      valid/
      invalid/
  edge/
```

---

## Case categories

### Smoke
Smoke cases are small, practical tests used as a quick confidence check. They should run fast and cover common real-world usage.

### Golden
Golden cases are tests with fixed expected output. They verify that a parser produces the correct result for known input.

### Edge
Edge cases focus on unusual, subtle, or boundary behavior, such as empty values, duplicate keys, repeated sections, string escapes, numeric corner cases, and nesting limits.

---

## Parser mode

The directory path defines the parser mode:

- `lenient/` means the case must be run in lenient mode.
- `strict/` means the case must be run in strict mode.

The runner MUST NOT guess the mode from file contents.

---

## Valid and invalid cases

The directory path also defines whether parsing is expected to succeed or fail:

- `valid/` means parsing is expected to succeed.
- `invalid/` means parsing is expected to fail.

---

## Valid case format

A valid case must contain:
- One `.yini` input file.
- One matching `.json` expected-output file.

Example:

```text
cases/smoke/lenient/valid/basic-config.yini
cases/smoke/lenient/valid/basic-config.json
```

```text
cases/smoke/strict/valid/basic-config.strict.yini
cases/smoke/strict/valid/basic-config.strict.json
```

Both files must have the same base name.

For a successful valid case:

- The adapter must succeed.
- The adapter must return exit code `0`.
- The adapter must print valid JSON to `stdout`.
- The actual JSON output must match the expected `.json` file.

---

## Invalid case format

An invalid case must contain one `.yini` input file.

Example:

```
cases/smoke/strict/invalid/duplicate-top-section.yini
```

For an invalid case:
- The adapter must fail.
- The adapter must return a non-zero exit code.
- The adapter should print a readable error message to `stderr`.

At the first stage, `yini-test` does not require an expected error file for invalid cases. It is enough that the adapter fails correctly.

---

## File naming

Case file names should be descriptive and should preferably use lowercase letters, digits, and hyphens. Related files should keep the same base name.

YINI input files that are expected to be parsed in strict mode MAY end with `.strict.yini`. However, the filename alone never decides in which mode the parser operates, parser mode is dispatched when running the parser.

---

## JSON expectations

Expected `.json` files must contain valid, machine-readable JSON and represent the canonical expected parsed output for the case.

For valid cases, `yini-test` compares the parsed JSON values, not raw text formatting. Differences in whitespace or indentation do not matter; the data structure itself must match.

Expected `.json` SHOULD still be pretty-formatted (using 4-space indentation) so it's nicer for humans to read during debugging and development.

---

## One case, one purpose

Each case should ideally test one main behavior. This makes failures easier to understand, debug, and maintain.
