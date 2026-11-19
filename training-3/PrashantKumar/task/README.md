# Titlecase — Python to Go

## Overview

This Harbor practice task involves converting the functionality of the original Python `titlecase` package into a Go implementation.

The objective is to implement a Go program that accepts text input line by line, applies title-case formatting, and produces output matching the original Python implementation.

## Task Details

- **Task Name:** `titlecase-go`
- **Task Folder:** `prashant1324task`
- **Original Repository:** [python-titlecase](https://github.com/ppannuto/python-titlecase)
- **Original Commit:** `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- **Implementation Language:** Go
- **Go Version:** 1.23
- **Dependencies:** Go standard library

## Project Structure

```text
prashant1324task/
├── environment/
│   ├── Dockerfile
│   └── repo/
│       └── Original Python starter files
├── python-titlecase/
│   └── Original Python reference project
├── solution/
│   ├── go.mod
│   ├── main.go
│   └── solve.sh
├── tests/
│   ├── Dockerfile
│   ├── build/
│   │   └── check.py
│   ├── behaviour/
│   │   └── check.py
│   ├── no_python/
│   │   └── check.py
│   ├── data/
│   │   ├── inputs.txt
│   │   ├── expected.txt
│   │   ├── hidden_inputs.txt
│   │   └── hidden_expected.txt
│   ├── reward.toml
│   └── test.sh
├── tools/
│   └── gen.py
├── instruction.md
├── task.toml
└── README.md
```

## Implementation Requirements

The Go implementation must:

1. Read input from standard input.
2. Process one title per line.
3. Apply title-case formatting consistent with the original Python package.
4. Print one formatted result per input line.
5. Handle punctuation, separators, capitalization, and small words correctly.
6. Use only the Go standard library.
7. Build successfully using `go build ./...`.
8. Avoid leaving Python files in the final workspace after the solution runs.

## Testing

The task includes three verification criteria:

| Criterion | Purpose |
|---|---|
| Build | Verifies that the Go implementation builds successfully. |
| Behaviour | Checks the implementation against hidden expected outputs. |
| No Python | Verifies that no Python files remain after a successful build. |

The test datasets contain:

- 2,000 visible input cases
- 2,000 hidden input cases

## Running the Harbor Trial

From the task directory, execute:

```bash
harbor trials start --path .
```

The trial runs the solution and evaluates the verification criteria.

## Verification Results

The completed Oracle trial achieved the following results:

| Criterion | Score |
|---|---:|
| Behaviour | 1.0 |
| Build | 1.0 |
| No Python | 1.0 |
| **Overall Reward** | **1.0 (100%)** |

All verification criteria passed successfully.

## Repository

The task is included in the following repository:

[Harbor_Training](https://github.com/japjeet-ethara/Harbor_Training)

Task directory:

`prashant1324task/`

## Notes

- The original Python project is retained as the reference implementation.
- The Go solution is maintained separately in the `solution/` directory.
- The dataset generator is maintained in `tools/`.
- The verifier uses the test files and datasets in `tests/`.
