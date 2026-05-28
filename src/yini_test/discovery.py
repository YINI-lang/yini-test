"""
Case discovery helpers for yini_test.
"""

# src/yini_test/discovery.py
from __future__ import annotations

from pathlib import Path

from yini_test.models import InvalidCase, ValidCase, WarningCase


def get_expected_json_path(yini_path: Path) -> Path:
    """
    Return the expected JSON output path for a YINI case.

    Valid and warning cases must have:

        example.yini
        example.json
    """

    json_path = yini_path.with_suffix(".json")

    if not json_path.is_file():
        raise FileNotFoundError(
            "Expected JSON file not found for YINI case.\n"
            f"  yini_path: \"{yini_path}\",\n"
            f"  expected_json_path: \"{json_path}\"\n"
            "  Hint: Every valid or warning .yini case must have a matching "
            ".json file with the same basename."
        )

    return json_path


def get_expected_warning_path(yini_path: Path) -> Path:
    """
    Return the expected warning diagnostics path for a warning YINI case.

    Warning cases must have:

        example.yini
        example.json
        example.warning.json
    """

    warning_path = yini_path.with_suffix(".warning.json")

    if not warning_path.is_file():
        raise FileNotFoundError(
            "Expected warning file not found for warning YINI case.\n"
            f"  yini_path: \"{yini_path}\",\n"
            f"  expected_warning_path: \"{warning_path}\"\n"
            "  Hint: Every warning .yini case must have a matching "
            ".warning.json file with the same basename."
        )

    return warning_path


def discover_valid_cases(valid_dir: Path) -> list[ValidCase]:
    """
    Discover valid YINI test cases.

    Each valid case must consist of:

        example.yini
        example.json
    """

    cases: list[ValidCase] = []

    if not valid_dir.exists():
        return cases

    if not valid_dir.is_dir():
        raise NotADirectoryError(f"Valid case path is not a directory: {valid_dir}")

    for yini_path in sorted(valid_dir.rglob("*.yini")):
        json_path = get_expected_json_path(yini_path)
        cases.append(ValidCase(yini_path=yini_path, json_path=json_path))

    return cases


def discover_warning_cases(warning_dir: Path) -> list[WarningCase]:
    """
    Discover warning YINI test cases.

    Each warning case must consist of:

        example.yini
        example.json
        example.warning.json
    """

    cases: list[WarningCase] = []

    if not warning_dir.exists():
        return cases

    if not warning_dir.is_dir():
        raise NotADirectoryError(
            f"Warning case path is not a directory: {warning_dir}"
        )

    for yini_path in sorted(warning_dir.rglob("*.yini")):
        json_path = get_expected_json_path(yini_path)
        warning_path = get_expected_warning_path(yini_path)
        cases.append(
            WarningCase(
                yini_path=yini_path,
                json_path=json_path,
                warning_path=warning_path,
            )
        )

    return cases


def discover_invalid_cases(invalid_dir: Path) -> list[InvalidCase]:
    """
    Discover invalid YINI test cases.

    Each invalid case must contain one .yini file.
    """

    if not invalid_dir.exists():
        return []

    if not invalid_dir.is_dir():
        raise NotADirectoryError(f"Invalid case path is not a directory: {invalid_dir}")

    return [
        InvalidCase(yini_path=path)
        for path in sorted(invalid_dir.rglob("*.yini"))
    ]
