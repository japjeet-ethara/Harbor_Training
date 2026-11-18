# Port python-titlecase to Go

## The repository

`/workspace/repo` contains **python-titlecase** (version 2.4.1, MIT licence), a
Python library that turns a string into a headline-style title, following the
New York Times Manual of Style rules from John Gruber's original Perl script.
For example it keeps small words such as "of" and "the" lower-case inside a
title, keeps words like "iPhone" or "U.S.A." as they are, handles names such as
"McDonald" and "O'Neil", and leaves URLs alone. The logic is the `titlecase()`
function in `titlecase/__init__.py`.

## What to build

Replace the Python library with a Go program in `/workspace/repo`.

- The program's `main` package must be at the root of `/workspace/repo`, with a
  `go.mod` there, so that `go build -o <binary> .` run in `/workspace/repo`
  produces the program.
- The program reads lines from standard input. Each line ends with `\n`. For
  each line it writes the titlecased line to standard output, followed by
  `\n`, in the same order. One input line gives exactly one output line.

## Hard rules

1. Go standard library only. The build happens offline with Go 1.23, so
   `go.mod` must not need third-party modules or a newer Go toolchain.
2. When you finish, no `.py` file may be left anywhere under `/workspace/repo`.
3. `go build ./...` run in `/workspace/repo` must succeed.

## Required behaviour

For every input line, the output must be **byte for byte** the same as what
the original Python code returns for `titlecase(line)` called with its default
arguments (no callback). In particular:

- The reference is the code path the module takes when the third-party
  `regex` package is **not** installed, that is, the `import re as regex`
  fallback, with the regular expressions in the `else:` branch near the top of
  `titlecase/__init__.py`. Python 3 `re` semantics apply (for example `\w`,
  `\s` and `\b` are Unicode-aware, and `re.I` is case-insensitive matching).
- Input lines are valid UTF-8 and contain no `\r` or `\n`. Besides printable
  ASCII they may contain tabs, no-break spaces, Latin letters with accents
  (such as é, ü, ñ, Ç), and typographic quotes and dashes
  (`“ ” ‘ ’ – ‒ — ―`). A line may be empty or only whitespace.
- All whitespace must be kept exactly as it is in the input.

Do not rely on a Python interpreter being available. Port the logic by
reading the source. Go's `regexp` package has no look-ahead, look-behind or
back-references and differs from Python's `re` in other ways, so the patterns
cannot simply be copied.

## Not checked

Speed, memory use, code style, and the wording of any error messages.

## How it is graded

Hidden automatic tests build your program and run it on many titles. The score
is partial: it combines whether the build passes, whether any `.py` file is
left, and the share of lines whose output exactly matches the reference.
