# Titlecase Go Port

## Repository
`/workspace/repo` contains `python-titlecase` (https://github.com/ppannuto/python-titlecase), a Python library implementing John Gruber's title-casing rules.

## Task
Build a Go program in `/workspace/repo` (with a valid `go.mod`) that reads one title per line from `stdin` and prints the titlecased result to `stdout`, one line per input line.

## Reference Mode
- **Regex Engine Mode:** Python standard-library `re` mode (`REGEX_AVAILABLE = False` in `titlecase/__init__.py`, without the optional third-party `regex` package installed).
- Reference answers are frozen across two independent runs (`PYTHONHASHSEED=1` and `PYTHONHASHSEED=2`) against `titlecase/__init__.py` in `stdlib re` mode.

## Hard Rules
- Use the Go standard library only (no external third-party Go modules in `go.mod`).
- Do not invoke external processes, shells, interpreters, or CGo (`os/exec`, `os.StartProcess`, `syscall`, `plugin`, `unsafe`, or `import "C"` are strictly forbidden).
- Remove all `.py` files anywhere under `/workspace/repo` when finished.
- `go build ./...` in `/workspace/repo` must pass with exit code 0.
- The compiled binary or `go run .` in `/workspace/repo` must accept lines on `stdin` and output titlecased lines on `stdout`.

## Behaviour
- Output must match the original Python `titlecase()` function (`stdlib re` mode) byte-for-byte for every input line, preserving all Unicode whitespace characters (`\t`, `\xa0`, `\u2009`, etc.), punctuation, small-word rules, inline uppercase/acronyms, URLs/emails, hyphenated and slash-separated compounds, apostrophes/contractions (`d'`, `o'`, `l'`, curly `'`), `Mac`/`Mc` prefixes, `Mr`/`Mrs`/`Ms`/`Dr`, and all-consonant acronyms.

## Not Checked
- Execution speed, memory usage, or stderr error message wording.

## Grading
- Graded automatically by hidden tests using gated weighted checks across build success, strict no-Python / stdlib-only compliance, and exact line-by-line output accuracy on a 105,000-line hidden test suite.
