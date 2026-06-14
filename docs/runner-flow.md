# The Runner Flow

**The flow in a runner is:**
```txt
yini-test runner
  -> finds .yini case
  -> decides mode: lenient or strict
  -> calls yini_parser_adapter.py
  -> adapter calls yini-parser-python
  -> adapter prints JSON or error
  -> yini-test checks success/failure/output
```

When `--all-modes` is used, the runner executes the selected suite in lenient and strict mode and prints one combined summary. For `all --all-modes`, the order is smoke lenient, smoke strict, golden lenient, then golden strict.
