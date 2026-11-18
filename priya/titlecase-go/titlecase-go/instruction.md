# Titlecase in Go

## 1. What the repository is

This repository is a checkout of python-titlecase (https://github.com/ppannuto/python-titlecase) at commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167, dated 2024-04-05, under the MIT License. Its `titlecase` function turns text into Title Caps. Small words follow the New York Times Manual of Style, plus `v` and `vs`: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, and vs. The function also handles uppercase initials, apostrophes, `Mc` prefixes, the honorifics `Mr`, `Mrs`, `Ms`, and `Dr`, inline periods, existing internal capitals, slash-separated and hyphenated words, all-caps lines, long all-consonant acronyms, and small words at the start of a line, at the end of a line, and after sub-phrase punctuation. A caller may pass a callback, preserve blank lines, or normalise space characters.

## 2. What to build

Build a Go program in `/workspace/repo`. It reads one title per line from standard input and writes the titlecased result to standard output, one title per line.

## 3. Hard rules

- Use only the Go standard library.
- Do not leave any `.py` files anywhere in the repository.
- `go build ./...` must pass.

## 4. Behaviour

For every input, the output must match the original Python `titlecase()` result byte for byte.

## 5. Not checked

Speed, memory use, and the wording of error messages are not checked.

## 6. How it is graded

Hidden automatic tests grade the program. The score can be partial.
