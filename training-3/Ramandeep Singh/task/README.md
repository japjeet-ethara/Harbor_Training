# Ramandeep Singh — titlecase-go (hardened)

A hardened Go port of the Python `titlecase` functionality, developed as part of Day 5 of the Harbor break-and-harden training.

## 1. Task Overview

The objective is to implement title-case conversion in Go while preserving the expected behaviour of the original Python titlecase implementation.

The solution must:
- Read input titles from standard input.
- Process each input line independently.
- Print the corresponding title-cased result to standard output.
- Handle the full test dataset correctly.
- Work without depending on Python or external executables.

The implementation is located in `task/solution/solve.sh`.

## 2. Exam Dataset

The task is evaluated against a large dataset containing **100,000 titles**.

- The pool is generated using `kit/make_pool.py`.
- The generation uses a fixed seed of `1` for reproducibility.
- Expected answers are generated and frozen using `kit/answers.py`.
- The answer-generation process uses the original titlecase implementation in `re` mode, without relying on the regex module.
- The generated inputs and expected outputs are stored in the task's test data directory.

Important dataset files:

| File | Purpose |
|---|---|
| `task/tests/data/inputs.txt` | Input dataset |
| `task/tests/data/hidden_inputs.txt` | Hidden evaluation inputs |
| `task/tests/data/hidden_expected.txt` | Corresponding hidden expected outputs |

The large dataset helps evaluate correctness across a wider range of title formats instead of relying on a small collection of examples.

## 3. Grading and Evaluation

The task uses separate evaluation checks to measure solution quality.

- **Build:** Checks whether the Go solution compiles successfully.
- **No Python:** Checks that the submitted solution does not depend on Python.
- **Behaviour:** Measures the proportion of test cases whose output matches the expected output.

The behavioural evaluation uses the hidden test dataset and compares output line by line.

A successful build alone does not establish correctness. The solution must also produce the expected results across the evaluation inputs.

Refer to `task/tests/` for the actual grading scripts and criterion configuration.

## 4. Security Hardening

The original task was hardened to reduce opportunities for bypassing the intended programming challenge.

The main hardening measures include:

### Restricted execution
- The candidate Go binary is executed as an unprivileged `nobody` user.
- Hidden test data permissions are restricted.
- The candidate program is not intended to access protected test files or use privileged execution.

### Import and dependency checks
- Go dependencies are inspected using `go list -deps`.
- Imports associated with process execution, low-level system access, plugins, and unsafe operations are rejected.
- The checks specifically cover:
  - `os/exec`
  - `syscall`
  - `plugin`
  - `unsafe`

### Independent verification
The task was tested against multiple attack implementations to check whether the hardening measures prevent shortcuts such as reading expected outputs directly or bypassing the intended solution.

## 5. Attack Verification Results

The hardened task was evaluated against three cheat attempts and the original Oracle solution.

| Test | Behaviour | Build | No Python | Reward |
|---|---:|---:|---:|---:|
| Cheat 1 | 0.000 | 1.000 | 1.000 | 0.333 |
| Cheat 2 | 0.000 | 1.000 | 0.000 | 0.050 |
| Cheat 3 | 0.059 | 0.000 | 0.000 | 0.053 |
| Original Oracle | 1.000 | 1.000 | 1.000 | 1.000 |

The results show that the original Oracle solution retains full reward while the tested cheat attempts receive substantially reduced rewards.

Detailed attack analysis is available in `attack/ATTACK-VERIFICATION.md`.

## 6. Port Evaluation

The 100,000-input comparison was also used to evaluate available ports.

| Port | Incorrect Answers | Accuracy |
|---|---:|---:|
| my-oracle | 912 | 99.088% |
| MadhurJain | 0 | 100.000% |
| NehaGaur | 3,520 | 96.480% |

The comparison reports are stored in `measure/`.

These results provide an additional correctness check and help identify differences between implementations.

## 7. Supporting Files

The main supporting files are organised as follows:

| Path | Description |
|---|---|
| `task/` | Main Harbor task, solution, tests, and configuration |
| `task/solution/solve.sh` | Go solution entry point |
| `task/tests/` | Build, behaviour, and no-Python evaluation checks |
| `task/tests/data/` | Input and expected-output datasets |
| `attack/ATTACK-VERIFICATION.md` | Attack attempts and verification results |
| `kit/` | Dataset generation, answer generation, and comparison utilities |
| `measure/` | Port comparison reports |
| `HARDEN.md` | Hardening process, results, and supporting evidence |

## 8. Reproducibility and Verification

The supporting scripts in `kit/` are provided to reproduce dataset generation, answer generation, and port comparisons.

The task can be evaluated through Harbor from the training repository using:

```powershell
harbor run --path ".\Ramandeep Singh\task" --agent oracle
```

Run this command from the `training-3` directory.

For a complete review, inspect:
- `task/task.toml` for task configuration.
- `task/tests/` for evaluation logic.
- `attack/ATTACK-VERIFICATION.md` for attack verification.
- `HARDEN.md` for the full hardening record.

## 9. Final Outcome

The task combines a large-scale behavioural evaluation with execution restrictions and dependency checks.

The final verification demonstrates that:
- The intended Oracle solution passes all evaluation criteria.
- The tested cheat attempts are blocked or substantially penalised.
- The 100,000-input dataset provides a reproducible correctness benchmark.
- Supporting scripts and reports document the hardening and verification process.

This task is intended to assess both implementation correctness and resistance to evaluation bypasses.
