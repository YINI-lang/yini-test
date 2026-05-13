"""
Core execution logic for yini_test.

This file contains the main test-running behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib
import json
import subprocess
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidCase:
    yini_path: Path
    json_path: Path


@dataclass(frozen=True, slots=True)
class InvalidCase:
    yini_path: Path


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_path: Path
    passed: bool
    message: str = ""


def run_suite(
    suite: str,
    mode: str,
    cases_root: Path,
    adapter_tokens: list[str],
    fail_fast: bool = False,
) -> int:
    """
    Run one test suite in the requested parser mode.

    Parameters:
    - suite: "smoke" or "all"
    - mode: "lenient" or "strict"
    - cases_root: root directory containing test case suites
    - adapter_tokens: command tokens for the adapter
    - fail_fast: stop after the first failure if True

    Returns:
    - 0 if all cases passed
    - 1 if any case failed
    """

    suite_names = _resolve_suite_names(suite)
    total_passed = 0
    total_failed = 0

    """
    @TODO 2026-05:
        PASS    green
        FAIL    red
        SKIP    yellow
        Summary green if all passed, red if any failed
        - red   = expected output that was missing/changed in actual (conventional coloring used by Git etc)
        + green = actual output that differed from expected (conventional coloring used by Git etc)
        File paths cyan or dim
    """

    for suite_name in suite_names:
        results = run_case_group(
            suite_name=suite_name,
            mode=mode,
            cases_root=cases_root,
            adapter_tokens=adapter_tokens,
            fail_fast=fail_fast,
        )

        for result in results:
            label = "PASS" if result.passed else "FAIL"
            print(f"{label}  \"{result.case_path}\"")

            if not result.passed and result.message:
                print()
                print(result.message)

        passed = sum(1 for result in results if result.passed)
        failed = sum(1 for result in results if not result.passed)

        total_passed += passed
        total_failed += failed

        if fail_fast and failed > 0:
            break

    total = total_passed + total_failed
    print()
    print(f"Summary: {total_passed} passed, {total_failed} failed, {total} total")

    return 0 if total_failed == 0 else 1


def run_case_group(
    suite_name: str,
    mode: str,
    cases_root: Path,
    adapter_tokens: list[str],
    fail_fast: bool = False,
) -> list[CaseResult]:
    """
    Run one concrete suite directory.

    Examples:
    - cases/smoke/lenient
    - cases/smoke/strict
    - cases/golden/lenient
    - cases/golden/strict
    """

    suite_dir = cases_root / suite_name / mode

    if not suite_dir.exists():
        raise FileNotFoundError(f"Case directory does not exist: {suite_dir}")

    if not suite_dir.is_dir():
        raise NotADirectoryError(f"Case path is not a directory: {suite_dir}")

    valid_cases = discover_valid_cases(suite_dir / "valid")
    invalid_cases = discover_invalid_cases(suite_dir / "invalid")

    results: list[CaseResult] = []

    for case in valid_cases:
        result = run_valid_case(case, adapter_tokens=adapter_tokens, mode=mode)
        results.append(result)

        if fail_fast and not result.passed:
            return results

    for case in invalid_cases:
        result = run_invalid_case(case, adapter_tokens=adapter_tokens, mode=mode)
        results.append(result)

        if fail_fast and not result.passed:
            return results

    return results


def get_expected_json_path(yini_path: Path) -> Path:
    """
    Return the expected JSON output path for a valid YINI case.

    Valid cases are golden tests. Therefore, each valid .yini input file
    must have a matching .json expected-output file beside it.

    Example:

        2-basic-config.yini
        2-basic-config.json
    """

    json_path = yini_path.with_suffix(".json")

    if not json_path.is_file():
        raise FileNotFoundError(
            "Expected JSON file not found for valid YINI case.\n"
            f"  yini_path: \"{yini_path}\",\n"
            f"  expected_json_path: \"{json_path}\"\n"
            "  Hint: Every valid .yini case must have a matching .json file "
            "with the same basename."
        )

    return json_path


def discover_valid_cases(valid_dir: Path) -> list[ValidCase]:
    """
    Discover valid YINI test cases.

    Each valid case must consist of:

        example.yini
        example.json

    The .yini file is the input.
    The .json file is the expected parser output.
    """

    cases: list[ValidCase] = []

    if not valid_dir.exists():
        return cases

    if not valid_dir.is_dir():
        raise NotADirectoryError(f"Valid case path is not a directory: {valid_dir}")

    for yini_path in sorted(valid_dir.glob("*.yini")):
        json_path = get_expected_json_path(yini_path)
        cases.append(ValidCase(yini_path=yini_path, json_path=json_path))

    return cases


def discover_invalid_cases(invalid_dir: Path) -> list[InvalidCase]:
    """
    Discover invalid YINI test cases.

    Each invalid case must contain one .yini file.

    Invalid cases do not need matching .json files because they are expected
    to fail parsing.
    """

    if not invalid_dir.exists():
        return []

    if not invalid_dir.is_dir():
        raise NotADirectoryError(f"Invalid case path is not a directory: {invalid_dir}")

    return [
        InvalidCase(yini_path=path)
        for path in sorted(invalid_dir.glob("*.yini"))
    ]


def run_valid_case(
    case: ValidCase,
    adapter_tokens: list[str],
    mode: str,
) -> CaseResult:
    """
    Run a valid case.

    Expected behavior:
    - adapter succeeds
    - adapter outputs valid JSON
    - actual JSON matches expected JSON
    """

    expected = load_expected_json(case.json_path)

    try:
        actual = run_adapter(adapter_tokens, input_path=case.yini_path, mode=mode)
    except RuntimeError as exc:
        return CaseResult(
            case_path=case.yini_path,
            passed=False,
            message=str(exc),
        )

    if actual == expected:
        return CaseResult(case_path=case.yini_path, passed=True)

    diff = make_diff(expected, actual)

    return CaseResult(
        case_path=case.yini_path,
        passed=False,
        message=(
            f"Output mismatch for valid case: {case.yini_path.name}\n"
            f"{diff}"
        ),
    )


def run_invalid_case(
    case: InvalidCase,
    adapter_tokens: list[str],
    mode: str,
) -> CaseResult:
    """
    Run an invalid case.

    Expected behavior:
    - adapter fails with non-zero exit code
    """

    command = render_adapter_command(
        adapter_tokens=adapter_tokens,
        input_path=case.yini_path,
        mode=mode,
    )

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if completed.returncode != 0:
        return CaseResult(case_path=case.yini_path, passed=True)

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()

    details = []

    if stdout:
        details.append(f"stdout:\n{stdout}")

    if stderr:
        details.append(f"stderr:\n{stderr}")

    message = (
        f"Invalid case unexpectedly succeeded: {case.yini_path.name}\n"
        f"Command: {' '.join(command)}"
    )

    if details:
        message += "\n" + "\n".join(details)

    return CaseResult(
        case_path=case.yini_path,
        passed=False,
        message=message,
    )


def load_expected_json(path: Path) -> Any:
    """
    Load the expected JSON output for a valid case.

    The expected JSON file may contain a UTF-8 BOM if it was created by
    Windows PowerShell or some editors. Using utf-8-sig accepts both normal
    UTF-8 and UTF-8 with BOM.
    """

    try:
        # utf-8-sig can read both:
        # - UTF-8 without BOM
        # - UTF-8 with BOM
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Expected JSON file is not valid JSON.\n"
            f"  json_path: \"{path}\"\n"
            f"  error: {exc}"
        ) from exc
    

def run_adapter(
    adapter_tokens: list[str],
    input_path: Path,
    mode: str,
) -> Any:
    """
    Run the adapter for a valid case and return parsed JSON output.

    Raises RuntimeError if the adapter:
    - exits with non-zero status
    - prints no output
    - prints invalid JSON
    """

    command = render_adapter_command(
        adapter_tokens=adapter_tokens,
        input_path=input_path,
        mode=mode,
    )

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        details = stderr or stdout or "No error output."

        raise RuntimeError(
            f"Adapter failed for valid case: {input_path.name}\n"
            f"Command: {' '.join(command)}\n"
            f"Details: {details}"
        )

    stdout = completed.stdout.strip()

    if not stdout:
        raise RuntimeError(
            f"Adapter produced no JSON output for valid case: {input_path.name}"
        )

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Adapter output was not valid JSON for case: {input_path.name}\n"
            f"Error: {exc}\n"
            f"Output:\n{stdout}"
        ) from exc


def render_adapter_command(
    adapter_tokens: list[str],
    input_path: Path,
    mode: str,
) -> list[str]:
    """
    Replace placeholders in adapter command tokens.

    Supported placeholders:
    - {input}
    - {mode}
    """

    if not adapter_tokens:
        raise ValueError("Adapter command is empty.")

    return [
        token.format(input=str(input_path), mode=mode)
        for token in adapter_tokens
    ]


def make_diff(expected: Any, actual: Any) -> str:
    """
    Create a readable diff between expected JSON and parser output.

    The raw unified diff hunk header, for example:

        @@ -1 +1,49 @@

    is replaced with a clearer yini-test-specific line:

        Mismatched block: Expected line 1 does not match parser output lines 1-49.
    """

    expected_text = json.dumps(
        expected,
        indent=4,
        ensure_ascii=False,
        sort_keys=True,
    )
    actual_text = json.dumps(
        actual,
        indent=4,
        ensure_ascii=False,
        sort_keys=True,
    )

    diff_lines = list(
        difflib.unified_diff(
            expected_text.splitlines(),
            actual_text.splitlines(),
            fromfile="expected",
            tofile="parser output",
            lineterm="",
        )
    )

    readable_lines = [
        _format_diff_hunk_header(line) if line.startswith("@@ ") else line
        for line in diff_lines
    ]

    spaced_lines = _add_spacing_around_diff_blocks(readable_lines)

    return "\n".join(spaced_lines)


def _add_spacing_around_diff_blocks(lines: list[str]) -> list[str]:
    """
    Add blank lines around expected/parser-output diff blocks.

    This makes output like this:

        -{}
        +{
        +    "App": {}
        +}

    easier to read as:

        -{}

        +{
        +    "App": {}
        +}

    Diff headers such as "--- expected" and "+++ parser output" are not treated
    as removed/added content lines.
    """

    result: list[str] = []
    previous_kind: str | None = None

    for line in lines:
        current_kind = _get_diff_content_kind(line)

        # Add a blank line before the first removed/added content block.
        if current_kind in {"removed", "added"} and previous_kind not in {
            "removed",
            "added",
        }:
            if result and result[-1] != "":
                result.append("")

        # Add a blank line between a removed block and an added block.
        if (
            current_kind in {"removed", "added"}
            and previous_kind in {"removed", "added"}
            and current_kind != previous_kind
        ):
            if result and result[-1] != "":
                result.append("")

        result.append(line)
        previous_kind = current_kind

    # Add one blank line after the final removed/added content block.
    if previous_kind in {"removed", "added"}:
        result.append("")

    return result


def _get_diff_content_kind(line: str) -> str | None:
    """
    Return whether a diff line is removed content or added content.

    This intentionally ignores unified diff file headers:

        --- expected
        +++ parser output
    """

    if line.startswith("--- ") or line.startswith("+++ "):
        return None

    if line.startswith("-"):
        return "removed"

    if line.startswith("+"):
        return "added"

    return None


def _format_diff_hunk_header(line: str) -> str:
    """
    Convert a unified diff hunk header into a clearer message.

    Example:

        @@ -1 +1,49 @@

    becomes:

        Changed block: Expected line 1 does not match parser output lines 1-49.
    """

    parts = line.split()

    if len(parts) < 3:
        return line

    expected_range = parts[1]
    actual_range = parts[2]

    if not expected_range.startswith("-") or not actual_range.startswith("+"):
        return line

    expected_text = _format_diff_range(expected_range[1:])
    actual_text = _format_diff_range(actual_range[1:])

    return (
        f"Mismatched block: Expected {expected_text} does not match "
        f"parser output {actual_text}."
    )


def _format_diff_range(raw_range: str) -> str:
    """
    Format a unified diff line range.

    Examples:
    - "1"    -> "line 1"
    - "1,1"  -> "line 1"
    - "1,49" -> "lines 1-49"
    - "5,3"  -> "lines 5-7"
    """

    if "," not in raw_range:
        return f"line {raw_range}"

    start_text, count_text = raw_range.split(",", 1)

    start = int(start_text)
    count = int(count_text)

    if count == 1:
        return f"line {start}"

    end = start + count - 1

    return f"lines {start}-{end}"


def _resolve_suite_names(suite: str) -> list[str]:
    """
    Resolve a user-facing suite name into concrete suite directories.

    Current mapping:
    - smoke -> ["smoke"]
    - all -> ["smoke", "golden"]
    """

    if suite == "smoke":
        return ["smoke"]

    if suite == "all":
        return ["smoke", "golden"]

    raise ValueError(f"Unsupported suite: {suite!r}")
