# Titlecase in Go

## 1. What the repository is

This directory is a checkout of python-titlecase (https://github.com/ppannuto/python-titlecase) at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05T22:03:59-07:00). The behaviour to preserve is the `titlecase()` function in `titlecase/__init__.py` at version 2.4.1. It rewrites text into title caps, using the New York Times small-word list plus `v`, `v.`, `via`, `vs`, and `vs.`, and the rest of the rules recorded in `NOTES.md`. The project is under the MIT License, copyright (c) 2021 Patrick William Pannuto (`LICENSE.txt`).

## 2. What to build

Build a Go program in `/workspace/repo`. It reads one title per line from standard input and writes the titlecased result to standard output, one result per line. Use the default `titlecase()` arguments: no per-word callback, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`. Read the current Python implementation and `NOTES.md` before you remove any Python files.

## 3. Hard rules

- Use only the Go standard library.
- Leave no `.py` files anywhere in the repository.
- `go build ./...` must pass when run in `/workspace/repo`.
- The program must be self-contained. When graded it runs alone in an empty sandbox: no other programs (no Python, no shell), no files, no network. It must not start other programs (`os/exec`).

## 4. Behaviour

For every input, the titlecased text must match the original Python `titlecase()` result byte for byte. The expected answers come from the original titlecase WITHOUT the optional `regex` package installed.

## 5. Not checked

Speed, memory use, and the wording of error messages are not checked.

## 6. How it is graded

Hidden automatic tests grade the program on inputs you do not see. A partial score is possible, but a program that gets fewer than 80% of the hidden titles exactly right scores 0 on behaviour.
