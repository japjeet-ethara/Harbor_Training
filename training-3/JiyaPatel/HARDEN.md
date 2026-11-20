# Task Hardening Report — `JiyaPatel/task` (`titlecase-go`)

## 1. Original Weaknesses & Incoming Attack Analysis (`NiharikaMudgal`)

Before hardening, `JiyaPatel/task` exhibited structural evaluation weaknesses targeted in Niharika Mudgal's attack (`training-3/NiharikaMudgal/attack/ATTACK.md`):

1. **Deterministic Seed Overlap & Shared Verifier Access (`/tests/data/expected.txt`):** `tests/gen.py` reset `random.Random(1)` identically for visible and hidden suites, and `task.toml` did not isolate the verifier environment (`[verifier] environment_mode = "separate"`), allowing `cheat1` (`os.ReadFile("/tests/data/expected.txt")`) to read fixture files directly.
2. **Un-gated Partial Credit & Missing Cardinality Check:** `tests/behaviour.py` used `zip(exp, out)` without enforcing `len(out) == len(exp)`, and `reward.toml` awarded `1/6` each to `build` and `no_python` independently of behavioral accuracy. Consequently, `cheat2` (partial `strings.Fields` + small-word map) scored `0.4070` (`behaviour = 0.1105`) and `cheat3` (hardcoded 25-line prefix output) scored `0.3417` (`behaviour = 0.0125`).
3. **Narrow 2,000-Line Exam Blind Spots:** All three peer Go ports (Jiya's original oracle, Harshit Kumar's port, and Madhur Jain's port) scored `0` mismatches (`2000/2000`) on the original 2,000-line exam while actually failing `876` to `3,475` lines out of `105,000` edge cases (such as underscore-prefixed words like `_xkcd`/`_at`, version tokens like `v1.2`, and Turkish dotted `İ` / `ıstanbul`).

---

## 2. Hardening Changes Implemented

1. **Separate Verifier Sandbox (`task/task.toml`):**
   - Set `[verifier] environment_mode = "separate"` so `/tests` (including `hidden_inputs.txt` and `hidden_expected.txt`) is never mounted into the agent/solution container.
2. **Consolidated Single-Process Verifier with Gated & Cardinality-Checked Grading (`task/tests/verify.py`, `task/tests/test.sh`):**
   - Replaced separate check scripts (`build.py`, `no_python.py`, `behaviour.py`) with a single `verify.py` runner that builds `./...` and a standalone binary `/tmp/titlecase_bin` in an isolated workspace.
   - Enforced strict output cardinality (`len(out) == len(exp)`) before line-by-line comparison, immediately rejecting prefix-truncation exploits (`cheat3`).
   - Enforced a minimum behavioral accuracy threshold (`beh >= 0.90`, and gated `build` + `no_python` credits on `beh >= 0.95`), eliminating free `0.3333`–`0.4070` baseline rewards for stub, lookup, or naive heuristic binaries (`cheat1`, `cheat2`, `cheat3`).
   - Added AST/import and `go.mod` inspection (`go list -json ./...` + regex checks) prohibiting `os/exec`, `plugin`, `syscall`, `unsafe`, `C` (cgo), external dependencies, and residual `.py`/`.pyc` or Python source artifacts.
3. **105,000-Line Frozen Edge-Case Exam (`kit/`, `task/tests/data/`):**
   - Built `kit/make_pool.py`, `kit/answers.py`, and `kit/compare.py` generating `105,000` distinct inputs across all `titlecase` rule families (underscore-prefixed words, version numbers `v1.2`, Turkish `ıstanbul`, small words after colons/slashes/hyphens/quotes, `Mc`/`Mac` prefixes, acronyms, URLs/emails, non-breaking spaces, and Unicode punctuation).
   - Verified `0 / 105,000` mismatches against upstream Python `titlecase` (`measure/jiya_hardened_compare.txt`).
4. **Hardened Oracle Go Port (`task/solution/solve.sh`):**
   - Updated the Go standard-library `titlecase` implementation (`bufio`, `fmt`, `os`, `regexp`, `strings`, `unicode`) to handle underscore word-boundary rules, version identifiers (`v1.2`), Turkish `ı`/`İ` casing, inline apostrophes/slashes/hyphens, and `Mc`/`Mac` exceptions with `0 / 105,000` mismatches.

---

## 3. Comparative Port Measurement (Old 2,000 vs. Hardened 105,000 Exam)

| Port Tested | Old Exam (`2,000` lines) | Hardened Exam (`105,000` lines) | Primary Failure Modes Exposed |
| :--- | :---: | :---: | :--- |
| **JiyaPatel (Original Oracle)** | `0` wrong (`100%`) | `3,475` wrong (`96.69%`) | `_xkcd`/`_at` underscore prefix, `v1.2` version tokens, `ıstanbul` |
| **Harshit Kumar Port** | `0` wrong (`100%`) | `3,172` wrong (`96.98%`) | `_xkcd`/`_at` underscore prefix, `v1.2` version tokens, `ıstanbul` |
| **Madhur Jain Port** | `0` wrong (`100%`) | `876` wrong (`99.17%`) | `_xkcd`/`_at`/`_for`/`_lord` underscore prefix, `v1.2` version tokens |
| **JiyaPatel (Hardened Oracle)** | `0` wrong (`100%`) | **`0` wrong (`100.00%`)** | None (`105,000 / 105,000` exact matches) |

---

## 4. Before vs. After Verification Results

All proofs are saved in `training-3/JiyaPatel/proof/`:

| Agent / Cheat | Before Hardening | After Hardening (`verify.py`) | Status |
| :--- | :---: | :---: | :--- |
| **`oracle` (Hardened Go Port)** | `1.0000` | **`1.0000`** (`build=1.0, no_python=1.0, behaviour=1.0`) | Pass |
| **`nop` (Unmodified Repo)** | `0.0000` | **`0.0000`** (`build=0.0, no_python=0.0, behaviour=0.0`) | Blocked |
| **Niharika Cheat 1 (`os.ReadFile("/tests/data/expected.txt")`)** | `0.3417` | **`0.0000`** (`build=0.0, no_python=0.0, behaviour=0.0`) | Blocked (`< 0.2`) |
| **Niharika Cheat 2 (Partial `strings.Fields` + small-word map)** | `0.4070` | **`0.0000`** (`build=0.0, no_python=0.0, behaviour=0.0`) | Blocked (`< 0.2`) |
| **Niharika Cheat 3 (Hardcoded 25-line prefix output)** | `0.3417` | **`0.0000`** (`build=0.0, no_python=0.0, behaviour=0.0`) | Blocked (`< 0.2`) |
