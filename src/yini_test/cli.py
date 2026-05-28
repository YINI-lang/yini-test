"""
Command-line interface for yini_test.

This module defines the user-facing CLI for the yini-test command.

The CLI is intentionally small. It only:

1. Defines accepted command-line arguments.
2. Parses those arguments.
3. Converts CLI options into runner options.
4. Delegates the actual test execution to src/yini_test/runner.py.

Supported forms:

    yini-test --adapter ...
    yini-test smoke --adapter ...
    yini-test all --adapter ...
    yini-test smoke --strict --adapter ...
    yini-test all --strict --adapter ...

Notes:
- The default suite is "all".
- The default mode is lenient.
- The --adapter option is required.
- The --adapter option must be placed last because it captures the remaining command tokens.
"""

# src/yini_test/cli.py
from __future__ import annotations

import argparse
from pathlib import Path

from .runner import run_suite


def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the command-line argument parser.

    This function only describes the CLI shape. It does not run any tests.
    Keeping parser construction separate makes the CLI easier to test.
    """

    parser = argparse.ArgumentParser(
        prog="yini-test",
        description="Run YINI test suites against a parser adapter.",
    )

    # Select which test suite to run.
    #
    # "all" is the default because a normal full run should execute all
    # available test groups.
    #
    # "smoke" is a smaller, faster suite intended for quick sanity checks.
    parser.add_argument(
        "suite",
        nargs="?",
        choices=("all", "smoke"),
        default="all",
        help="Test suite to run. Default: all",
    )

    # Select strict mode.
    #
    # If this flag is not provided, yini-test runs in lenient mode.
    # The runner receives the normalized string value: "strict" or "lenient".
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Run cases in strict mode. Default: lenient mode",
    )

    # Root directory containing the test case structure.
    #
    # Expected example:
    #
    #   cases/
    #     smoke/
    #       lenient/
    #         valid/
    #         invalid/
    #       strict/
    #         valid/
    #         invalid/
    parser.add_argument(
        "--cases-root",
        type=Path,
        default=Path("cases"),
        help="Root directory containing test cases. Default: cases",
    )

    # Stop immediately when the first failing case is found.
    #
    # Useful during development when you want the first concrete failure
    # instead of a full summary.
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at the first failing case.",
    )

    # Adapter command used to call a parser implementation.
    #
    # Important:
    # argparse.REMAINDER means this option captures everything after --adapter.
    # Therefore, --adapter must be the final yini-test option.
    #
    # Example:
    #
    #   --adapter python ../yini-parser-python/tools/yini_parser_adapter.py --input {input} --mode {mode}
    #
    # The runner replaces:
    #
    #   {input} with the path to the current .yini test file
    #   {mode}  with either "lenient" or "strict"
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
    """
    Parse command-line arguments and run the selected test suite.

    Args:
        argv:
            Optional argument list used mainly by tests.
            If None, argparse reads from sys.argv automatically.

    Returns:
        Process exit code.

        Expected convention:
        - 0 means all selected cases passed.
        - Non-zero means at least one case failed or execution could not continue.
    """

    parser = build_parser()
    args = parser.parse_args(argv)

    # This is mostly defensive because --adapter is already marked as required.
    # It also catches the case where the user writes "--adapter" without an
    # actual adapter command after it.
    if not args.adapter:
        parser.error("--adapter requires a command")

    # Convert the boolean CLI flag into the explicit mode string expected
    # by the runner layer.
    mode = "strict" if args.strict else "lenient"

    # Delegate actual work to the runner.
    #
    # The CLI should not know how cases are discovered, how adapters are
    # executed, or how results are compared. That logic belongs in runner.py.
    return run_suite(
        suite=args.suite,
        mode=mode,
        cases_root=args.cases_root,
        adapter_tokens=args.adapter,
        fail_fast=args.fail_fast,
    )
