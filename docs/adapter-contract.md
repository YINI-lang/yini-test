# Adapter Contract

An adapter is a small command-line program used by `yini-test-suite` to run a specific YINI parser implementation.

Its purpose is to let `yini-test-suite` test different parser implementations in a uniform way.

---

## Adapters

This repository itself does not include the adapters for all the specific parser implementations.

Instead, each parser project/repository should keep and maintain its own adapter, including:
- Its own adapter script (for `yini-test-suite`).
- Any parser-specific setup.
- Any parser-specific path or import handling.

So, in practice, for example:
- `yini-parser-typescript` contains its own TypeScript adapter.
- `yini-parser-python` contains its own Python adapter.
- And so on.

This means each project/repository owns its own adapter and is responsible for making it follow the rules defined in [docs/adapter-contract.md](./docs/adapter-contract.md).

Suggested locations for the adapter:
- `tools/yini-test-adapter.ts`
- `tools/yini_test_adapter.py`
- `scripts/yini_test_adapter.py`

---


## Required behavior

The adapter must:
1. Accept a path to a `.yini` input file.
2. Accept an optional parser mode: `lenient` or `strict`, lenient MUST be the default.
3. Write parsed JSON to standard output (`stdout`) on success.
4. Write error output to standard error (`stderr`) on failure.
5. Return exit code `0` on success.
6. Return a non-zero exit code if parsing fails, validation fails, arguments are invalid, or the adapter itself fails.

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
- On success, `stdout` must contain exactly one valid JSON document.
- On failure, `stdout` should be empty.
- The adapter should not print extra logging to `stdout`.
- Any debug, warning, or error text should go to `stderr`.

---

## Enforcement
This contract is enforced by `runner.py`.
