# Smoke Case Fixtures

This document summarizes the general characteristics of the smoke test fixtures. These tests are meant to be relatively quick and broad, to spot general issues quickly.

The fixtures are organized into the following directory structure:
```txt
smoke/<mode>/<expected>/<fixture-files...>
```

Where:
- **mode** is either `lenient` or `strict` parser mode used when a fixture is parsed.
- **expected** is either `valid` or `invalid`, and defines whether the fixture is parsed successfully or not.
- **fixture-files** are the `.yini` files in that directory. Each file covers some practical smoke-test feature(s).

## Scope

The smoke fixtures aim to cover a broad, practical **subset of YINI syntax and features**, though not every possible feature and variation.

More detailed and exhaustive syntax and behavior coverage should be handled by golden and/or conformance test cases.

---

## Lenient-mode Files

The set of valid lenient-mode YINI files aims to include:

- The use of both double-quoted `"` and single-quoted `'` strings.
- The set tries to include files both with the YINI directive `@yini`, and without.
- At least one member with an empty value (= implicit `null`).

---

## Strict-mode Files

Additional characteristics of the valid strict-mode YINI files, except the required strict-mode rules:

- The set includes both double-quoted `"` and single-quoted `'` strings.
- The set includes different comment styles, including `//`, `#`, and block comments.
- The set aims to include different capitalization variants of the YINI directive, such as `@yini`, `@Yini`, and `@YINI`.
- The set tries to include different capitalization variants of the document terminator, such as `/END`, `/End`, and `/end`.

Note: The strict smoke files cover a representative subset of strict-mode behavior, not every valid spelling, literal form, or edge case.
