"""
Readable JSON diff helpers for yini_test.
"""

# src/yini_test/diffing.py
from __future__ import annotations

import difflib
import json
from typing import Any


def make_diff(expected: Any, actual: Any) -> str:
    """
    Create a readable diff between expected JSON and parser output.
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
    """

    result: list[str] = []
    previous_kind: str | None = None

    for line in lines:
        current_kind = _get_diff_content_kind(line)

        if current_kind in {"removed", "added"} and previous_kind not in {
            "removed",
            "added",
        }:
            if result and result[-1] != "":
                result.append("")

        if (
            current_kind in {"removed", "added"}
            and previous_kind in {"removed", "added"}
            and current_kind != previous_kind
        ):
            if result and result[-1] != "":
                result.append("")

        result.append(line)
        previous_kind = current_kind

    if previous_kind in {"removed", "added"}:
        result.append("")

    return result


def _get_diff_content_kind(line: str) -> str | None:
    """
    Return whether a diff line is removed content or added content.
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
