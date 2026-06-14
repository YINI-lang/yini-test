"""
Core execution logic for yini_test.

This module orchestrates suite execution. Case discovery, adapter execution,
expected-output loading, and diff formatting live in dedicated helper modules.
"""

# src/yini_test/runner.py
from __future__ import annotations

from pathlib import Path
import time

# Remember this importing order:
#   1. standard libraries
#   2. blank line
#   3. local package imports, grouped by module

from yini_test.adapters import (
    parse_adapter_stdout_json,
    render_adapter_command,
    run_adapter,
    run_adapter_raw,
)
from yini_test.diffing import make_diff
from yini_test.discovery import (
    discover_invalid_cases,
    discover_valid_cases,
    discover_warning_cases,
)
from yini_test.expectations import (
    load_expected_json,
    load_expected_warnings,
    match_expected_warnings,
)
from yini_test.models import CaseResult, InvalidCase, ValidCase, WarningCase
from yini_test.utils.executables import resolve_executable
from yini_test.utils.formatting import format_duration


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
    case_groups = [(suite_name, mode) for suite_name in suite_names]

    return run_case_groups(
        case_groups=case_groups,
        cases_root=cases_root,
        adapter_tokens=adapter_tokens,
        fail_fast=fail_fast,
        show_group_headers=False,
    )


def run_suite_matrix(
    suite: str,
    modes: list[str],
    cases_root: Path,
    adapter_tokens: list[str],
    fail_fast: bool = False,
) -> int:
    """
    Run selected suites across multiple parser modes.

    The order is suite-major, then mode-major. For "all" and
    ["lenient", "strict"], this runs:
    - smoke / lenient
    - smoke / strict
    - golden / lenient
    - golden / strict
    """

    suite_names = _resolve_suite_names(suite)
    case_groups = [(suite_name, mode) for suite_name in suite_names for mode in modes]

    return run_case_groups(
        case_groups=case_groups,
        cases_root=cases_root,
        adapter_tokens=adapter_tokens,
        fail_fast=fail_fast,
        show_group_headers=True,
    )


def run_case_groups(
    case_groups: list[tuple[str, str]],
    cases_root: Path,
    adapter_tokens: list[str],
    fail_fast: bool = False,
    show_group_headers: bool = False,
) -> int:
    """
    Run concrete suite/mode groups and print one combined summary.
    """

    started_at = time.perf_counter()
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

    for suite_name, mode in case_groups:
        if show_group_headers:
            print()
            print(f"Group: {suite_name} / {mode}")

        results = run_case_group(
            suite_name=suite_name,
            mode=mode,
            cases_root=cases_root,
            adapter_tokens=adapter_tokens,
            fail_fast=fail_fast,
        )

        for result in results:
            label = "PASS" if result.passed else "FAIL"
            print(f'{label}  "{result.case_path}"')

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
    duration = time.perf_counter() - started_at

    print()
    print(
        f"Summary: {total_passed} passed, {total_failed} failed, "
        f"{total} total, duration {format_duration(duration)}"
    )

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

    Case categories:
    - valid: must succeed and match .json
    - warning: must succeed, match .json, and match warning expectations
    - invalid: must fail
    """

    suite_dir = cases_root / suite_name / mode

    if not suite_dir.exists():
        raise FileNotFoundError(f"Case directory does not exist: {suite_dir}")

    if not suite_dir.is_dir():
        raise NotADirectoryError(f"Case path is not a directory: {suite_dir}")

    valid_cases = discover_valid_cases(suite_dir / "valid")
    warning_cases = discover_warning_cases(suite_dir / "warning")
    invalid_cases = discover_invalid_cases(suite_dir / "invalid")

    results: list[CaseResult] = []

    for valid_case in valid_cases:
        result = run_valid_case(valid_case, adapter_tokens=adapter_tokens, mode=mode)
        results.append(result)

        if fail_fast and not result.passed:
            return results

    for warning_case in warning_cases:
        result = run_warning_case(
            warning_case, adapter_tokens=adapter_tokens, mode=mode
        )
        results.append(result)

        if fail_fast and not result.passed:
            return results

    for invalid_case in invalid_cases:
        result = run_invalid_case(
            invalid_case, adapter_tokens=adapter_tokens, mode=mode
        )
        results.append(result)

        if fail_fast and not result.passed:
            return results

    return results


def run_valid_case(
    case: ValidCase,
    adapter_tokens: list[str],
    mode: str,
) -> CaseResult:
    """
    Run a valid case.

    Expected behavior:
    - Adapter succeeds.
    - Adapter outputs valid JSON.
    - Actual JSON matches expected JSON.
    """

    expected = load_expected_json(case.json_path)

    print(f'RUN   "{case.yini_path}"')
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
        message=(f"Output mismatch for valid case: {case.yini_path.name}\n{diff}"),
    )


def run_warning_case(
    case: WarningCase,
    adapter_tokens: list[str],
    mode: str,
) -> CaseResult:
    """
    Run a warning case.

    Expected behavior:
    - Adapter succeeds.
    - Adapter outputs valid JSON.
    - Actual JSON matches expected JSON.
    - Adapter emits the expected warning diagnostics.
    """

    expected_json = load_expected_json(case.json_path)
    expected_warnings = load_expected_warnings(case.warning_path)

    print(f'RUN   "{case.yini_path}"')
    try:
        adapter_result = run_adapter_raw(
            adapter_tokens=adapter_tokens,
            input_path=case.yini_path,
            mode=mode,
        )
    except RuntimeError as exc:
        return CaseResult(
            case_path=case.yini_path,
            passed=False,
            message=str(exc),
        )

    if adapter_result.returncode != 0:
        return CaseResult(
            case_path=case.yini_path,
            passed=False,
            message=(
                f"Adapter failed for warning case: {case.yini_path.name}\n"
                f"stderr:\n{adapter_result.stderr.strip()}"
            ),
        )

    try:
        actual_json = parse_adapter_stdout_json(
            adapter_result.stdout,
            case_name=case.yini_path.name,
        )
    except RuntimeError as exc:
        return CaseResult(
            case_path=case.yini_path,
            passed=False,
            message=str(exc),
        )

    if actual_json != expected_json:
        diff = make_diff(expected_json, actual_json)
        return CaseResult(
            case_path=case.yini_path,
            passed=False,
            message=(
                f"Output mismatch for warning case: {case.yini_path.name}\n{diff}"
            ),
        )

    warning_error = match_expected_warnings(
        expected_warnings=expected_warnings,
        stderr=adapter_result.stderr,
    )

    if warning_error is not None:
        return CaseResult(
            case_path=case.yini_path,
            passed=False,
            message=(
                f"Warning mismatch for warning case: {case.yini_path.name}\n"
                f"{warning_error}\n"
                f"stderr:\n{adapter_result.stderr.strip()}"
            ),
        )

    return CaseResult(case_path=case.yini_path, passed=True)


def run_invalid_case(
    case: InvalidCase,
    adapter_tokens: list[str],
    mode: str,
) -> CaseResult:
    """
    Run an invalid case.

    Expected behavior:
    - Adapter fails with a non-zero exit code.
    """

    command = render_adapter_command(
        adapter_tokens=adapter_tokens,
        input_path=case.yini_path,
        mode=mode,
    )

    command[0] = resolve_executable(command[0])

    print(f'RUN   "{case.yini_path}"')
    try:
        adapter_result = run_adapter_raw(
            adapter_tokens=adapter_tokens,
            input_path=case.yini_path,
            mode=mode,
        )
    except RuntimeError as exc:
        return CaseResult(
            case_path=case.yini_path,
            passed=False,
            message=str(exc),
        )

    if adapter_result.returncode != 0:
        return CaseResult(case_path=case.yini_path, passed=True)

    details = []

    stdout = adapter_result.stdout.strip()
    stderr = adapter_result.stderr.strip()

    if stdout:
        details.append(f"stdout:\n{stdout}")

    if stderr:
        details.append(f"stderr:\n{stderr}")

    message = (
        f'Invalid case was expected to fail, but succeeded: "{case.yini_path.name}"\n'
        f"Command: {' '.join(command)}"
    )

    if details:
        message += "\n" + "\n".join(details)

    return CaseResult(
        case_path=case.yini_path,
        passed=False,
        message=message,
    )


def _resolve_suite_names(suite: str) -> list[str]:
    """
    Resolve a user-facing suite name into concrete suite directories.

    Current mapping:
    - smoke -> ["smoke"]
    - golden -> ["golden"]
    - all -> ["smoke", "golden"]
    """

    if suite == "smoke":
        return ["smoke"]

    if suite == "golden":
        return ["golden"]

    if suite == "all":
        return ["smoke", "golden"]

    raise ValueError(f"Unsupported suite: {suite!r}")
