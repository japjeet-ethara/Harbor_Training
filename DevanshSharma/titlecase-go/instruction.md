# Instruction

## 1. What the repository is

This repository is [python-titlecase](https://github.com/ppannuto/python-titlecase) at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (Fri Apr 5 22:03:59 2024 -0700), under The MIT License (MIT). Its `titlecase` function title-cases text one line at a time. Small words from the New York Times Manual of Style, plus `v` and `vs`, stay lowercase except at the start or end of a line or after sub-phrase punctuation. A fully uppercase line is normalized before ordinary capitalization. Other rules cover initialisms, `d'`/`l'`/`o'` apostrophes, `Mc`/`MC` names, `Mr`/`Mrs`/`Ms`/`Dr`, words with an inline period, words that already contain a later capital, `/` and `-` compounds, consonant-only acronyms, an optional per-word callback, blank lines, and the original spacing between words.

## 2. What to build

Build a Go program in `/workspace/repo` that reads one title per line from stdin and prints the titlecased result, one per line.

## 3. Hard rules

- Use the Go standard library only.
- No `.py` files may be left anywhere in the repository.
- `go build ./...` must pass.

## 4. Behaviour

The output must match the original Python `titlecase()` byte for byte, for every input.

## 5. Not checked

Speed, memory, and error message wording are not checked.

## 6. How it is graded

Grading uses hidden automatic tests and assigns a partial score.
