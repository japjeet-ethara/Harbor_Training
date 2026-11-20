# Day 6: Defence Notes

## 1. Proof Summary (Hardened Task)
- **Oracle:** `1.000` (`proof/oracle-reward.json`, job: `jobs/2026-11-20__13-06-06`)
- **Nop:** `0.000` (`proof/nop-reward.json`, job: `jobs/2026-11-20__13-07-15`)
- **Attacker's Cheats (Shubham Tumane):**
  - Cheat 1: `0.000` (`jobs/2026-11-20__17-01-17`)
  - Cheat 2: `0.000` (`jobs/2026-11-20__12-23-09`)
  - Cheat 3: `0.073` (`jobs/2026-11-20__12-24-50`)

## 2. Strongest Cheat (Before vs After)
- Strongest cheat (`Cheat 1` — reading hidden expected output directly): score was `1.00` before hardening, now `0.000` (`jobs/2026-11-20__17-01-17`).
- Hardened `Dockerfile`, `docker-compose.yaml`, `tests/test.sh`, `tests/behaviour/check.py`, and `tests/reward.toml` so `build` and `no_python` cannot award points without real `behaviour` score, hidden test data stays isolated, and every cheat stays below `0.2` (max `0.073`).

## 3. Exam: Before vs After
- **Old exam:** 2,000 inputs
- **New exam:** 100,000 unique inputs (`seed=42`), frozen twice (`PYTHONHASHSEED=1` and `2`, `pool: 100000`, `kept: 100000`, `dropped: 0`, `regex: False` in `kit/report.txt`), Python stdlib `re` mode (`REGEX_AVAILABLE = False`), explicitly stated in `task/instruction.md`.

| Port | Wrong on 100k exam | Chance a random 2,000 suite misses all |
|---|---:|---|
| `my-oracle` (`KanishkaSharma`) | 0 | 100% |
| `AbhishekNain` | 4,017 | 0% |
| `AlokKumarJaiswal` | 28,043 | 0% |

## 4. One Thing That Surprised Me
- Even though my own Go oracle passed the old 2,000-title exam with `1.0`, running it against the new 100,000-title pool exposed two real edge-case bugs in my port: consecutive spaces in `splitWords` and non-greedy `_` handling in `capfirst`. Fixing those bugs in `solve.sh` brought it to `0` wrong out of `100,000`.
