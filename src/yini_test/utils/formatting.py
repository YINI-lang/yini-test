"""
Output formatting helpers for yini_test.
"""

# src/yini_test/utils/formatting.py
from __future__ import annotations


def format_duration(seconds: float) -> str:
    """
    Format a duration in a compact human-readable form.
    """

    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"

    if seconds < 60:
        return f"{seconds:.2f} s"

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    return f"{minutes} min {remaining_seconds:.2f} s"
