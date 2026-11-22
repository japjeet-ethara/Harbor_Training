# Title case in Go

## 1. What the repository is

This tree is [python-titlecase](https://github.com/ppannuto/python-titlecase) at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05T22:03:59-07:00), under the MIT License. Its `titlecase()` function title-cases a string by applying the ordered rules in `NOTES.md`: line-break handling, spacing, an optional per-word callback, names and honorifics, dotted and mixed-case words, a fixed small-word list, slash- and hyphen-separated parts, all-caps lines, consonant-only acronyms, and capitalization of whatever remains, including small words at the ends of a line and after a subphrase mark.

## 2. What to build

Build a Go program in `/workspace/repo`. It reads one title per line from stdin and prints the titlecased result. Each input line must produce exactly one corresponding output line.

## 3. Hard rules

- Use the Go standard library only.
- No `.py` files may be left anywhere in the repository.
- Implement the titlecasing in Go; do not launch another process or interpreter.
- Do not import `os/exec`, `syscall`, `unsafe`, `plugin`, or `runtime/cgo`,
  call `os.StartProcess`, or use `go:linkname`.
- `go build ./...` must pass.

## 4. Behaviour

The output must match the original Python `titlecase()` byte for byte, for every input. Each input line must produce exactly one corresponding output line.

## 5. Reference mode and exam

The graded exam contains 100,000 unique single-line inputs. Its answers were
frozen twice from the original Python `titlecase()` implementation using Python's
standard-library `re` (`REGEX_AVAILABLE = False`); the two freezes matched.
The optional third-party `regex` package is not part of the reference environment.

The 2,000-line practice set is separate from the graded exam.

## 6. Not checked

Speed, memory, and error-message wording are not checked.

## 7. How it is graded

The behavior score is the fraction of exam answers matched byte for byte.
Build, no-Python, and no-subprocess rules are gates, not independent points:
the behavior score is zero if any hard rule fails.
