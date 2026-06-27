# Tests Directory

This directory contains tests for `yini-test-suite` itself.

These files check the Python test harness, CLI, discovery logic, runner behavior, adapter command handling, diff formatting, and utility helpers.

They are not the YINI parser conformance cases that parser adapters run against.

The packaged YINI case corpus lives under:

```text
src/yini_test/cases/
```

Those case files are the inputs and expected outputs used when running `yini-test-suite` against a parser implementation.
