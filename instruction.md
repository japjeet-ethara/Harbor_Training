# Task: Port python-titlecase to Go

## Repository

The directory `/workspace/repo` contains [python-titlecase](https://github.com/ppannuto/python-titlecase), a Python library that converts strings to title case following the rules of the New York Times Manual of Style. The main logic is in `titlecase/__init__.py`.

## What to Build

Write a Go program in `/workspace/repo` that reads one title per line from **stdin** and prints the titlecased result to **stdout**, one per line. The program must be a complete, buildable Go module (with `go.mod`).

## Hard Rules

1. **Go standard library only** — no third-party modules or dependencies.
2. **No Python files may remain** — delete every `.py` file anywhere under `/workspace/repo` when you are done.
3. **`go build ./...` must succeed** — the code must compile without errors.

## Behaviour

The Go program's output must match the original Python `titlecase()` function **byte for byte** for every input line. This includes:

- Small words (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v.`, `via`, `vs.`) stay lowercase unless they are the first or last word.
- After sub-phrase punctuation (`: . ; ? ! - – ‒ — ―` followed by a space), small words are capitalized.
- Words with mixed case (e.g. `iPhone`) are preserved.
- Inline periods (letters on both sides of `.`) are preserved.
- Apostrophe-second words (`d'Artagnan`, `O'Brien`) follow special capitalization rules.
- `Mc`/`Mac` prefixed names capitalize the prefix and the next letter.
- `Mr`/`Mrs`/`Ms`/`Dr` capitalize the first letter only.
- Hyphenated words titlecase each segment independently.
- Slash-separated words (but not `//` URLs) titlecase each segment.
- All-consonant words longer than 2 characters are uppercased as acronyms.
- All-caps lines are lowercased first, then titlecased (with UC initials like `A.B.` preserved).

**Important:** Go's `regexp` package does not support look-ahead, look-behind, or back-references. You must replicate those behaviours using plain string/rune logic.

## Not Checked

- Execution speed or memory usage.
- Error message wording.
- Code style or comments.

## Grading

Your solution will be graded automatically by hidden tests. Partial credit is awarded: the score is the fraction of test lines your program gets exactly right.
