# Task: Port Python Titlecase to Go

## 1. Repository

The original project is python-titlecase (https://github.com/ppannuto/python-titlecase), released under the MIT License at commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (2024-04-05). Its titlecase function turns text into title case. Small words come from the New York Times Manual of Style, plus vs and v: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. It also keeps uppercase initials on an all-caps line, recases apostrophe words that start with d, o, or l, capitalizes Mc names, capitalizes only the first letter of Mr, Mrs, Ms, and Dr, leaves inline periods and existing internal capitals unchanged, lowercases small words, title-cases the parts of a single slash or a hyphen separately, lowercases a remaining word on an all-caps line before capitalizing it, uppercases a consonant-only acronym longer than two letters, capitalizes any other word, capitalizes a small word at the start or end of a line and after a subphrase break, and keeps the original space characters.

## 2. What to Build

Create a Go program in `/workspace/repo` that reads one title per line from standard input and prints the titlecased result, one per line.

## 3. Hard Rules

- Use only the Go standard library.
- Do not leave any `.py` files anywhere in the repository.
- `go build ./...` must pass.

## 4. Behaviour

The Go program's output must match the original Python `titlecase()` function byte-for-byte for every input.

## 5. Not Checked

Speed, memory usage, and error message wording are not checked.

## 6. Grading

The solution is evaluated using hidden automatic tests and receives a partial score based on its correctness.