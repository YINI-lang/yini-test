"""
Package entry point for running yini_test as a module.

Makes it possible to run this project as a Python module:

    python -m yini_test

It forwards execution to the main CLI function defined in cli.py.
"""

# src/yini_test/__main__.py
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
