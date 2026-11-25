# Port Python titlecase to Go

## 1. What the Repository Is

This repository contains the Python `titlecase` library (`python-titlecase` by Patrick William Pannuto, licensed under the MIT License), which provides a rule-based algorithm for converting text into title case. The library processes text line by line and word by word, applying an ordered sequence of rules that handle whitespace preservation, small words derived from the New York Times Manual of Style (along with `v` and `vs`), initials, contractions and apostrophe forms, prefixes like `Mc`, honorifics like `Mr` and `Dr`, URLs and domains, internal capitalization, slash and hyphen compound words, consonant-only acronyms, and sub-phrase capitalization following punctuation markers. Full details of the rule precedence and specifications are documented in `NOTES.md`.

## 2. What to Build

Build a Go program in `/workspace/repo` that reads one title per line from standard input (`stdin`) and prints the titlecased result to standard output (`stdout`), one per line. The `main` package must be at the repository root, so that `go build .` there produces the program.

## 3. Hard Rules

- **Go standard library only**: Do not use any third-party external dependencies or packages. There is no network access, and the grader builds with `CGO_ENABLED=0`, `GOPROXY=off` and `GOTOOLCHAIN=local`.
- **A real port, not a wrapper**: The program must not start other programs or reach past the Go runtime. Imports of `os/exec`, `syscall`, `plugin`, `unsafe`, `golang.org/x/sys`, and cgo (`import "C"`) are rejected, as are `os.StartProcess`/`os.ProcAttr` and the `//go:embed`, `//go:linkname` and `//go:cgo_*` directives. The program is run as an unprivileged user that cannot execute any interpreter.
- **No Python left behind**: No `.py`, `.pyc` or other Python files, and no native objects (`.so`, `.a`, `.syso`), may be left anywhere in the repository.
- **Size limits**: At most 256 KiB of Go source in total, and no other file over 64 KiB (compiled Go executables excepted). Lookup tables of answers are not a port.
- **Build verification**: `go build ./...` must pass without errors.

## 4. Behaviour

The output must match the original Python `titlecase()` byte for byte, for every input. Refer to `NOTES.md` for the exact rules, precedence order, and edge-case handling.

The answers come from python-titlecase 2.4.1 WITHOUT the regex package (Python re mode). In that mode the `regex`-only branches in `titlecase/__init__.py` are not used: `\w` is Python's `re` word class (Unicode letters and digits, plus `_`), and `UC_ELSEWHERE` and `UC_INITIALS` match ASCII letters only (`[a-zA-Z]`, `[A-Z]`).

## 5. Not Checked

The following aspects are not evaluated:
- Execution speed
- Memory usage
- Error message wording

## 6. How It Is Graded

Grading is based on hidden automatic tests and is all-or-nothing: the score is 1 only if the build passes, the rules in section 3 hold, and the output matches on every line of a large hidden exam (100,000 titles). Otherwise the score is 0. There is no partial credit.
