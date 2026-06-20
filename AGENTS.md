# AGENTS.md

> AI agent instructions for this repository.
> Read this before making any changes to the codebase.
> If any instruction in this file is unclear, ambiguous, or conflicts with the repository state, stop and ask the human maintainer before proceeding.

See also: [Shared AI agent instructions for the YINI project family](../AGENTS.md)

## Project Overview

- **Name:** `yini-test`
- **Purpose:** Shared test harness and case corpus for YINI parser implementations.
- **Language/runtime:** Python 3.10+
- **Packaging:** `setuptools` via `pyproject.toml`
- **Dependency files:** `requirements.txt` and `requirements-dev.txt`
- **Task runner:** Taskfile (`Taskfile.yml`)
- **Test framework:** pytest
- **Lint/format/type tools:** Ruff and mypy
- **Monorepo:** No

This repository does **not** contain a YINI parser. It discovers YINI test cases, runs an external parser adapter, and checks whether that adapter succeeds, fails, warns, and emits JSON according to the case contract.

## Repository Structure

```text
.
|-- src/yini_test/              # Python package and CLI implementation.
|-- src/yini_test/cases/        # Packaged smoke and golden YINI case corpus.
|   |-- smoke/                  # Small practical confidence tests.
|   `-- golden/                 # Broader fixed-output conformance cases.
|-- tests/                      # Tests for the yini-test runner itself.
|-- docs/                       # Contracts and runner documentation.
|-- runner-configs/             # Runner configuration files, if present.
|-- Taskfile.yml                # Common development and adapter-run commands.
|-- pyproject.toml              # Build metadata and pytest configuration.
|-- requirements-dev.txt        # Development dependencies.
|-- requirements.txt            # Runtime dependency placeholder.
`-- README.md                   # Human-facing project overview.
```

Important modules:
- `src/yini_test/cli.py`: command-line argument parsing.
- `src/yini_test/runner.py`: suite and case execution.
- `src/yini_test/discovery.py`: valid, warning, and invalid case discovery.
- `src/yini_test/adapters.py`: adapter command execution and stdout parsing.
- `src/yini_test/expectations.py`: expected JSON and warning loading/matching.
- `src/yini_test/diffing.py`: mismatch formatting.
- `src/yini_test/models.py`: case and result dataclasses.
- `src/yini_test/utils/`: small shared helper utilities.

## Commands

Install development dependencies and editable package:

```bash
task install
```

Run the unit/integration tests for `yini-test` itself:

```bash
task test
```

Run all repository checks:

```bash
task check
```

Equivalent direct commands:

```bash
python -m pytest -v -W error
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy -p yini_test --explicit-package-bases --ignore-missing-imports
```

On Windows, the Taskfile typecheck command sets `MYPYPATH=src` through `cmd /c`. If running mypy directly on Windows, use the same environment setup.

Run smoke or golden cases against configured parser adapters:

```bash
task run-smoke-python-lenient
task run-smoke-python-strict
task run-all-python
task run-smoke-typescript-lenient
task run-smoke-typescript-strict
task run-all-typescript
```

These adapter commands assume sibling repositories named `../yini-parser-python` and `../yini-parser-typescript`, as documented in `README.md`.

## Required Checks

Before considering a change complete, run the smallest relevant checks first.

For documentation-only changes:

```bash
python -m pytest -v -W error
```

For runner, discovery, expectation, adapter, or CLI changes:

```bash
task test
task lint
task typecheck
```

For formatting-sensitive changes:

```bash
task format-check
```

For broad changes:

```bash
task check
```

For case-corpus changes, also run the relevant adapter cases if the required sibling parser repository is available:

```bash
task run-smoke-python-lenient
task run-smoke-python-strict
task run-all-python
```

If a required check cannot be run, explain why and describe what was validated instead.

## Code Style

Follow the existing Python style in `src/yini_test` and `tests`.

General rules:
- Prefer clear, simple, maintainable code.
- Prefer small, focused changes.
- Do not rewrite unrelated code.
- Do not reformat files unnecessarily.
- Keep error messages clear and deterministic.
- Do not silently normalize invalid strict-mode syntax.
- Keep public APIs stable unless the task explicitly asks for an API change.
- Add or update tests when behavior changes.
- Prefer explicit, readable logic over clever or overly compact code.
- Preserve existing naming conventions, file layout, and architectural patterns.
- Keep imports grouped as standard library, blank line, then local package imports.
- Use `pathlib.Path` for filesystem paths, matching the current code.
- Keep command output and error messages useful for parser implementers.

## Testing

When changing runner behavior:
- Add or update focused pytest coverage in `tests/`.
- Prefer direct tests of discovery, runner, adapter, expectation, or diff helpers.
- Keep tests deterministic and filesystem-local, usually with `tmp_path`.
- Do not remove failing tests. Fix the issue or clearly report why the test is failing.

When changing the case corpus:
- Valid cases must include a `.yini` file and matching `.json` file with the same basename.
- Warning cases must include `.yini`, `.json`, and `.warning.json` files with the same basename.
- Invalid cases only require the `.yini` file; do not add expected-output sidecars unless the runner contract changes.
- Strict valid cases may use `.strict.yini` / `.strict.json` names, but parser mode is determined by the directory and CLI flag, not the filename.
- Expected JSON should be valid machine-readable JSON and preferably pretty-formatted with 4-space indentation.

## Documentation Guidance

Update documentation when a change affects:
- command-line usage,
- adapter behavior,
- case layout or case contracts,
- installation,
- examples,
- user-visible runner behavior.

Keep documentation concise and consistent with the direct tone in `README.md` and `docs/`.

## Dependency Policy

Do not add new runtime dependencies unless clearly necessary.

Before adding a dependency, prefer:

1. Existing project utilities.
2. Python standard library functionality.
3. Small local helper functions.

If a new dependency is necessary, explain why it is justified and update the appropriate requirements file.

## Safety and Scope Boundaries

### Always Do

- Run tests before submitting any change.
- Match the code patterns in the file you are editing.
- Keep changes focused — one concern per PR.
- When editing Markdown files, if a line introduces a bulleted list and ends with a colon (`:`), place the first bullet immediately on the next line. Do not insert a blank line between the introductory line and the first bullet.

### Ask First

- Before adding a new dependency.
- Before changing the public API or exported types.
- Before modifying CI/CD configuration.
- Before refactoring shared utilities used across multiple modules.

### Never Do

Do not modify:
- secrets,
- credentials,
- private keys,
- `.env` files,
- generated files unless generation is part of the requested task,
- vendored dependencies,
- lockfiles unless dependency changes require it,
- unrelated formatting or whitespace.

Do not perform destructive operations such as:
- deleting large parts of the repository,
- resetting history,
- force-pushing,
- creating releases,
- publishing packages.

Do not create commits, tags, branches, or releases unless explicitly requested.

## Project-Specific Notes

The YINI format values clarity, readability, predictability, explicit structure, and deterministic parsing.

When changing code, tests, cases, examples, or documentation:
- Prefer clarity over cleverness.
- Avoid implicit or magical behavior.
- Keep syntax examples human-readable.
- Preserve strict-mode and lenient-mode separation.
- Keep parser behavior aligned with the current YINI specification and this repository's case contract.
- Add or update golden tests when parsing behavior changes.
- Prefer precise diagnostics over vague errors.
- Remember that adapters live in parser repositories; this repo defines the harness and shared expectations.
- Keep `docs/case-contract.md`, `docs/adapter-contract.md`, and `docs/runner-flow.md` in sync with runner behavior.
