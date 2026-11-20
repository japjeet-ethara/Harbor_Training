# Titlecase in Go

## 1. Overview
This repository contains `python-titlecase`, a Python port of John Gruber's titlecasing filter (`titlecase.pl`). The library converts English text to title case according to style conventions such as the New York Times Manual of Style, intelligently managing small words (e.g. prepositions and conjunctions), honorifics, acronyms, mixed-case words, hyphenated and slash-separated compounds, and punctuation delimiters.

## 2. Requirements
Build a Go program inside `/workspace/repo` that reads text from standard input (stdin) one title per line and prints the titlecased result to standard output (stdout), one per line.

## 3. Hard Rules
- Use only the Go standard library (no third-party dependencies).
- When completed, no `.py` files may be left anywhere in `/workspace/repo` (remove all Python files from the repository).
- Running `go build ./...` inside `/workspace/repo` must succeed without errors.

## 4. Behavior
The output of your Go program must match the original Python `titlecase()` function byte-for-byte for every input line.

## 5. Not Checked
Execution speed, memory usage, and error message wording are not checked.

## 6. Grading
Your solution is graded automatically via hidden automated tests with partial credit awarded based on build success, elimination of Python files, and output matching accuracy.
