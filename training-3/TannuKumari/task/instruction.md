# Task: Port Python Titlecase to Go

## 1. Repository

`/workspace/repo` contains python-titlecase 2.4.1 (https://github.com/ppannuto/python-titlecase), MIT License, commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (2024-04-05). Its `titlecase()` function in `titlecase/__init__.py` turns text into title case. Small words come from the New York Times Manual of Style, plus vs and v: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. It also keeps uppercase initials on an all-caps line, recases apostrophe words that start with d, o, or l, capitalizes Mc names, capitalizes only the first letter of Mr, Mrs, Ms, and Dr, leaves inline periods and existing internal capitals unchanged, lowercases small words, title-cases the parts of a single slash or a hyphen separately, lowercases a remaining word on an all-caps line before capitalizing it, uppercases a consonant-only acronym longer than two letters, capitalizes any other word, capitalizes a small word at the start or end of a line and after a subphrase break, and keeps the original space characters.

Python 3 is installed, so you can run the original, for example:

    cd /workspace/repo && python3 -c "from titlecase import titlecase; print(titlecase('the lord of the rings'))"

## 2. Mode

The expected answers come from the original `titlecase(line)` with its default options, running **without the third-party `regex` module** (`REGEX_AVAILABLE` is `False`, so the standard library `re` fallback patterns are used). This is exactly what the installed `python3` does.

## 3. What to Build

A Go program whose module root is `/workspace/repo` (`go.mod` and `package main` in that folder). It reads standard input one title per line and writes the titlecased result to standard output, one result per line, each ending with a newline. Input is UTF-8 and can contain Unicode letters, punctuation, tabs and other unusual space characters. The program takes no arguments.

## 4. Hard Rules

- Use only the Go standard library: no `require` or `replace` in `go.mod`, no `vendor` folder, no cgo.
- No `.py` file may remain anywhere in `/workspace/repo`.
- `go build ./...` in `/workspace/repo` must pass.
- The program must be self-contained. It is run alone, as an unprivileged user, in an empty folder with no Python, no other files and no network.
- The Go source files together must stay under 1 MB.

If any hard rule is broken, the score is 0.

## 5. Behaviour

For every input line, the output line must match what the original `titlecase(line)` returns in the mode above, byte for byte.

## 6. Not Checked

Speed, memory usage, error message wording, tests and code style are not checked.

## 7. Grading

The score is the share of 100,000 hidden input lines whose output matches exactly, from 0 to 1. Building and removing Python earn no points on their own.
