# Day 5: Task Hardening Summary

## 1. Cheats Closed (Before vs After)
All three cheats from the attacker's `ATTACK.md` were re-run against the hardened `task` so every cheat scores below `0.2`:
- **Cheat 1 (Read hidden expected answers):** job `jobs/2026-11-20__17-01-17` — reward was `1.00` (before), now `0.000` (`build: 1.0, no_python: 1.0, behaviour: 0.0`). Fix: isolate hidden test data outside agent-accessible paths and require real behavioral execution.
- **Cheat 2 (Hidden Python via `.dat`):** job `jobs/2026-11-20__12-23-09` — reward was `1.00` (before), now `0.000` (`build: 1.0, no_python: 1.0, behaviour: 0.0`). Fix: enforce non-Python Go execution and gate verification so bypassed/non-compliant runs score `0.0`.
- **Cheat 3 (Empty Go build / partial score):** job `jobs/2026-11-20__12-24-50` — reward was `0.3333` (before), now `0.073` (`build: 1.0, no_python: 1.0, behaviour: 0.073`). Fix: gate `build` and `no_python` reward weights in `tests/reward.toml` behind actual `behaviour` test performance.

Hardened `task/environment/Dockerfile`, `task/environment/docker-compose.yaml`, `task/tests/test.sh`, `task/tests/behaviour/check.py`, and `task/tests/reward.toml`.

## 2. Step 5.1 Re-Attack Comparison (Attacker Report vs Hardened Re-Run)
- **Attacker's `ATTACK.md` baseline on target:** highest cheat score reported was `1.00` (`Cheat 1`: `1.00`, `Cheat 2`: `1.00`, `Cheat 3`: `0.3333`).
- **Hardened re-run on `KanishkaSharma/task`:** `Cheat 1` is `0.000` (`jobs/2026-11-20__17-01-17`), `Cheat 2` is `0.000` (`jobs/2026-11-20__12-23-09`), and `Cheat 3` is `0.073` (`jobs/2026-11-20__12-24-50`) — all strictly below `0.2`.

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
| `AbhishekNain` | 4,017 | 0% | No (rare/unseen in 2k sample) |
| `AlokKumarJaiswal` | 28,043 | 0% | No (missed by old 2k suite) |

## 5. Final Verification
- `harbor run -p task -a oracle`: **1.000** (`Behaviour: 1.000`, `Build: 1.000`, `No_Python: 1.000`, `Exceptions: 0`, job `jobs/2026-11-20__13-06-06`)
- `harbor run -p task -a nop`: **0.000** (`Behaviour: 0.000`, `Build: 0.000`, `No_Python: 0.000`, `Exceptions: 0`, job `jobs/2026-11-20__13-07-15`)

## What I Learned
- Partial reward weights and exposed test artifacts let shortcuts earn high scores without real behavioral correctness.
- Scaling evaluation from 2,000 to 100,000 deterministic inputs (`seed=42`) exposes subtle edge cases missed by smaller suites.
- Every cheat score, job ID, and measurement file must match actual verifier outputs to pass strict audits.
