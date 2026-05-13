# yini-test

The **yini-test** tool is the shared case corpus (test harness) for YINI parser implementations.

It does not contain a YINI parser itself. Instead, it invokes a chosen parser implementation through an adapter, compares the actual output with the expected output, and reports pass/fail results consistently.

The goal of `yini-test` is to stay implementation-agnostic, so that multiple YINI parsers can be tested in a uniform way.

---

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

## Quick Start

### First-time setup

It is assumed you are in the `yini-test/` directory, and that you have the directory `yini-parser-python/` already alongside the directory `yini-test`.

Run:
```bash
task clean
task install
task test
task run-smoke-python
```

If you want to test the TypeScript parser instead, replace the last command with:
```bash
task run-smoke-typescript
```

### Later runs

Run these commands from the `yini-test/` directory.

Run:
```bash
task run-smoke-python
```

or:

```bash
task run-smoke-typescript
```

depending on which parser implementation you want to test.

---

## Expected local repository layout

The predefined Taskfile commands assume that the parser repositories are located next to `yini-test`:

```text
/
├─ yini-test/
├─ yini-parser-typescript/
└─ yini-parser-python/
```

Adapter paths are **relative to** this directory: `yini-test/`:
- The TypeScript parser adapter is expected at:  
  `../yini-parser-typescript/tools/yini-test-adapter.ts`
- The Python parser adapter is expected at:  
  `../yini-parser-python/tools/yini_parser_adapter.py`

## Installing and running tests

### 1. Clean local cache files

```bash
task clean
```

This removes Python cache files and temporary tool caches.

### 2. Install dependencies

```bash
task install
```

This installs the development dependencies and installs `yini-test` itself **in editable mode**.

### 3. Show available tasks

```bash
task
```

### 4. Test `yini-test` itself

```bash
task test
```

This runs the unit and integration tests for the `yini-test` runner.

A successful result should look similar to:
```txt
15 passed
```

### 5. Run smoke tests against `yini-parser-python`

```bash
task run-smoke-python
```

This runs the smoke test cases against the Python parser adapter.

The task uses a command similar to:
```bash
python -m yini_test smoke \
  --cases-root cases \
  --adapter python ../yini-parser-python/tools/yini_parser_adapter.py --input {input} --mode {mode}
```

The `{input}` and `{mode}` placeholders are replaced automatically for each test case.

### 6. Understanding the result

Each case is reported as `PASS` or `FAIL`.

Example:
```txt
PASS  "cases\smoke\lenient\valid\1-minimal.yini"
FAIL  "cases\smoke\lenient\valid\3-nested-sections.yini"
```

For valid cases, `yini-test` compares the parser output with the matching expected JSON file.

For example:
```txt
cases/smoke/lenient/valid/3-nested-sections.yini
```

is compared with:
```txt
cases/smoke/lenient/valid/3-nested-sections.json
```

If a test case fails, `yini-test` prints the difference showing the expected output and the actual parser output.

---

## Project structure

- `src/yini_test/__main__.py` is the package entry point.
- `src/yini_test/cli.py` handles the command-line argument parsing.
- `src/yini_test/runner.py` contains the core test-running logic.
- `cases/` contains the shared (parser test) case corpus.
- `tests/` contains tests for this `yini-test` project itself.

Current case groups include:
- `golden/` for cases where valid input must produce exact expected output.
- `smoke/` for smaller practical cases used to catch obvious parser issues.

---

## Adapters

This project itself does not include adapters for specific parser implementations.

Instead, each parser project/repository should provide and maintain its own adapter logic for `yini-test` to call.

---

## Related documents
- [docs/adapter-contract.md](./docs/adapter-contract.md)
- [docs/case-contract.md](./docs/case-contract.md)
- [docs/runner-flow.md](./docs/runner-flow.md)

---

**^YINI ≡**  
> YINI is a human-readable, INI-inspired, indentation-insensitive configuration format with clear nested sections, explicit structure, and predictable parsing.
> 
> It has a formal specification and a defined grammar.

[yini-lang.org](https://yini-lang.org/?utm_source=github&utm_medium=referral&utm_campaign=yini_test&utm_content=readme_footer) · [YINI-lang on GitHub](https://github.com/YINI-lang)  
