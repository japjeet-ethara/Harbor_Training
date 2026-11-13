# Harbor Task: `titlecase-go`

A Harbor evaluation task that ports the MIT-licensed [`ppannuto/python-titlecase`](https://github.com/ppannuto/python-titlecase) (commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`) to a standalone Go command-line program using only the Go standard library.

The Go program reads one title per line from standard input (`stdin`) and prints the title-cased string to standard output (`stdout`), matching the original Python `titlecase()` function byte-for-byte. All Python source files are purged from `/workspace/repo` upon completion.

---

## Verification Results

The task was evaluated using Harbor with local Docker execution across Oracle, Nop, and Cheat configurations:

| Check | Agent / Mode | Command / Setup | Trials | Exceptions | Mean | Reward | Runtime |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| **Oracle** | `oracle` | `harbor run -p .\Ayush_Kr_Singh\titlecase-go -a oracle -o .\jobs --job-name oracle-check-3` | 1 | 0 | **1.000** | **1.0** | 2m 14s |
| **Nop** | `nop` | `harbor run -p .\Ayush_Kr_Singh\titlecase-go -a nop -o .\jobs --job-name nop-check` | 1 | 0 | **0.000** | **0.0** | 1m 23s |
| **Cheat** | `oracle` (swapped) | Swapped `cheat/solve.sh` into `solution/solve.sh` before running | 1 | 0 | **0.167** | **0.1667** | 2m 01s |

---

## Detailed Check Breakdown

### 1. Oracle Check (Expected Mean: 1.000, Exceptions: 0)
- **Command**:
  ```powershell
  harbor run -p .\Ayush_Kr_Singh\titlecase-go -a oracle -o .\jobs --job-name oracle-check-3
  ```
- **Outcome**:
  - `1/1` Trials completed, `0` Exceptions
  - **Mean Score**: `1.000` (Reward: `1.0`)
  - **Runtime**: `2m 14s`
  - **Result file**: `jobs\oracle-check-3\result.json`
- **Screenshot Evidence**: `Screenshot 2026-11-12 143200.png`, `Screenshot 2026-11-12 143220.png`

### 2. Nop Check (Expected Mean: 0.000, Exceptions: 0)
- **Command**:
  ```powershell
  harbor run -p .\Ayush_Kr_Singh\titlecase-go -a nop -o .\jobs --job-name nop-check
  ```
- **Outcome**:
  - `1/1` Trials completed, `0` Exceptions
  - **Mean Score**: `0.000` (Reward: `0.0`)
  - **Runtime**: `1m 23s`
  - **Result file**: `jobs\nop-check\result.json`
- **Screenshot Evidence**: `Screenshot 2026-11-12 143220.png`

### 3. Cheat Check (Expected Mean < 0.2, ~0.167)
- **Commands**:
  ```powershell
  Copy-Item .\Ayush_Kr_Singh\titlecase-go\solution\solve.sh .\Ayush_Kr_Singh\titlecase-go\solution\solve.sh.bak
  Copy-Item .\Ayush_Kr_Singh\titlecase-go\cheat\solve.sh .\Ayush_Kr_Singh\titlecase-go\solution\solve.sh
  harbor run -p .\Ayush_Kr_Singh\titlecase-go -a oracle -o .\jobs --job-name cheat-check
  Move-Item -Force .\Ayush_Kr_Singh\titlecase-go\solution\solve.sh.bak .\Ayush_Kr_Singh\titlecase-go\solution\solve.sh
  ```
- **Outcome**:
  - `1/1` Trials completed, `0` Exceptions
  - **Mean Score**: `0.167` (Reward: `0.1667`)
  - **Runtime**: `2m 01s`
  - **Result file**: `jobs\cheat-check\result.json`
- **Screenshot Evidence**: `Screenshot 2026-11-12 143232.png`

---

## Grading System & Reward Weights

The grading is automated using `harbor-rewardkit` (`tests/checks/reward.toml`) with a weighted-mean aggregation across three criteria:


| Criterion | Weight | Requirement | Description |
|---|:---:|---|---|
| `build` | 1.0 | `go build ./...` passes | Validates that a Go binary builds without errors in `/workspace/repo`. |
| `no_python` | 1.0 | No `.py` files remain & `go build` passes | Ensures all original Python files (`*.py`) were deleted and code still builds. |
| `behaviour` | 4.0 | Hidden behavior accuracy | Fraction of lines in `/tests/data/hidden_inputs.txt` matching `hidden_expected.txt` byte-for-byte. |

### Why Cheat Scores ~0.167
In the cheat run, `cheat/solve.sh` only builds the Go module without purging the existing Python files and only contains responses for the visible dataset. Therefore:
- `build` passes: $1.0$ (weight 1.0)
- `no_python` fails: $0.0$ (weight 1.0)
- `behaviour` fails on hidden set: $0.0$ (weight 4.0)
- **Total**: $\frac{1.0 \times 1.0 + 1.0 \times 0.0 + 4.0 \times 0.0}{6.0} = \frac{1}{6} \approx 0.1667$

---

## Task Structure

```text
Ayush_Kr_Singh/
├── README.md                              # Task documentation & test run summary
├── Screenshot 2026-11-12 143200.png       # Screenshot: Oracle test run & commands
├── Screenshot 2026-11-12 143220.png       # Screenshot: Oracle job info & Nop check
├── Screenshot 2026-11-12 143232.png       # Screenshot: Cheat check run & job info
└── titlecase-go/
    ├── task.toml                          # Harbor task configuration (1 CPU, 2GB RAM, 1800s timeout)
    ├── instruction.md                     # Agent prompt and functional requirements
    ├── environment/
    │   ├── Dockerfile                     # Environment container setup (golang:1.23)
    │   └── repo/                          # python-titlecase source snapshot
    ├── solution/
    │   └── solve.sh                       # Reference oracle solution (generates Go implementation)
    ├── cheat/
    │   └── solve.sh                       # Visible-only cheat implementation for verifier testing
    └── tests/
        ├── Dockerfile                     # Verifier container definition (Python 3.12 + Go)
        ├── test.sh                        # Verifier entrypoint running rewardkit
        ├── gen.py                         # Deterministic visible & hidden dataset generator
        ├── checks/
        │   ├── build.py                   # Check 1: build verification
        │   ├── no_python.py               # Check 2: no Python files remaining
        │   ├── behaviour.py               # Check 3: byte-for-byte hidden test comparison
        │   └── reward.toml                # Reward calculation configuration
        └── data/
            ├── inputs.txt                 # Visible test inputs (2,000 lines)
            ├── expected.txt               # Visible expected outputs (2,000 lines)
            ├── hidden_inputs.txt          # Hidden test inputs (2,000 lines)
            └── hidden_expected.txt        # Hidden expected outputs (2,000 lines)
```

---

## How to Run Locally

Run trials using Harbor from the parent directory:

```powershell
# Run the Oracle solution
harbor run -p .\Ayush_Kr_Singh\titlecase-go -a oracle -o .\jobs --job-name oracle-check

# Run the Nop baseline
harbor run -p .\Ayush_Kr_Singh\titlecase-go -a nop -o .\jobs --job-name nop-check

# View test results
harbor view jobs
```
