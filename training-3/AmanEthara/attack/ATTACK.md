# Attack Report — Target: Isha Jakhad

## Target Info
- **Target Name:** Isha Jakhad
- **Target Commit SHA:** `dab8256a4b869be722e8243e470946857da2add3`
- **Target Task:** `Isha-Jakhad` (`isha/titlecase-go`)
- **Exam Environment:** `golang:1.23` with `/usr/bin/python3` preinstalled; verifier uses `harbor-rewardkit==0.2.4`

---

## Cheat 1 — Delete & Build Dummy Stub

- **Cheat name:** Delete & Build Dummy Stub
- **What it does:** Deletes all `*.py` files, removes `titlecase/` package directory, and creates a minimal `go.mod` and a dummy `main.go` that loops over stdin emitting empty lines without performing any titlecasing logic.
- **Why it is not a genuine port:** It contains zero titlecasing algorithm logic or capitalization rules. It is an empty 3-line Go stub designed solely to pass compilation and file deletion checks.
- **Actual Harbor reward and component scores:**
  - `build`: 1.0
  - `no_python`: 1.0
  - `behaviour`: 0.0
  - **Total Reward:** `0.3333`
- **Exact Harbor job folder:** `jobs/2026-11-20__06-02-48`
- **Exact target file and line evidence:**
  - `tests/reward/reward.toml:4` — `weights = { build = 1.0, no_python = 1.0, behaviour = 4.0 }` defines decoupled weights, awarding 2 out of 6 points (0.3333) unconditionally for compilation and file cleanup.
  - `tests/reward/no_python/check.py:11` — `if any(workspace.rglob("*.py")): return False` checks strictly for the presence of files ending in `.py`.
  - `tests/reward/build/check.py:10-25` — `@criterion(description="go build ./... succeeds")` awards 1.0 merely for `go build ./...` succeeding.
- **Why the exploit worked:** The reward weights in `tests/reward/reward.toml` treat `build` and `no_python` as independent additive criteria that do not require any behavioral correctness. Simply deleting all `.py` files and creating a dummy Go module passes both checks, earning 33.3% of the total score for zero implementation.
- **How the target owner could fix the weakness:** Require a passing behavioral threshold before awarding points for `build` or `no_python` (e.g. gate the criteria or multiply build/no_python scores by `behaviour > 0.2`).
- **Result file:** `attack/results/cheat1-reward.json`

---

## Cheat 2 — Cloaked Python Inside Go Wrapper

- **Cheat name:** Cloaked Python Inside Go Wrapper
- **What it does:** Preserves the original Python `titlecase/__init__.py` by copying it to `tc_runner.pytxt` with a batch stdin/stdout loop, deletes all `.py` files to satisfy the file-extension check, and writes a Go `main.go` wrapper that invokes `/usr/bin/python3 /workspace/repo/tc_runner.pytxt` via `os/exec`.
- **Why it is not a genuine port:** It writes zero Go titlecase logic. It delegates 100% of the titlecasing computation to the original Python runtime, evading the core assignment requirement to port the library to Go.
- **Actual Harbor reward and component scores:**
  - `build`: 1.0
  - `no_python`: 1.0
  - `behaviour`: 1.0
  - **Total Reward:** `1.0000`
- **Exact Harbor job folder:** `jobs/2026-11-20__06-04-28`
- **Exact target file and line evidence:**
  - `environment/Dockerfile:1` & `tests/Dockerfile:1` — `FROM golang:1.23` leaves Debian's `/usr/bin/python3` preinstalled in the container.
  - `tests/reward/no_python/check.py:11` — `if any(workspace.rglob("*.py")): return False` only searches for `*.py` file extensions on disk, completely blind to Python scripts stored under `.pytxt` or other extensions.
  - `tests/reward/behaviour/check.py:93-101` — executes the compiled Go binary without process restriction or sandboxing, allowing standard library `os/exec` to invoke `/usr/bin/python3`.
- **Why the exploit worked:** The `no_python` check only performed a static filename pattern match for `.py`. Because `/usr/bin/python3` was available inside the container and the binary was permitted to spawn subprocesses, the Go wrapper executed the exact Python titlecase code and produced 100% byte-for-byte identical outputs on all 2,000 hidden test cases.
- **How the target owner could fix the weakness:** Remove `/usr/bin/python*` from both the environment and verifier container images, restrict execution privileges (or use seccomp/apparmor) to prevent spawning unauthorized subprocesses, and inspect the compiled binary or filesystem for embedded scripts.
- **Result file:** `attack/results/cheat2-reward.json`

---

## Cheat 3 — Naive Capitalization Half-Port

- **Cheat name:** Naive Capitalization Half-Port
- **What it does:** Implements a 15-line Go program that only capitalizes the first character of each space-delimited word (`unicode.ToUpper(runes[0])` followed by `unicode.ToLower` on the rest) without implementing small words, hyphenated/slashed words, acronyms, mixed caps, apostrophe names, or subphrase rules.
- **Why it is not a genuine port:** It ignores ~90% of the titlecase specification and edge cases, using a simplistic whitespace-split capitalizer.
- **Actual Harbor reward and component scores:**
  - `build`: 1.0
  - `no_python`: 1.0
  - `behaviour`: 0.3365
  - **Total Reward:** `0.5577`
- **Exact Harbor job folder:** `jobs/2026-11-20__06-06-15`
- **Exact target file and line evidence:**
  - `tests/gen.py:109-114` — `ordinary_lower()` generates sentences consisting solely of ordinary dictionary words with single spaces where naive title-casing matches the correct output.
  - `tests/reward/behaviour/check.py:51-62` — `_line_fraction()` computes `matched / total` line fraction without weighting edge cases or penalizing naive heuristics.
  - `tests/reward/reward.toml:4` — `weights = { build = 1.0, no_python = 1.0, behaviour = 4.0 }` compounds the score with build (1.0) and no_python (1.0), yielding `(1.0 + 1.0 + 4.0 * 0.3365) / 6.0 = 0.5577`.
- **Why the exploit worked:** Over 33% of the generated hidden test cases in `tests/data/hidden_inputs.txt` (673 of 2,000 lines) were ordinary lowercase words where simple word-by-word capitalization matches the true titlecase output. Combined with the 2 build/cleanup points, the naive program earned 55.77% of the total reward.
- **How the target owner could fix the weakness:** Expand and harden the exam test cases using diverse, adversarial titles (e.g. 100,000 titles pool containing mixed caps, acronyms, small words in varied positions, punctuation, Mc/O' prefixes) so that a naive capitalizer scores near 0.
- **Result file:** `attack/results/cheat3-reward.json`

---

## Summary of Results

| Cheat | Strategy | Build | No_Python | Behaviour | Reward | Harbor Job Folder |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Cheat 1** | Delete & Build Dummy Stub | 1.000 | 1.000 | 0.000 | **0.3333** | `jobs/2026-11-20__06-02-48` |
| **Cheat 2** | Cloaked Python Inside Go Wrapper | 1.000 | 1.000 | 1.000 | **1.0000** | `jobs/2026-11-20__06-04-28` |
| **Cheat 3** | Naive Capitalization Half-Port | 1.000 | 1.000 | 0.3365 | **0.5577** | `jobs/2026-11-20__06-06-15` |

**Highest score achieved by any of the three cheats:** **1.0000** (Cheat 2 — Cloaked Python Inside Go Wrapper)
