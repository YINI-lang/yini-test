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
