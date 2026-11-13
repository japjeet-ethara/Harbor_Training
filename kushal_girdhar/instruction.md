# Port python-titlecase to Go

## Repository

`/workspace/repo` contains the MIT-licensed python-titlecase 2.4.1 source at
commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`. Its `titlecase()` function
applies ordered rules for small words, capitalization, names, punctuation,
acronyms, compounds, and spacing. The bundled Python source is the reference.

## What to build

Create a Go module with a `main` package at `/workspace/repo`. The program takes
no arguments. It reads UTF-8 titles from stdin and writes one converted title
per input line, in order, each followed by a single `\n`.

Records contain no internal `\r`; CR is permitted only in CRLF line endings.
Split records on `\n` and remove one trailing `\r` from each record. A final
record without `\n` still produces one output line. Empty stdin produces no
output; an empty record produces an empty output line. Preserve all other
characters unless the reference conversion changes them. In particular, do not
normalize repeated spaces, tabs, or other Unicode whitespace.

## Hard rules

- Use only the Go standard library, with no third-party modules or cgo.
- `go build ./...` must succeed using the installed Go 1.23 toolchain.
- Leave no `.py` files anywhere under `/workspace/repo`.
- Implement the conversion in Go. The running program reads only stdin and
  writes its results to stdout; it must not read files, start other programs,
  or use the network.

## Behavior

For every input record, reproduce `titlecase(record)` byte for byte with default
arguments: no callback, first/last small-word handling enabled, blank-line
preservation disabled, and space normalization disabled. Process each record
independently. Do not implement the Python CLI or load an acronym wordlist.

The reference uses CPython 3.12.14 and `regex==2026.11.9`, with
`titlecase.REGEX_AVAILABLE` true. Both are installed so you can inspect and run
the reference before removing the Python sources. Case mappings and character
classes must agree with that runtime, including non-ASCII text.

## Not checked

Speed, memory usage, source style, and error-message wording are not scored.

## Grading

Hidden automatic checks award partial credit: one part for successful builds,
one part for removing Python files while still building, and four parts for the
fraction of output lines that match the reference exactly. Missing or extra
output lines reduce behavioral credit. The program runs without network access
or access to other files.
