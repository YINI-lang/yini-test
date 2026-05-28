"""
Shared data models for yini_test.
"""

# src/yini_test/models.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ValidCase:
    yini_path: Path
    json_path: Path


@dataclass(frozen=True, slots=True)
class WarningCase:
    yini_path: Path
    json_path: Path
    warning_path: Path


@dataclass(frozen=True, slots=True)
class InvalidCase:
    yini_path: Path


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_path: Path
    passed: bool
    message: str = ""


@dataclass(frozen=True, slots=True)
class AdapterResult:
    stdout: str
    stderr: str
    returncode: int
