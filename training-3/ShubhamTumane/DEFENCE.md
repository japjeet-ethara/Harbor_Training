# Defence Report: `ShubhamTumane/titlecase-go`

## 1. Oracle Bug Discovery & Resolution (100,000-Title Stress Test)
Running the 100,000-title randomized suite (`seed = 1`) against our original Go oracle (`v1`)—which previously scored `1.000` on the 2,000-title suite—uncovered **46,440 wrong answers out of 100,000** (`0%` chance a random 2,000-title sample misses all bugs).

### Root Causes Found & Fixed in `solution/main.go`
1. **Consecutive Whitespace Splitting (`pySplitSpace`):** Python's `re.split(r'(\s)', line)` splits on every individual whitespace character (` `, `\t`, `\u00a0`, `\u2009`), yielding empty string tokens (`""`) between adjacent spaces. Replicating single-character whitespace splitting fixed all spacing and subphrase regressions.
2. **All-Caps Line Detection (`allCaps`):** Python evaluates `line.upper() == line` without requiring an alphabetic character, affecting punctuation/numeric tokens and single-word hyphenated lines (`X-RAY`).
3. **ASCII-Only Consonant Acronym Detection (`isAsciiConsonants`):** Python's `CONSONANTS` constant contains only ASCII consonants (`bcdfghjklmnpqrstvwxz`). Restricting acronym uppercasing to ASCII consonants prevented false uppercasing of non-ASCII words such as Cyrillic `Дом`.
4. **Unicode Word Matching (`[\p{L}\p{N}_]`):** Go's RE2 `\w` is ASCII-only, whereas Python's `re` `\w` matches Unicode letters and digits (`straße`, `École`, `αlpha`, `l‘oiseau`). Updating `capfirstRe`, `macMcRe`, `inlinePeriod`, and `matchAposSecond` to Unicode character classes eliminated all Unicode capitalization mismatches.

After applying these four fixes, `solution/main.go` achieved **`0 of 100,000` wrong answers** and **`1.0` reward** in Harbor (`jobs/2026-11-20__12-29-20`).

## 2. Hardening Against Exploit Vectors
- **Environment & Filesystem Isolation (`environment/Dockerfile`, `tests/behaviour.py`):** Removed system `python3` from the Go build container and locked `/tests/data` (`chmod 000`) while executing the untrusted binary as `nobody` so runtime file-read cheats cannot access `tests/data/answers.txt`.
- **Gated Criteria (`tests/build.py`, `tests/no_python.py`, `tests/behaviour.py`):** Coupled `build` and `no_python` criteria to `evaluate_behaviour(workspace) > 0.25`, and coupled `behaviour` to `passes_no_python_static_and_runtime` so non-functional stubs, empty binaries, simplified half-ports, and Python-wrapped binaries score `0.0`.
- **Non-Trivial Transformation Scoring (`tests/behaviour.py`):** Filtered out identity lines (`input == expected`) from the denominator while requiring exact matches on unchanged lines and strict line-count parity (`len(actual) == len(expected)`), neutralizing `echo` and extra-line exploits.
- **Anti-Python & Anti-Shell Enforcement (`tests/no_python.py`, `tests/behaviour.py`):** Blocked `.py`/`.pyc`/`.sh` files in `/workspace/repo`, blocked `titlecase` `.py`/`.pyc` artifacts in `/tmp` and `/var/tmp`, rejected `os/exec`/`syscall`/`python` imports in Go code and `python3`/`python`/`/bin/sh` strings in compiled binaries, and verified standalone binary execution under `env -i PATH=/nonexistent`.
- **RewardKit Layout Note:** `harbor-rewardkit==0.2.*` discovers criterion modules directly inside `/tests/*.py` (referenced via `rewardkit /tests` in `tests/test.sh`), so `build.py`, `no_python.py`, and `behaviour.py` reside directly under `task/tests/`.

## 3. Verification Matrix (Self-Hardening Stress Suite)

| Run Type | Job Path | Proof File | Reward | Status |
| :--- | :--- | :--- | :--- | :--- |
| Oracle (`solution/solve.sh`) | `jobs/2026-11-20__12-29-20` | `proof/oracle-reward.json` | `1.0` | Passed (`0 / 100,000` errors) |
| NOP (`-a nop`) | `jobs/2026-11-20__12-30-31` | `proof/nop-reward.json` | `0.0` | Blocked |
| Self Cheat 1 (Hidden Exam Read) | `jobs/2026-11-19__23-05-11` | `proof/self-cheats-reward.txt` | `0.0` | Blocked |
| Self Cheat 2 (Base64 Python Wrapper) | `jobs/2026-11-19__23-06-10` | `proof/self-cheats-reward.txt` | `0.0` | Blocked |
| Self Cheat 3 (Naive `strings.Title` + Stub) | `jobs/2026-11-19__23-07-14` | `proof/self-cheats-reward.txt` | `0.0` | Blocked |

## 4. Incoming Attacker Defense (`Isha-Jakhad`)
Attacker **Isha Jakhad** delivered her attack report (`proof/incoming-isha-jakhad/ATTACK.md`) and all three exploit scripts (`proof/incoming-isha-jakhad/cheat1-solve.sh`, `cheat2-solve.sh`, `cheat3-solve.sh`) targeting `ShubhamTumane/titlecase-go`. All three exploit scripts were executed verbatim against our hardened task, verified to score `0.0`, and consolidated in `proof/cheats-reward.txt`:

| Attack Experiment (`Isha-Jakhad`) | Mechanism | Unhardened Score | Reproducible Script | Hardened Job Path | Proof File | Hardened Reward | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cheat 1 — Python Inside** | Copies `/workspace/repo/titlecase` to `/tmp/titlecase-python`, deletes `.py` in repo, and invokes `python3 -c "from titlecase import cmd; cmd()"` via `os/exec` in Go. | `1.0000` (`jobs/2026-11-19__18-39-12`) | `proof/incoming-isha-jakhad/cheat1-solve.sh` | `defense_jobs/cheat1/2026-11-20__11-53-43` | `proof/isha-cheat1-reward.json` & `proof/cheats-reward.txt` | **`0.0`** | **Blocked** (Caught by `/tmp` artifact scan, `os/exec`/`python` AST/binary check, and `PATH=/nonexistent` runtime probe) |
| **Cheat 2 — Half Port** | Simplified whitespace-splitting Go titlecaser ignoring punctuation, acronyms, hyphens, and Unicode rules (`behaviour = 0.108`). | `0.7027` (`jobs/2026-11-18__22-51-25`) | `proof/incoming-isha-jakhad/cheat2-solve.sh` | `defense_jobs/cheat2/2026-11-20__11-48-52` | `proof/isha-cheat2-reward.json` & `proof/cheats-reward.txt` | **`0.0`** | **Blocked** (Failed `> 0.25` behaviour gate on `build` and `no_python`, and failed strict line/format checks) |
| **Cheat 3 — Build Trick** | Empty `func main() {}` Go binary after deleting `.py` files (`behaviour = 0.0`). | `0.6667` (`jobs/2026-11-18__22-59-14`) | `proof/incoming-isha-jakhad/cheat3-solve.sh` | `defense_jobs/cheat3/2026-11-20__11-50-21` | `proof/isha-cheat3-reward.json` & `proof/cheats-reward.txt` | **`0.0`** | **Blocked** (Zero behaviour gated `build` and `no_python` to `0.0`) |