# AahanTask1 – Go Implementation

A Go-based implementation of the Title Case task, designed to work within the Harbor training and evaluation environment.

## Overview

This project contains a Go implementation, supporting scripts, test cases, and environment configuration for the Title Case task.

The repository includes:
- A Go-based solution.
- A reference implementation for comparison.
- Test scripts and test data.
- A Docker-based environment.
- A separate cheat implementation for evaluation testing.

## Project Structure

```text
AahanTask1/
├── .gitignore
├── README.md
├── NOTES.md
├── instruction.md
├── task.toml
│
├── environment/
│   ├── .dockerignore
│   ├── Dockerfile
│   └── repo/                  # Embedded Git repository
│
├── solution/
│   ├── main.go                # Main Go implementation
│   └── solve.sh               # Solution execution script
│
├── cheat/
│   ├── main.go
│   └── solve.sh               # Cheat implementation
│
├── tests/
│   ├── check.py               # Test validation
│   ├── gen.py                 # Test data generator
│   ├── test.sh                # Test execution script
│   └── data/
│       ├── expected.txt
│       ├── hidden_expected.txt
│       ├── hidden_inputs.txt
│       └── inputs.txt
│
└── screenshots/
    ├── NOP.png.png
    ├── cheat.png.png
    └── oracle.png.png
```

## Components

### 1. Solution

The `solution/` directory contains the primary Go implementation.

- `main.go` contains the Go solution.
- `solve.sh` provides the execution script.

### 2. Cheat Implementation

The `cheat/` directory contains a separate implementation used to test the evaluation system against a potentially non-generalizable solution.

### 3. Test Suite

The `tests/` directory contains the testing infrastructure.

| File | Description |
|---|---|
| `check.py` | Test validation script |
| `gen.py` | Generates test data |
| `test.sh` | Runs the test workflow |
| `inputs.txt` | Visible test inputs |
| `expected.txt` | Expected outputs |
| `hidden_inputs.txt` | Hidden test inputs |
| `hidden_expected.txt` | Expected hidden test outputs |

### 4. Environment

The `environment/` directory contains the Docker configuration and embedded repository used by the project.

- `Dockerfile` defines the environment.
- `.dockerignore` controls which files are excluded from the Docker build context.
- `repo/` contains an embedded Git repository.

## Local Development

### Build the Docker Environment

From the project root:

```bash
docker build -t aahan-task1-env ./environment
```

### Run the Test Script

```bash
bash tests/test.sh
```

### Execute the Go Solution

```bash
go run solution/main.go
```

Alternatively, use the provided execution script:

```bash
bash solution/solve.sh
```

## Evaluation

The repository includes three important evaluation components:

- **Solution:** The primary Go implementation.
- **NOP:** A baseline representing an implementation that does not solve the task.
- **Cheat:** An alternative implementation used to test the robustness of the evaluation process.

Screenshots of the evaluation runs are available in the `screenshots/` directory.

## Technologies Used

- Go
- Python
- Docker
- Bash
- Git
- Harbor Training Environment

## Notes

- Task configuration is maintained in `task.toml`.
- Agent-facing instructions are available in `instruction.md`.
- Additional project information and development notes are available in `NOTES.md`.

