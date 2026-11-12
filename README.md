# Harbor Training – Go Titlecase Task

## Overview

This repository contains a Harbor benchmark task for implementing Python's `titlecase()` functionality in Go.

The objective is to reproduce the original Python implementation's output exactly while using only the Go standard library.

## Task Information

- **Task:** Titlecase – Python to Go
- **Language:** Go
- **Benchmark Framework:** Harbor
- **Implementation:** Go standard library only

## Project Structure

```text
NitinEthara/
└── titlecase-go/
    ├── baselines/
    ├── cheat/
    ├── environment/
    ├── solution/
    ├── tests/
    ├── instruction.md
    ├── task.toml
    ├── README.md
    └── NOTES.md
```

## Requirements

The implementation must:

1. Match the original Python `titlecase()` output byte-for-byte.
2. Use only the Go standard library.
3. Build successfully.
4. Remove Python files from `/workspace/repo`.
5. Pass the required Harbor benchmark evaluations.

## Running the Benchmark

Install Harbor:

```bash
uv tool install harbor
```

Run the Oracle evaluation:

```bash
harbor run -p . -a oracle
```

Run the No-op evaluation:

```bash
harbor run -p . -a nop
```

## Evaluation Results

The Oracle evaluation completed successfully with:

| Metric | Result |
|---|---:|
| Behaviour | 1.000 |
| Build | 1.000 |
| No_Python | 1.000 |
| Reward | 1.000 |

The No-op and cheat evaluations should also be run and documented separately.

## Author

**Nitin Ethara**

## Repository

[Harbor Training – GitHub](https://github.com/japjeet-ethara/Harbor_Training)
