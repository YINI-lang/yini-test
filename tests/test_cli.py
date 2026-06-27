# tests/test_cli.py
from yini_test.cli import build_parser


def test_build_parser() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "smoke",
            "--adapter",
            "python",
            "adapter.py",
            "--input",
            "{input}",
            "--mode",
            "{mode}",
        ]
    )

    assert parser.prog == "yini-test-suite"
    assert args.suite == "smoke"
    assert args.strict is False
    assert args.adapter == [
        "python",
        "adapter.py",
        "--input",
        "{input}",
        "--mode",
        "{mode}",
    ]


def test_build_parser_accepts_golden_suite() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "golden",
            "--adapter",
            "python",
            "adapter.py",
        ]
    )

    assert args.suite == "golden"
    assert args.strict is False
    assert args.all_modes is False


def test_build_parser_accepts_all_modes() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "all",
            "--all-modes",
            "--adapter",
            "python",
            "adapter.py",
        ]
    )

    assert args.suite == "all"
    assert args.all_modes is True
    assert args.strict is False
