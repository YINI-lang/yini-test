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
