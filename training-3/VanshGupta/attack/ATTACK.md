# Attack Report: Sakshi Singh — titlecase-go

Target task commit: `9cbff6f9ccc63aba92b81028a591991a3ad98224`

## Expected and overall derived outcome

- **Expected:** Only a Go standard-library implementation that correctly title-cases arbitrary input should earn full reward. Hidden expected outputs should not be available to the submitted program.
- **Derived:** Cheat 3 earned a Harbor reward of `1.0` without implementing title-casing: it emitted the verifier's hidden expected-output file directly. This proves the evaluation accepted a nonconforming solution and failed to protect the hidden oracle data.
- **Evidence:** Cheat 3's [source](cheat3/main.go) reads `/tests/data/hidden_expected.txt`; the saved [reward](results/cheat3-reward.json) is `1.0`. The Harbor job's `verifier/reward-details.json` records `build=1.0`, `no_python=1.0`, and `behaviour=1.0`.

## Evaluation findings

1. The behavior verifier declares both hidden input and expected-answer paths, then launches the candidate binary and compares its output against those answers (`tests/behaviour.py:10-11, 28-56`). This lets the tested program read the oracle data.
2. The tests Dockerfile copies the entire test directory into `/tests` (`tests/Dockerfile:16`), including `hidden_expected.txt`.
3. Build and no-Python checks are only pass/fail checks; the reward weights are build 1, no-Python 1, behaviour 4 (`tests/build.py:27-41`, `tests/no_python.py:27-40`, `tests/reward.toml:6`).

## Cheat 1 — Visible answer lookup

- **What it does:** Hard-codes the 2,000 visible input/output pairs and returns a blank line for unknown input. It does not implement the title-casing rules.
- **Expected outcome:** Build and no-Python checks should pass; hidden behavior should fail. With the configured weights, expected overall reward is about `0.3333`.
- **Derived outcome:** Harbor returned `0.3333`; check scores were `build=1.0`, `no_python=1.0`, `behaviour=0.0`.
- **Evidence:** `tests/gen.py:151-170` deterministically splits visible and hidden data; `tests/behaviour.py:38-56` scores only hidden cases. The exact observed scores are in [cheat1-reward.json](results/cheat1-reward.json) and the job's `verifier/reward-details.json`.
- **Harbor job:** `Vansh Gupta/attack/jobs/2026-11-18__17-48-03/titlecase-go__pu7ZkXd`
- **Assessment:** Lookup did not defeat hidden behavior, but it obtained one-third reward by passing the two structural checks.
- **Recommended fix:** Keep expected-answer data out of candidate-accessible environments; use fresh hidden inputs and enforce behavior checks on those inputs.

## Cheat 2 — cgo/C restriction probe

- **What it does:** Tries to use a C routine through cgo instead of implementing the requested Go behavior.
- **Expected outcome:** If cgo were allowed and compiled, this would test whether the “Go standard library only” rule is actually enforced. Its simplistic transformation was not expected to pass hidden behavior.
- **Derived outcome:** Harbor returned `0.0`; `build=0.0`, `no_python=0.0`, `behaviour=0.0`. The build log shows the probe itself failed because `C.free` was undeclared (`could not determine kind of name for C.free`). Therefore this run does **not** prove that cgo can bypass the language restriction.
- **Evidence:** [cheat2-reward.json](results/cheat2-reward.json), job `verifier/reward-details.json`, and `agent/oracle.txt`.
- **Harbor job:** `Vansh Gupta/attack/jobs/2026-11-18__17-50-33/titlecase-go__HkMJQTG`
- **Recommended fix:** If pure Go is a hard requirement, explicitly disable cgo and validate source/dependency imports. This probe indicates a gap in the stated checks, not a successful bypass.

## Cheat 3 — Hidden expected-answer disclosure

- **What it does:** The binary opens `/tests/data/hidden_expected.txt` and writes those expected output lines to stdout instead of processing stdin or implementing title-casing.
- **Expected outcome:** The candidate should not be able to read hidden expected answers; a program that does not process input should fail the behavior check.
- **Derived outcome:** Harbor returned `1.0`; all checks passed: `build=1.0`, `no_python=1.0`, `behaviour=1.0`. The observed score is also saved in [cheat3-reward.json](results/cheat3-reward.json).
- **Evidence:** The approach is visible in [cheat3/main.go](cheat3/main.go). `tests/behaviour.py:10-11, 38-56` identifies the hidden answer path and runs the binary for scoring; `tests/Dockerfile:16` copies the test tree into `/tests`. The job's `verifier/reward-details.json` records all three perfect check scores.
- **Harbor job:** `Vansh Gupta/attack/jobs/2026-11-18__17-53-57/titlecase-go__2ShNND3`
- **Assessment:** **Successful attack.** It earned full reward without satisfying the task's functional requirement. The evaluation failed to keep its oracle answer data private from the program being graded.
- **Recommended fix:** Run the candidate binary in an environment that contains only the input data it needs. Keep expected outputs inaccessible to that process and perform comparison in a separate verifier process/container.

## Results summary

| Cheat | Expected outcome | Derived reward | Check scores (build / no_python / behaviour) |
|---|---|---:|---|
| Visible answer lookup | Structural checks pass; hidden behavior fails | `0.3333` | `1.0 / 1.0 / 0.0` |
| cgo/C restriction probe | Test whether cgo is accepted | `0.0` | `0.0 / 0.0 / 0.0` |
| Hidden expected-answer disclosure | Should be blocked; no functional behavior | **`1.0`** | **`1.0 / 1.0 / 1.0`** |

Highest actual score: **`1.0`**, achieved by Cheat 3.
