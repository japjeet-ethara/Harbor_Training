# Port Python titlecase to Go

## 1. What the Repository Is

This repository contains the Python `titlecase` library (`python-titlecase` by Patrick William Pannuto, licensed under the MIT License), which provides a rule-based algorithm for converting text into title case. The library processes text line by line and word by word, applying an ordered sequence of rules that handle whitespace preservation, small words derived from the New York Times Manual of Style (along with `v` and `vs`), initials, contractions and apostrophe forms, prefixes like `Mc`, honorifics like `Mr` and `Dr`, URLs and domains, internal capitalization, slash and hyphen compound words, consonant-only acronyms, and sub-phrase capitalization following punctuation markers. Full details of the rule precedence and specifications are documented in `NOTES.md`.

## 2. What to Build

Build a Go program in `/workspace/repo` that reads one title per line from standard input (`stdin`) and prints the titlecased result to standard output (`stdout`), one per line.

## 3. Hard Rules

- **Go standard library only**: Do not use any third-party external dependencies or packages.
- **No `.py` files**: No `.py` files may be left anywhere in the repository.
- **Build verification**: `go build ./...` must pass without errors.

## 4. Behaviour

The output must match the original Python `titlecase()` byte for byte, for every input. Refer to `NOTES.md` for the exact rules, precedence order, and edge-case handling.

## 5. Not Checked

The following aspects are not evaluated:
- Execution speed
- Memory usage
- Error message wording

## 6. How It Is Graded

Grading is based on hidden automatic tests, with partial score awarded for partially correct implementations.
