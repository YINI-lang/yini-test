"""
Adapter execution helpers for yini_test.
"""

# src/yini_test/adapters.py
from __future__ import annotations

from pathlib import Path
import json
import subprocess
from typing import Any

from yini_test.models import AdapterResult
from yini_test.utils.executables import resolve_executable


def render_adapter_command(
    adapter_tokens: list[str],
    input_path: Path,
    mode: str,
) -> list[str]:
    """
    Replace placeholders in adapter command tokens.

    Supported placeholders:
    - {input}
    - {mode}
    """

    if not adapter_tokens:
        raise ValueError("Adapter command is empty.")

    return [
        token.format(input=str(input_path), mode=mode)
        for token in adapter_tokens
    ]


def run_adapter_raw(
    adapter_tokens: list[str],
    input_path: Path,
    mode: str,
) -> AdapterResult:
    """
    Run the adapter and return raw stdout, stderr, and return code.
    """

    command = render_adapter_command(
        adapter_tokens=adapter_tokens,
        input_path=input_path,
        mode=mode,
    )

    command[0] = resolve_executable(command[0])

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Adapter timed out for case: {input_path.name}\n"
            f"Command: {' '.join(command)}\n"
            "Hint: The adapter may be waiting for interactive input, "
            "or the parser process may not be exiting."
        ) from exc

    return AdapterResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )


def run_adapter(
    adapter_tokens: list[str],
    input_path: Path,
    mode: str,
) -> Any:
    """
    Run the adapter for a valid case and return parsed JSON output.

    Raises RuntimeError if the adapter:
    - exits with non-zero status
    - prints no output
    - prints invalid JSON
    """

    adapter_result = run_adapter_raw(
        adapter_tokens=adapter_tokens,
        input_path=input_path,
        mode=mode,
    )

    if adapter_result.returncode != 0:
        stderr = adapter_result.stderr.strip()
        stdout = adapter_result.stdout.strip()
        details = stderr or stdout or "No error output."

        command = render_adapter_command(
            adapter_tokens=adapter_tokens,
            input_path=input_path,
            mode=mode,
        )
        command[0] = resolve_executable(command[0])

        raise RuntimeError(
            f"Adapter failed for valid case: {input_path.name}\n"
            f"Command: {' '.join(command)}\n"
            f"Details: {details}"
        )

    return parse_adapter_stdout_json(
        adapter_result.stdout,
        case_name=input_path.name,
    )


def parse_adapter_stdout_json(stdout: str, case_name: str) -> Any:
    """
    Parse adapter stdout as JSON.
    """

    output = stdout.strip()

    if not output:
        raise RuntimeError(
            f"Adapter produced no JSON output for case: {case_name}"
        )

    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Adapter output was not valid JSON for case: {case_name}\n"
            f"Error: {exc}\n"
            f"Output:\n{output}"
        ) from exc
