Work in `/workspace/repo`.

`/workspace/repo` contains a snapshot of `ppannuto/python-titlecase`. Build a Go
program that reproduces `titlecase(line)` from `titlecase/__init__.py`.

## Hard rules

- Put a valid `go.mod` at `/workspace/repo` and a `main` package at the module
  root, so `go build -o <bin> .` produces the program.
- Go standard library only: `go.mod` must have no `require` entries.
- `go build ./...` must exit 0.
- No file anywhere under `/workspace/repo` has a name ending in `.py`, `.pyc`,
  `.pyo`, `.pyd`, or `.pyw`.
- Do not ship a Python interpreter or embedded Python source.
- Do not import `os/exec`, `syscall`, `plugin`, or `unsafe`; do not use cgo,
  `os.StartProcess`, `exec.Command`, or `//go:embed`.

## Behaviour

- Read stdin as UTF-8 and split it with the same rules as Python
  `str.splitlines()`.
- For each line, in order, append the UTF-8 encoding of `titlecase(line)` and
  then `\n`.
- `titlecase` is the function in `titlecase/__init__.py`, called with that one
  argument and no other arguments.
- **Mode:** the reference answers use titlecase **WITHOUT** regex
  (`REGEX_AVAILABLE = False`, standard-library `re`, no optional `regex`
  package).
- Stdout is those bytes and nothing else. The output must match the reference
  byte for byte on a hidden exam of 100,000 titles.

## How it is graded

- `build` (weight 1): `go build ./...` succeeds and the built binary reproduces
  at least 98% of the hidden exam.
- `no_python` (weight 1): no Python sources or interpreter, no embedded Python,
  no exec/embed/cgo escape hatch, and at least 98% accuracy.
- `behaviour` (weight 4): fraction of the 100,000 hidden lines matching byte
  for byte. Full credit requires at least 98% overall accuracy and at least 95%
  accuracy on edge cases (apostrophes, Mc/Mac names, honorifics, acronyms,
  inline periods, slashes, hyphens, underscores, version strings, tabs,
  non-breaking spaces, Unicode, and subphrase punctuation). Below either floor
  the partial credit is scaled down to 10%.

A stub that only compiles, a lookup table, or a program that reaches for an
interpreter earns no structural credit.
