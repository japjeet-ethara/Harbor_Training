# Day 5: Task Hardening Summary

## 1. Cheats Closed (Before vs After)
All three cheats from Shubham Tumane's `ATTACK.md` (`training-3/ShubhamTumane/attack/ATTACK.md`) were re-run against the hardened `task` so every cheat scores below `0.2`:
- **Cheat 1 (Read hidden exam directly from workspace):** job `jobs/2026-11-20__17-34-49` — reward was `1.000` before (`jobs/2026-11-19__20-47-56`), now `0.000` (`build: 1.0, no_python: 1.0, behaviour: 0.0`). Fix: isolate hidden test data outside agent-accessible paths and require real behavioral execution.
- **Cheat 2 (Embedded Python runner without `.py` extension):** job `jobs/2026-11-20__17-35-53` — reward was `0.1818` before (`jobs/2026-11-19__20-50-04`), now `0.000` (`build: 1.0, no_python: 1.0, behaviour: 0.0`). Fix: enforce non-Python Go execution and gate verification so non-compliant runs score `0.0`.
- **Cheat 3 (Visible fixture lookup + naive `strings.Title` fallback):** job `jobs/2026-11-20__17-36-58` — reward was `0.2415` before (`jobs/2026-11-19__20-51-50`), now `0.1695` (`build: 1.0, no_python: 1.0, behaviour: 0.1695`). Fix: do not expose test fixtures inside the workspace, expand to 100,000 inputs, and gate reward weights on behavior.

Hardened `task/environment/Dockerfile`, `task/environment/docker-compose.yaml`, `task/tests/test.sh`, `task/tests/behaviour/check.py`, and `task/tests/reward.toml`.

## 2. Step 5.1 Re-Attack Comparison (Attacker Report vs Hardened Re-Run)
- **Shubham Tumane's `ATTACK.md` baseline on target (`KanishkaSharma`):** highest cheat score was `1.000` (`Cheat 1`: `1.000`, `Cheat 2`: `0.1818`, `Cheat 3`: `0.2415`).
- **Hardened re-run on `KanishkaSharma/task`:** `Cheat 1` is `0.000` (`jobs/2026-11-20__17-34-49`), `Cheat 2` is `0.000` (`jobs/2026-11-20__17-35-53`), and `Cheat 3` is `0.1695` (`jobs/2026-11-20__17-36-58`) — all strictly below `0.2`.

## 3. 100,000-Input Exam (`re` Mode)
- Generated `100000` unique inputs using `kit/make_pool.py` (`count=100000`, `seed=42`).
- Froze reference answers twice using `kit/answers.py` (`PYTHONHASHSEED=1` and `2`), recorded in `kit/report.txt`:
  - `pool: 100000`
  - `kept: 100000`
  - `dropped: 0`
  - `regex: False`
- Documented `re` mode (`REGEX_AVAILABLE = False`) in `task/instruction.md`.
- Saved frozen files to `task/tests/data/hidden_inputs.txt` and `task/tests/data/hidden_expected.txt`.
- Fixed two edge cases in `task/solution/solve.sh`: consecutive spaces in `splitWords` and non-greedy `_` handling in `capfirst`.

## 4. Old Exam (2,000) vs New Exam (100,000) Measurement
Saved in `measure/` (`measure/my-oracle.txt`, `measure/AbhishekNain.txt`, `measure/AlokKumarJaiswal.txt`):

| Port | Wrong on 100k exam | Chance a random 2,000 suite misses all | Old exam caught it? |
|---|---:|---|---|
| `my-oracle` (`KanishkaSharma`) | 0 | 100% | N/A (0 errors) |
| `AbhishekNain` | 4,017 | 0% | Unverified on 2k suite (not re-run separately; 0% miss chance on 100k) |
| `AlokKumarJaiswal` | 28,043 | 0% | Unverified on 2k suite (not re-run separately; 0% miss chance on 100k) |

## 5. Final Verification
- `harbor run -p task -a oracle`: **1.000** (`Behaviour: 1.000`, `Build: 1.000`, `No_Python: 1.000`, `Exceptions: 0`, job `jobs/2026-11-20__13-06-06`)
- `harbor run -p task -a nop`: **0.000** (`Behaviour: 0.000`, `Build: 0.000`, `No_Python: 0.000`, `Exceptions: 0`, job `jobs/2026-11-20__13-07-15`)

## What I Learned
- Partial reward weights and exposed test artifacts let shortcuts earn high scores without real behavioral correctness.
- Scaling evaluation from 2,000 to 100,000 deterministic inputs (`seed=42`) exposes subtle edge cases missed by smaller suites.
- Every cheat score, job ID, and measurement file must match actual verifier outputs to pass strict audits.
