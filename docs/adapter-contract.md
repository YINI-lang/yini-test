# Adapter Contract

An adapter is a small command-line program used by `yini-test` to run a specific YINI parser implementation.

Its purpose is to let `yini-test` test different parser implementations in a uniform way.

## Required behavior

The adapter must:
1. Accept a path to a `.yini` input file.
2. Accept an optional parser mode: `lenient` or `strict`, lenient MUST be the default.
3. Write parsed JSON to standard output (`stdout`) on success.
4. Write error output to standard error (`stderr`) on failure.
5. Return exit code `0` on success.
6. Return a non-zero exit code on failure.

---

## Command-line interface

The adapter should support this interface:

```bash
adapter --input <path-to-yini-file> [--mode <lenient|strict>]
```

---

## Success output

On success, the adapter must print exactly one valid JSON document to `stdout`.

Example:
```json
{
  "App": {
    "name": "Demo App"
  }
}
```

---

## Failure output

On failure, the adapter should print a readable error message to `stderr` and exit with a non-zero exit code.

Example:
```
Parse error at line 3, column 8: duplicate key "name"
```

Requirements:
- The JSON output must be valid and machine-readable.
- The adapter should not print extra logging to `stdout`.
- Any debug, warning, or error text should go to `stderr`.

---

## Enforcement
This contract is enforced by `runner.py`.
