"""
Core execution logic for yini_test.

This file contains the main test-running behavior.
"""

#  src/yini_test/runner.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib
import json
import subprocess
from typing import Any


@dataclass(slots=True)
class FixturePair:
    yini_path: Path
    json_path: Path


@dataclass(slots=True)
class TestResult:
    fixture: FixturePair
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
            print(f"{label}  {result.case_path}")

            if not result.passed and result.message:
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
    Run one concrete suite directory, such as:
    - cases/smoke/lenient
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


def discover_valid_cases(valid_dir: Path) -> list[ValidCase]:
    """
    Discover valid cases in a valid/ directory.

    Each valid case must contain:
    - one .yini file
    - one matching .json file
    """

    if not valid_dir.exists():
        return []

    if not valid_dir.is_dir():
        raise NotADirectoryError(f"Valid case path is not a directory: {valid_dir}")

    cases: list[ValidCase] = []

    for yini_path in sorted(valid_dir.glob("*.yini")):
        json_path = yini_path.with_suffix(".json")

        if not json_path.exists():
            raise FileNotFoundError(
                f"Missing expected JSON file for valid case: {yini_path} "
                f"(expected {json_path.name})"
            )

        cases.append(ValidCase(yini_path=yini_path, json_path=json_path))

    return cases


def discover_invalid_cases(invalid_dir: Path) -> list[InvalidCase]:
    """
    Discover invalid cases in an invalid/ directory.

    Each invalid case must contain:
    - one .yini file
    """
    
    if not invalid_dir.exists():
        return []

    if not invalid_dir.is_dir():
        raise NotADirectoryError(f"Invalid case path is not a directory: {invalid_dir}")

    return [InvalidCase(yini_path=path) for path in sorted(invalid_dir.glob("*.yini"))]


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
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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
    Create a readable unified diff between expected and actual JSON values.
    """
    
    expected_text = json.dumps(expected, indent=4, ensure_ascii=False, sort_keys=True)
    actual_text = json.dumps(actual, indent=4, ensure_ascii=False, sort_keys=True)

    diff = difflib.unified_diff(
        expected_text.splitlines(),
        actual_text.splitlines(),
        fromfile="expected",
        tofile="actual",
        lineterm="",
    )
    return "\n".join(diff)


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
