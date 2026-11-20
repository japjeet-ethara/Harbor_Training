# Titlecase in Go

## What the repository is

This repository is the MIT-licensed Python package from https://github.com/ppannuto/python-titlecase at commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (2024-04-05T22:03:59-07:00). Its `titlecase` function walks text line by line and word by word. `NOTES.md` records the rules, including the New York Times Manual of Style small-word list plus `v`, `v.`, `vs`, and `vs.`, and the handling of all-caps lines, apostrophes, `Mc` names, honorifics, dotted words, internal capitals, hyphens, slashes, consonant acronyms, first and last small words, and sub-phrases.

## What to build

Build a Go program whose module root and `main` package are `/workspace/repo`. The program reads the entire standard input as one text and writes the titlecased result to standard output.

## Hard rules

- Use only the Go standard library: `go.mod` must have no `require` lines.
- No file whose name ends in `.py` may remain anywhere under `/workspace/repo`.
- No Python of any kind: the program must not run Python, must not contain the Python
  `titlecase` source under any file name (also not embedded in the Go binary), and must not bundle
  a Python interpreter. There is no Python in the environment.
- All packages must compile: `go build ./...` and `go build .`, run with working directory
  `/workspace/repo`, must succeed (the grader writes their output to a temporary folder, not into
  the repository).
- The program is run as an unprivileged user from an empty working directory. It must work from
  there and must not depend on any file outside `/workspace/repo`.

## Behaviour

Standard output must be identical, byte for byte, to the string returned by this repository's `titlecase()` when the entire input is passed in one call with its default arguments: `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`.

**Mode: the answers come from titlecase WITHOUT the optional `regex` package**, so the module uses Python's built-in `re` and the `else:` branch of the pattern definitions in `titlecase/__init__.py` (`INLINE_PERIOD`, `UC_ELSEWHERE`, `CAPFIRST`, `APOS_SECOND`, `UC_INITIALS`). In that mode `\w` and `\s` follow Python's `re` rules for `str`: `\w` is any Unicode letter or digit or `_`, and `\s` is any character for which `str.isspace()` is true. Upper- and lower-casing follow Python's `str.upper()`, `str.lower()` and `str.capitalize()`.

With those defaults, `titlecase` splits the text on each run of one or more `\r` or `\n` characters. Both characters are line breaks, a mixed run such as `\r\n` is one break, and the characters in the run are discarded. Output line breaks are `\n`.

A run between pieces of text is only a separator, so consecutive breaks collapse and the blank line between them is omitted. A piece that still contains other characters, including spaces or tabs, is kept. A run at the start of the text yields one leading empty piece, and a run at the end yields one trailing empty piece. Further `\r` or `\n` characters in that same run do not add more empty pieces. Empty pieces are kept and joined with the other pieces by `\n`, so a leading run makes the result start with `\n` and a trailing run makes the result end with `\n`.

Empty input splits to one empty piece and the returned string is empty. Input made only of `\r` and `\n` splits to two empty pieces and the returned string is `\n`.

## Not checked

Speed, memory, and error-message wording are not graded.

## How it is graded

Hidden automatic tests score the program on a large set of titles, one per line, given as one text
on standard input. Partial credit is given only above 50% exact answers: the behaviour score is
`(share of exact answers − 0.5) / 0.5`, and 0 at or below 50%. The no-Python rule earns its point
only when the behaviour score is above 0.
