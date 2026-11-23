# Port python-titlecase to Go

## Background
This repository currently contains the Python package `python-titlecase` (version 2.4.1), which converts text to title case following English typographic conventions, handling small words, punctuation, abbreviations, acronyms, apostrophes, hyphenated compounds, slash-separated phrases, and Unicode characters.

## Task Objective
Reimplement the behavior of Python's `titlecase()` function as a standalone Go CLI application directly in `/workspace/repo`.

The Go program must read UTF-8 encoded text from standard input (`stdin`) line by line, process each line through the title-casing algorithm, and print the resulting title-cased string to standard output (`stdout`) followed by a newline (`\n`).

## Hard Requirements
1. **Module & Package**: Create a valid `go.mod` in the repository root (`/workspace/repo`) and write a Go application (`package main`).
2. **Build**: The project must successfully compile with `go build ./...` without errors.
3. **Dependencies**: Use **only** the Go standard library. Third-party Go dependencies, external modules, and `cgo` are strictly forbidden.
4. **No Python Files**: All `.py` source files and Python cache directories (`__pycache__`, `*.pyc`, `*.egg-info`) must be completely removed from the workspace. The final application must run purely on the Go runtime without requiring Python.
5. **Line Processing**:
   - Every input line corresponds to exactly one output line.
   - Blank and empty lines must be preserved as empty lines.
   - Do not emit carriage returns (`\r`). Always terminate output lines with `\n`.
6. **Byte-for-Byte Behavioral Compatibility**:
   - The output for every line must match the output of the original Python `titlecase(line)` implementation byte-for-byte.
   - All edge cases must be handled according to the reference Python implementation (including small words, first/last word capitalization, subphrase capitalization after punctuation, contractions, hyphenated words, slash-separated words, honorifics, Mc/Mac names, and uppercase acronyms).

## Non-Functional Scope
Execution speed, memory usage, and error message wording are not evaluated.

## Grading
Your solution will be evaluated automatically by an independent verifier that checks compilation (`go build ./...`), confirms that no `.py` files remain in the workspace, and evaluates behavioral correctness across a comprehensive suite of hidden test cases.
