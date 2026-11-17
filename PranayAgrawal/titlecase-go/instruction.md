# Titlecase

## 1. What the repository is

This repository is an MIT-licensed Python implementation of `titlecase`. The function turns text into title case and lowercases a fixed list of small words — a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, and vs. — taken from the New York Times Manual of Style, plus v and vs. It also handles blank lines, original spacing, an optional per-word callback, initials on a fully uppercase line, `d'` / `o'` / `l'` forms, an `Mc` prefix, the honorifics Mr, Mrs, Ms, and Dr, words with an inline period, words that already contain an internal capital, `/` and `-` pieces, all-caps lines, all-consonant acronyms, ordinary first-letter capitalization, small words at the start or end of a line, and a small word that opens a subphrase after punctuation.

## 2. What to build

Build a Go program in `/workspace/repo`. It reads one title per line from stdin and prints the titlecased result, one per line.

## 3. Hard rules

- Use only the Go standard library.
- No `.py` files may be left anywhere in the repository.
- `go build ./...` must pass.

## 4. Behaviour

The output must match the original Python `titlecase()` byte for byte, for every input. Use the function’s default arguments. Each input line is one call, and the printed line is that call’s return value.

## 5. Not checked

Speed, memory, and error-message wording are not checked.

## 6. How it is graded

Hidden automatic tests grade the program. A partial score is possible.
