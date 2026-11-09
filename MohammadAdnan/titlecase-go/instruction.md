# Titlecase in Go

## What the repository is

This repository is the MIT-licensed Python package from https://github.com/ppannuto/python-titlecase at commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (2024-04-05T22:03:59-07:00). Its `titlecase` function walks text line by line and word by word. `NOTES.md` records the rules, including the New York Times Manual of Style small-word list plus `v`, `v.`, `vs`, and `vs.`, and the handling of all-caps lines, apostrophes, `Mc` names, honorifics, dotted words, internal capitals, hyphens, slashes, consonant acronyms, first and last small words, and sub-phrases.

## What to build

Build a Go program whose module root and `main` package are `/workspace/repo`. The program reads the entire standard input as one text and writes the titlecased result to standard output.

## Hard rules

- Use only the Go standard library.
- No file whose name ends in `.py` may remain anywhere under `/workspace/repo`.
- `go build ./...`, run with working directory `/workspace/repo`, must exit 0.

## Behaviour

Standard output must be identical, byte for byte, to the string returned by this repository's `titlecase()` when the entire input is passed in one call with its default arguments: `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`.

With those defaults, `titlecase` splits the text on each run of one or more `\r` or `\n` characters. Both characters are line breaks, a mixed run such as `\r\n` is one break, and the characters in the run are discarded. Output line breaks are `\n`.

A run between pieces of text is only a separator, so consecutive breaks collapse and the blank line between them is omitted. A piece that still contains other characters, including spaces or tabs, is kept. A run at the start of the text yields one leading empty piece, and a run at the end yields one trailing empty piece. Further `\r` or `\n` characters in that same run do not add more empty pieces. Empty pieces are kept and joined with the other pieces by `\n`, so a leading run makes the result start with `\n` and a trailing run makes the result end with `\n`.

Empty input splits to one empty piece and the returned string is empty. Input made only of `\r` and `\n` splits to two empty pieces and the returned string is `\n`.

## Not checked

Speed, memory, and error-message wording are not graded.

## How it is graded

Hidden automatic tests score the program and can award partial credit.
