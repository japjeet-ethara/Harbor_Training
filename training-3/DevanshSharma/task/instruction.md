# Instruction

## 1. What the repository is

This repository is [python-titlecase](https://github.com/ppannuto/python-titlecase) at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (Fri Apr 5 22:03:59 2024 -0700), under The MIT License (MIT). Its `titlecase` function title-cases text one line at a time. Small words from the New York Times Manual of Style, plus `v` and `vs`, stay lowercase except at the start or end of a line or after sub-phrase punctuation. A fully uppercase line is normalized before ordinary capitalization. Other rules cover initialisms, `d'`/`l'`/`o'` apostrophes, `Mc`/`MC` names, `Mr`/`Mrs`/`Ms`/`Dr`, words with an inline period, words that already contain a later capital, `/` and `-` compounds, consonant-only acronyms, blank lines, and the original spacing between words.

**Mode:** all graded answers come from `titlecase()` run **without** the `regex` package (stdlib `re` only).

## 2. What to build

Build a Go program in `/workspace/repo` that reads one title per line from stdin and prints the titlecased result, one per line.

The program must be the `main` package at the root of `/workspace/repo` so that `go build -o titlecase .` produces the binary.

## 3. Hard rules

- Use the Go standard library only. No third-party modules.
- No `.py` files may remain anywhere under `/workspace/repo`.
- Do not import `os/exec` or `syscall`. The program must not shell out to any external interpreter.
- `go build ./...` must pass in `/workspace/repo`.

## 4. Behaviour

For every input line, the output must be the same bytes that the original Python `titlecase()` returns, using its default arguments and **without** the `regex` package installed.

## 5. Not checked

Speed, memory, and error message wording are not checked.

## 6. How it is graded

Grading uses hidden automatic tests (100,000 inputs) and assigns a partial score. Three checks contribute: build, no Python files or interpreter shelling, and output correctness on the hidden input set.
