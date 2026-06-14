# tests/test_runner.py
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yini_test.adapters import render_adapter_command
from yini_test.diffing import make_diff
from yini_test.discovery import (
    discover_invalid_cases,
    discover_valid_cases,
    get_expected_json_path,
)
from yini_test.models import CaseResult, InvalidCase, ValidCase
from yini_test.runner import run_suite_matrix, _resolve_suite_names


def test_get_expected_json_path_returns_matching_json_path(tmp_path: Path) -> None:
    # Arrange.
    yini_path = tmp_path / "basic-config.yini"
    json_path = tmp_path / "basic-config.json"

    yini_path.write_text('name = "Demo"', encoding="utf-8")
    json_path.write_text('{"name": "Demo"}', encoding="utf-8")

    # Act.
    result = get_expected_json_path(yini_path)

    # Assert.
    assert result == json_path


def test_get_expected_json_path_raises_clear_error_when_json_file_is_missing(
    tmp_path: Path,
) -> None:
    # Arrange.
    yini_path = tmp_path / "missing-json.yini"
    expected_json_path = tmp_path / "missing-json.json"

    yini_path.write_text('name = "Demo"', encoding="utf-8")

    # Act.
    with pytest.raises(FileNotFoundError) as exc_info:
        get_expected_json_path(yini_path)

    # Assert.
    message = str(exc_info.value)

    assert "Expected JSON file not found for YINI case." in message
    assert f'yini_path: "{yini_path}"' in message
    assert f'expected_json_path: "{expected_json_path}"' in message
    assert "matching .json file" in message


def test_discover_valid_cases_returns_yini_json_pairs(tmp_path: Path) -> None:
    # Arrange.
    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()

    first_yini = valid_dir / "1-basic.yini"
    first_json = valid_dir / "1-basic.json"

    second_yini = valid_dir / "2-nested.yini"
    second_json = valid_dir / "2-nested.json"

    first_yini.write_text('name = "Demo"', encoding="utf-8")
    first_json.write_text(json.dumps({"name": "Demo"}), encoding="utf-8")

    second_yini.write_text('^ App\nname = "Demo"', encoding="utf-8")
    second_json.write_text(json.dumps({"App": {"name": "Demo"}}), encoding="utf-8")

    # Act.
    cases = discover_valid_cases(valid_dir)

    # Assert.
    assert cases == [
        ValidCase(yini_path=first_yini, json_path=first_json),
        ValidCase(yini_path=second_yini, json_path=second_json),
    ]


def test_discover_valid_cases_returns_empty_list_when_directory_is_missing(
    tmp_path: Path,
) -> None:
    # Arrange.
    valid_dir = tmp_path / "valid"

    # Act.
    cases = discover_valid_cases(valid_dir)

    # Assert.
    assert cases == []


def test_discover_valid_cases_raises_when_path_is_not_directory(
    tmp_path: Path,
) -> None:
    # Arrange.
    valid_dir = tmp_path / "valid"
    valid_dir.write_text("not a directory", encoding="utf-8")

    # Act.
    with pytest.raises(NotADirectoryError) as exc_info:
        discover_valid_cases(valid_dir)

    # Assert.
    assert "Valid case path is not a directory" in str(exc_info.value)


def test_discover_invalid_cases_returns_yini_files(tmp_path: Path) -> None:
    # Arrange.
    invalid_dir = tmp_path / "invalid"
    invalid_dir.mkdir()

    first_yini = invalid_dir / "1-broken.yini"
    second_yini = invalid_dir / "2-invalid-section.yini"

    first_yini.write_text("=", encoding="utf-8")
    second_yini.write_text("^^ MissingParent", encoding="utf-8")

    # Act.
    cases = discover_invalid_cases(invalid_dir)

    # Assert.
    assert cases == [
        InvalidCase(yini_path=first_yini),
        InvalidCase(yini_path=second_yini),
    ]


def test_discover_invalid_cases_returns_empty_list_when_directory_is_missing(
    tmp_path: Path,
) -> None:
    # Arrange.
    invalid_dir = tmp_path / "invalid"

    # Act.
    cases = discover_invalid_cases(invalid_dir)

    # Assert.
    assert cases == []


def test_discover_invalid_cases_raises_when_path_is_not_directory(
    tmp_path: Path,
) -> None:
    # Arrange.
    invalid_dir = tmp_path / "invalid"
    invalid_dir.write_text("not a directory", encoding="utf-8")

    # Act.
    with pytest.raises(NotADirectoryError) as exc_info:
        discover_invalid_cases(invalid_dir)

    # Assert.
    assert "Invalid case path is not a directory" in str(exc_info.value)


def test_render_adapter_command_replaces_input_and_mode_placeholders(
    tmp_path: Path,
) -> None:
    # Arrange.
    input_path = tmp_path / "basic.yini"

    adapter_tokens = [
        "python",
        "adapter.py",
        "--input",
        "{input}",
        "--mode",
        "{mode}",
    ]

    # Act.
    command = render_adapter_command(
        adapter_tokens=adapter_tokens,
        input_path=input_path,
        mode="lenient",
    )

    # Assert.
    assert command == [
        "python",
        "adapter.py",
        "--input",
        str(input_path),
        "--mode",
        "lenient",
    ]


def test_render_adapter_command_raises_when_adapter_command_is_empty(
    tmp_path: Path,
) -> None:
    # Arrange.
    input_path = tmp_path / "basic.yini"

    # Act.
    with pytest.raises(ValueError) as exc_info:
        render_adapter_command(
            adapter_tokens=[],
            input_path=input_path,
            mode="lenient",
        )

    # Assert.
    assert "Adapter command is empty." in str(exc_info.value)


def test_make_diff_contains_expected_and_actual_output() -> None:
    # Arrange.
    expected = {"name": "Demo", "enabled": True}
    actual = {"name": "Demo", "enabled": False}

    # Act.
    diff = make_diff(expected, actual)

    # Assert.
    assert "--- expected" in diff
    assert "parser output" in diff
    assert '"enabled": true' in diff
    assert '"enabled": false' in diff
    assert "Mismatched block:" in diff


def test_resolve_suite_names_for_smoke() -> None:
    # Arrange.
    suite = "smoke"

    # Act.
    result = _resolve_suite_names(suite)

    # Assert.
    assert result == ["smoke"]


def test_resolve_suite_names_for_golden() -> None:
    # Arrange.
    suite = "golden"

    # Act.
    result = _resolve_suite_names(suite)

    # Assert.
    assert result == ["golden"]


def test_resolve_suite_names_for_all() -> None:
    # Arrange.
    suite = "all"

    # Act.
    result = _resolve_suite_names(suite)

    # Assert.
    assert result == ["smoke", "golden"]


def test_resolve_suite_names_raises_for_unknown_suite() -> None:
    # Arrange.
    suite = "unknown"

    # Act.
    with pytest.raises(ValueError) as exc_info:
        _resolve_suite_names(suite)

    # Assert.
    assert "Unsupported suite" in str(exc_info.value)


def test_run_suite_matrix_runs_groups_in_suite_then_mode_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange.
    calls: list[tuple[str, str]] = []

    def fake_run_case_group(
        suite_name: str,
        mode: str,
        cases_root: Path,
        adapter_tokens: list[str],
        fail_fast: bool = False,
    ) -> list[CaseResult]:
        calls.append((suite_name, mode))
        return [
            CaseResult(
                case_path=tmp_path / f"{suite_name}-{mode}.yini",
                passed=True,
            )
        ]

    monkeypatch.setattr("yini_test.runner.run_case_group", fake_run_case_group)

    # Act.
    exit_code = run_suite_matrix(
        suite="all",
        modes=["lenient", "strict"],
        cases_root=tmp_path,
        adapter_tokens=["adapter"],
    )

    # Assert.
    output = capsys.readouterr().out

    assert exit_code == 0
    assert calls == [
        ("smoke", "lenient"),
        ("smoke", "strict"),
        ("golden", "lenient"),
        ("golden", "strict"),
    ]
    assert "Summary: 4 passed, 0 failed, 4 total" in output
