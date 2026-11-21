# Task instructions

## What the repository is

This repository contains a Python implementation of titlecasing that converts text to title case while handling small words, phrase boundaries, apostrophe forms, names, abbreviations, and hyphenated or slash-separated words specially. It is distributed under the MIT License.

## What to build

Build a Go program in `/workspace/repo` that reads one title per line from standard input and prints the titlecased result, one per line.

## Hard rules

- Use only the Go standard library.
- Leave no `.py` files anywhere in the repository.
- `go build ./...` must pass.

## Behaviour

For every input, the output must match the original Python `titlecase()` byte for byte.

## Not checked

Speed, memory usage, and error message wording are not checked.

## How it is graded

The task is graded by hidden automatic tests. Partial credit is available.