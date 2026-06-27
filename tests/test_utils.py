# tests/test_utils.py

from __future__ import annotations

import os
import shutil

from yini_test.utils.executables import resolve_executable


"""
NOTE:
By default, pytest captures print() output and only shows it when a test fails.

To see the output even when tests pass, run:
  python -m pytest -v -s
"""


def test_resolve_executable_returns_original_command_when_missing() -> None:
    # Arrange.
    command = "definitely-not-a-real-yini-test-suite-command"

    # Act.
    resolved = resolve_executable(command)

    # Debug output for manual inspection.
    print()
    print("Missing command resolution:")
    print(f"  Input command:    {command}")
    print(f"  Resolved command: {resolved}")

    # Assert.
    assert resolved == command


def test_resolve_executable_resolves_python() -> None:
    # Arrange.
    command = "python"

    # Act.
    resolved = resolve_executable(command)

    # Debug output for manual inspection.
    print()
    print("Python command resolution:")
    print(f"  Input command:    {command}")
    print(f"  shutil.which:     {shutil.which(command)}")
    print(f"  Resolved command: {resolved}")

    # Assert.
    assert resolved
    assert resolved != "definitely-not-a-real-yini-test-suite-command"


def test_resolve_executable_resolves_npx_when_available() -> None:
    # Arrange.
    command = "npx"

    # Act.
    resolved = resolve_executable(command)

    # Debug output for manual inspection.
    print()
    print("npx command resolution:")
    print(f"  Platform:         {os.name}")
    print(f"  Input command:    {command}")
    print(f"  shutil.which:     {shutil.which(command)}")
    print(f"  shutil.which cmd: {shutil.which(command + '.cmd')}")
    print(f"  Resolved command: {resolved}")

    # Assert.
    # If npx is installed, it should resolve to either npx, npx.cmd, or a full path.
    # If npx is not installed, the function should safely return the original command.
    assert resolved
