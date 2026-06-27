"""
Core execution logic for yini_test.

This module orchestrates suite execution. Case discovery, adapter execution,
expected-output loading, and diff formatting live in dedicated helper modules.
"""

# src/yini_test/runner.py
from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
import json
from pathlib import Path
import sys
import time

# Remember this importing order:
#   1. standard libraries
#   2. blank line
#   3. local package imports, grouped by module

from yini_test import __version__
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


SUMMARY_RULE = "─" * 40
SUMMARY_RULE_FALLBACK = "-" * 40


@dataclass(frozen=True, slots=True)
class GroupSummary:
    suite_name: str
    mode: str
    passed: int
    failed: int
    duration: float

    @property
    def total(self) -> int:
        return self.passed + self.failed


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
        selected_suite=suite,
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
        selected_suite=suite,
        case_groups=case_groups,
        cases_root=cases_root,
        adapter_tokens=adapter_tokens,
        fail_fast=fail_fast,
        show_group_headers=True,
    )


def run_case_groups(
    selected_suite: str,
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
    group_summaries: list[GroupSummary] = []

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

        group_started_at = time.perf_counter()
        results = run_case_group(
            suite_name=suite_name,
            mode=mode,
            cases_root=cases_root,
            adapter_tokens=adapter_tokens,
            fail_fast=fail_fast,
        )
        group_duration = time.perf_counter() - group_started_at

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

        group_summaries.append(
            GroupSummary(
                suite_name=suite_name,
                mode=mode,
                passed=passed,
                failed=failed,
                duration=group_duration,
            )
        )

        if fail_fast and failed > 0:
            break

    total = total_passed + total_failed
    duration = time.perf_counter() - started_at

    print_summary(
        adapter_name=format_adapter_name(adapter_tokens),
        selected_suite=selected_suite,
        group_summaries=group_summaries,
        total_passed=total_passed,
        total_failed=total_failed,
        total=total,
        duration=duration,
    )

    return 0 if total_failed == 0 else 1


def print_summary(
    adapter_name: str,
    selected_suite: str,
    group_summaries: list[GroupSummary],
    total_passed: int,
    total_failed: int,
    total: int,
    duration: float,
) -> None:
    """
    Print the terminal summary table for a completed run.
    """

    print()
    summary_rule = format_summary_rule()

    print(summary_rule)
    print("YINI Test Suite Summary")
    print(f"Adapter: {adapter_name}")
    print(f"yini-test-suite: {__version__}")
    print(f"Test suite: {selected_suite}")
    print(f"YINI spec: {get_yini_spec_revision()}")
    print()
    print(
        f"{'Suite':<9}{'Mode':<9}{'Passed':>6}{'Failed':>8}{'Total':>7}{'Duration':>10}"
    )

    for group_summary in group_summaries:
        print(
            f"{group_summary.suite_name:<9}"
            f"{group_summary.mode:<9}"
            f"{group_summary.passed:>6}"
            f"{group_summary.failed:>8}"
            f"{group_summary.total:>7}"
            f"{format_duration(group_summary.duration):>10}"
        )

    print()
    print(
        f"Summary: {total_passed} passed, {total_failed} failed, "
        f"{total} total, duration {format_duration(duration)}"
    )
    print(f"Result: {'PASS' if total_failed == 0 else 'FAIL'}")

    failed_groups = [
        group_summary for group_summary in group_summaries if group_summary.failed > 0
    ]

    if failed_groups:
        print()
        print("Failed groups:")

        for group_summary in failed_groups:
            print(
                f"- {group_summary.suite_name} / {group_summary.mode}: "
                f"{group_summary.failed} failed"
            )


def format_summary_rule(stream_encoding: str | None = None) -> str:
    """
    Return the preferred summary rule when the terminal can encode it.
    """

    encoding = stream_encoding or sys.stdout.encoding or "utf-8"

    try:
        SUMMARY_RULE.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return SUMMARY_RULE_FALLBACK

    return SUMMARY_RULE


def get_yini_spec_revision() -> str:
    """
    Return the YINI spec revision declared by the packaged case corpus.
    """

    manifest = load_case_manifest()
    revision = manifest.get("yini_spec_revision")

    if isinstance(revision, str) and revision.strip():
        return revision

    return "not declared"


def load_case_manifest() -> dict[str, object]:
    """
    Load metadata for the packaged case corpus.
    """

    manifest_path = resources.files("yini_test").joinpath("cases", "manifest.json")
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)

    if not isinstance(manifest, dict):
        raise ValueError("Case manifest must contain a JSON object.")

    return manifest


def format_adapter_name(adapter_tokens: list[str]) -> str:
    """
    Return a compact adapter name suitable for summary output.
    """

    if not adapter_tokens:
        return "(none)"

    for token in adapter_tokens:
        parts = token.replace("\\", "/").split("/")

        for part in parts:
            if part.startswith("yini-parser-"):
                return part

    known_runners = {
        "bun",
        "deno",
        "node",
        "npx",
        "py",
        "python",
        "python3",
    }

    candidates = [
        token
        for token in adapter_tokens
        if token and not token.startswith("-") and "{" not in token
    ]

    for token in candidates:
        name = Path(token).stem or token

        if name.lower() not in known_runners:
            return name

    return Path(adapter_tokens[0]).stem or adapter_tokens[0]


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
