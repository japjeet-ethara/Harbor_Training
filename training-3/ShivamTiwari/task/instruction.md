Work in `/workspace/repo`.

`/workspace/repo` contains a snapshot of `ppannuto/python-titlecase`. Build a Go
program that reproduces `titlecase(line)` from `titlecase/__init__.py`.

## Hard rules

These rules are checked *before* any criterion is scored. A single violation
makes `build`, `no_python` and `behaviour` all score zero, so the finished
program must be a genuine, self-contained Go port.

- Put a valid `go.mod` at `/workspace/repo` and a `main` package at the module
  root, so `go build -o <bin> .` produces the program.
- Go standard library only: `go.mod` must have no `require`, `replace` or
  `toolchain` entries, and there is no module cache or network at build time.
- `go build ./...` must exit 0.
- No file anywhere under `/workspace/repo` may use a foreign or binary
  extension: `.py`, `.pyc`, `.pyo`, `.pyd`, `.pyw`, `.s`, `.syso`, `.o`, `.a`,
  `.so`, `.dylib`, `.dll`, `.c`, `.h`, `.cc`, `.cp`, `.cpp`, `.cxx`, `.m`,
  `.wasm`, `.js`, `.mjs`, `.pl`, `.rb`, `.php`, `.lua`, `.class` or `.jar`.
- No symlinks (files or directories), no `vendor/` directory, and no `go.work`
  / `go.work.sum`.
- Do not ship a Python interpreter, embedded Python source or any Python
  runtime signature in a source file or in the built binary.
- Do not import `os/exec`, `syscall`, `plugin`, `unsafe`, any `net` package or
  `golang.org/x/sys`; do not use cgo, `os.StartProcess`, `exec.Command`,
  `syscall.Exec`, `syscall.ForkExec`, `syscall.RawSyscall`, `//go:embed` or
  `//go:linkname`. Imports are resolved with `go list`, so raw-string or
  escaped spellings (for example ``import `os/exec` ``) count as the path they
  name, and forbidden symbols are rejected even through an aliased import.
- Delete the original Python sources; the snapshot still contains them, and
  they are not part of the port.

The verifier runs the built binary as an unprivileged user whose Python
interpreters and standard libraries are unreadable, so copying an interpreter
into the repository does not help.

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

All three criteria first run the same structural audit described above; any
violation zeroes all of them.

- `build` (weight 1): `go build ./...` succeeds and the built binary reproduces
  at least 98% of the hidden exam.
- `no_python` (weight 1): the audit passes, the unprivileged runner cannot
  start an interpreter, and the binary reproduces at least 98% accuracy.
- `behaviour` (weight 4): fraction of the 100,000 hidden lines matching byte
  for byte. Full credit requires at least 98% overall accuracy and at least 95%
  accuracy on edge cases (apostrophes, Mc/Mac names, honorifics, acronyms,
  inline periods, slashes, hyphens, underscores, version strings, tabs,
  non-breaking spaces, Unicode, and subphrase punctuation). Below either floor
  the partial credit is scaled down to 10%.

A stub that only compiles, a lookup table, a half port, or a program that
reaches for an interpreter earns no structural credit.
