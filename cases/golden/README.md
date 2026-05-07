# Golden Case Fixtures

This document summarizes the general characteristics of the golden test fixtures. Golden tests are more detailed, representative test cases that cover all major YINI features and expected parser behavior.

These golden fixtures are organized into the following directory structure:
```txt
golden/<mode>/<expected>/<category>/<fixture-files...>
```

Where:
- **mode** is either `lenient` or `strict`, indicating the parser mode used, when parsing a fixture.
- **expected** is either `valid` or `invalid`, and defines whether the fixture is parsed successfully or not.
- **category** is the feature group being tested.
- **fixture-files** are the `.yini` files in that category. Each file covers a group of related cases for a specific feature type.

## Scope

Golden fixtures define stable input/output expectations for selected YINI syntax and behavior.

Golden tests SHOULD provide broad coverage of **all major** YINI features through representative cases, rather than exhaustively mapping every isolated syntax variation to its own expected result.

These fixtures aim to cover more detailed syntax sets and behavior cases of specific types of features within each category.

Yet more exhaustive and specification-level coverage should be handled by dedicated ***future*** conformance tests.

---
