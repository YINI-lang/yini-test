"""
Expected-output and warning-matching helpers for yini_test.
"""

# src/yini_test/expectations.py
from __future__ import annotations

from pathlib import Path
import json
from typing import Any


def load_expected_json(path: Path) -> Any:
    """
    Load an expected JSON file.

    The file may contain a UTF-8 BOM. Using utf-8-sig accepts both normal
    UTF-8 and UTF-8 with BOM.
    """

    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Expected JSON file is not valid JSON.\n"
            f"  json_path: \"{path}\"\n"
            f"  error: {exc}"
        ) from exc


def load_expected_warnings(path: Path) -> list[dict[str, Any]]:
    """
    Load expected warning diagnostics for a warning case.

    Initial warning format:

        [
            {
                "contains": "YINI_MODE_MISMATCH"
            }
        ]
    """

    warnings_data = load_expected_json(path)

    if not isinstance(warnings_data, list):
        raise RuntimeError(
            "Expected warning file must contain a JSON array.\n"
            f"  warning_path: \"{path}\""
        )

    for index, item in enumerate(warnings_data):
        if not isinstance(item, dict):
            raise RuntimeError(
                "Each expected warning entry must be a JSON object.\n"
                f"  warning_path: \"{path}\"\n"
                f"  index: {index}"
            )

        if "contains" not in item:
            raise RuntimeError(
                "Each expected warning entry must contain a 'contains' field.\n"
                f"  warning_path: \"{path}\"\n"
                f"  index: {index}"
            )

        if not isinstance(item["contains"], str):
            raise RuntimeError(
                "The expected warning 'contains' field must be a string.\n"
                f"  warning_path: \"{path}\"\n"
                f"  index: {index}"
            )

    return warnings_data


def match_expected_warnings(
    expected_warnings: list[dict[str, Any]],
    stderr: str,
) -> str | None:
    """
    Check that every expected warning marker appears in stderr.

    Returns None when all expected warnings match.
    Returns an error message otherwise.
    """

    for expected_warning in expected_warnings:
        expected_text = expected_warning["contains"]

        if expected_text not in stderr:
            return (
                "Expected warning text was not found.\n"
                f"  expected contains: {expected_text!r}"
            )

    return None
