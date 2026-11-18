# Harbor Training – Go Titlecase Task

## Overview
This repository contains a Harbor benchmark task for implementing Python's `titlecase()` functionality in Go.
The objective is to reproduce the original Python implementation's output exactly while using only the Go standard library.

## Task Information
- Task: Titlecase – Python to Go
- Language: Go
- Benchmark Framework: Harbor
- Implementation: Go standard library only
- Source project: python-titlecase 2.4.1 (MIT), commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167

## Project Structure
```
Aaditya-Markande-<ID>/
└── titlecase-go/
    ├── cheat/
    ├── environment/
    ├── scripts/
    ├── screenshots/
    ├── solution/
    ├── tests/
    ├── instruction.md
    ├── task.toml
    ├── README.md
    └── NOTES.md
```

## Requirements
The implementation must:
- Match the original Python `titlecase()` output byte-for-byte.
- Use only the Go standard library.
- Build successfully.
- Remove Python files from /workspace/repo.

## Running the Benchmark
```
uv tool install harbor
harbor run -p . -a oracle
harbor run -p . -a nop
```

## Evaluation Results
| Run | Behaviour | Build | No_Python | Reward |
|---|---|---|---|---|
| Oracle | 1.000 | 1.000 | 1.000 | **1.000** |
| Nop | 0.000 | 0.000 | 0.000 | **0.000** |
| Cheat | 0.017 | 1.000 | 0.000 | **0.178** |

The cheat (cheat/solve.sh) hard-codes the visible answers only and leaves the .py files in place; it is run through Harbor's oracle agent by copying it over solution/solve.sh, which is why that job shows agent "oracle". Screenshots are in screenshots/.

## Notes
- Most-missed issue: the first Go port compiled to a module named "titlecase", which collided with the leftover empty titlecase/ folder after the .py files were deleted (fixed by renaming the module and removing empty folders); on the 4000 generated lines no titlecase rule differed from Python.
- Harder version: add non-ASCII input (e.g. é, ß, İ), because Python's \w and str.upper()/capitalize() are Unicode-aware while Go's regexp \w is ASCII-only, and add digit/underscore cases around the Mc/Mac rule.
- The verifier is a plain bash test.sh using the same weights as the PDF (build 1, no_python 1, behaviour 4, weighted mean) instead of Reward Kit.

## Author
Aaditya Markande
