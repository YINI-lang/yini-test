"""
Command-line interface for yini_test.

Defines the user-facing CLI, parses arguments, and forwards execution
to the runner layer.

Supported forms:
    yini-test
    yini-test smoke
    yini-test all
    yini-test smoke --strict
    yini-test all --strict

Notes:
- The default suite is "all".
- The default mode is lenient.
- The --adapter option is required and must be placed last.
"""

# src/yini_test/cli.py
from __future__ import annotations

import argparse
from pathlib import Path

from .runner import run_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yini-test",
        description="Run YINI test suites against a parser adapter.",
    )

    parser.add_argument(
        "suite",
        nargs="?",
        choices=("all", "smoke"),
        default="all",
        help="Test suite to run. Default: all",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Run cases in strict mode. Default: lenient mode",
    )

    parser.add_argument(
        "--cases-root",
        type=Path,
        default=Path("cases"),
        help="Root directory containing test cases. Default: cases",
    )

    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at the first failing case.",
    )

    parser.add_argument(
        "--adapter",
        nargs=argparse.REMAINDER,
        required=True,
        help=(
            "Adapter command tokens. Put this option last. "
            "Use {input} and {mode} placeholders inside the adapter command. "
            "Example: --adapter python path/to/adapter.py --input {input} --mode {mode}"
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.adapter:
        parser.error("--adapter requires a command")

    mode = "strict" if args.strict else "lenient"

    return run_suite(
        suite=args.suite,
        mode=mode,
        cases_root=args.cases_root,
        adapter_tokens=args.adapter,
        fail_fast=args.fail_fast,
    )
