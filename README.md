# yini-test

The **yini-test** tool is the shared case corpus (test harness) for YINI parser implementations.

It does not contain a YINI parser itself. Instead, it invokes a chosen parser implementation through an adapter, compares the actual output with the expected output, and reports pass/fail results consistently.

The goal of `yini-test` is to stay implementation-agnostic, so that multiple YINI parsers can be tested in a uniform way.

## What `yini-test` does

- Runs a chosen parser implementation through an adapter.
- Compares actual output with expected output.
- Reports pass/fail results consistently.
- Provides a shared test corpus for multiple YINI parser implementations.

---

## What `yini-test` does not do

- It does not contain a YINI parser.
- It does not contain parser-specific execution logic.
- It does not own parser-specific adapters.

---

## Project structure

- `__main__.py` is the package entry point.
- `cli.py` handles command-line argument parsing.
- `runner.py` contains the core test-running logic.
- `cases/` contains the shared case corpus.
- `tests/` contains tests for the `yini-test` project itself.

Current case groups include:
- `golden/` for cases where valid input must produce exact expected output.
- `smoke/` for smaller practical cases used to catch obvious parser issues.

---

## Adapters

This project itself does not include adapters for specific parser implementations.

Instead, each parser project/repository should keep and maintain its own adapter, including:
- Its own adapter script (for `yini-test`).
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

## Running `yini-test`

`yini-test` accepts an adapter command, for example:

Example with the TypeScript parser adapter:
```bash
yini-test smoke --adapter node ../yini-parser-typescript/dist/tools/yini-test-adapter.js --input {input} --mode {mode}
```

Example with the Python parser adapter:
```bash
yini-test smoke --adapter python ../yini-parser-python/tools/yini_test_adapter.py --input {input} --mode {mode}
```

---

## Related documents
- [docs/adapter-contract.md](./docs/adapter-contract.md)
- [docs/case-contract.md](./docs/case-contract.md)
