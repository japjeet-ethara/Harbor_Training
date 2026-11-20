# Task Hardening Report — Rucchika Kapoor / titlecase-go

## 1. Target and Reported Attacks

- **Task:** `RucchikaKapoor/titlecase-go`
- **Baseline cited in the supplied attack report:** `4aa4d0d827bcd61a0b202a5af2b862967b703e7c`
- **Hardening implementation:** commit `a102cb9` on `training-3`

The supplied report demonstrated that an empty/echo Go program earned `0.3333` from
structural checks and that a program reading `/tests/data/hidden_expected.txt` earned
`1.0`. Its embedded-Python attempt did not pass the behavior check.

## 2. Controls Added

### Verifier and scoring

- `environment_mode` is now `separate`, and the verifier has no network access.
- Build and no-Python checks are eligibility requirements, not independently rewarded
criteria.
- A behavior score below `0.20` earns no reward.
- The behavior comparator requires the exact expected number of output records. Missing
or extra records receive no behavior credit; matching records are compared as bytes.

### Runtime isolation

The verifier builds the submitted Go program, places only that executable in a fresh
chroot, and runs it as UID/GID `65534:65534` with supplementary groups cleared. The
process receives test input through stdin, has an empty environment, and inherits no
extra file descriptors. It cannot see `/tests`, the answer key, the reference source,
or an interpreter in its filesystem.

The run is bounded by a timeout and limits on CPU time, process count, open files,
core dumps, and stdout/stderr file size.

### Exam suite

The kit-based generator in [`tests/gen.py`](./tests/gen.py) uses
[`tools/make_pool.py`](./tools/make_pool.py) and
[`tools/freeze_answers.py`](./tools/freeze_answers.py) to generate varied inputs and
retain only outputs stable under two independent Python hash seeds. The committed
fixtures contain 2,000 visible cases and 100,000 hidden cases. The generation run
retained all 102,000 cases as stable.

## 3. Verification Evidence

| Attack or check | Result |
|---|---|
| Read `/tests/data/hidden_expected.txt` from the submitted Go program | The path was absent inside the chroot; behavior and reward were `0.0`. |
| Build and echo input without titlecasing | Behavior was `0.01442` from unchanged records; the 20% gate made reward `0.0`. |
| Harbor task lint | Passed. |
| Python syntax checks for the grader and fixture tools | Passed. |
| Hidden fixture record counts | 100,000 inputs and 100,000 expected outputs. |

The attack replays used the local `titlecase-go-verifier:local` Docker image and the
task's actual grader. No full Harbor agent/oracle trial was run for this hardening.

## 4. Scope

These controls address the reported file-read and structural-credit attacks and
restrict the submitted process. They do not prove that every possible future attack
or platform vulnerability is impossible.
