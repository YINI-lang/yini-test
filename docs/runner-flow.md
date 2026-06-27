# The Runner Flow

**The flow in a runner is:**
```txt
yini-test-suite runner
  -> finds .yini case
  -> decides mode: lenient or strict
  -> calls yini_parser_adapter.py
  -> adapter calls yini-parser-python
  -> adapter prints JSON or error
  -> yini-test-suite checks success/failure/output
```

When `--all-modes` is used, the runner executes the selected suite in lenient and strict mode and prints one combined summary. For `all --all-modes`, the order is smoke lenient, smoke strict, golden lenient, then golden strict.

At the end of a run, the runner prints a terminal summary table showing the adapter name, each suite/mode group, passed/failed/total counts, and duration. It also prints the one-line summary in this form:
```txt
Summary: 169 passed, 4 failed, 173 total, duration 29.93 s
```

If any group fails, the summary includes a `Failed groups:` section with one line per failing suite/mode group.
