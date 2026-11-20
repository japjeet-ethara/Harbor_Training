# Day 5: Task Hardening Summary

## 1. Cheats Closed
All three cheats from the attacker's `ATTACK.md` were re-run and closed so every cheat scores below `0.2`:
- **Cheat 1:** `0.000`
- **Cheat 2:** `0.000`
- **Cheat 3:** `0.073`

Hardened `task/environment/Dockerfile`, `task/environment/docker-compose.yaml`, `task/tests/test.sh`, `task/tests/behaviour/check.py`, and `task/tests/reward.toml`.

## 2. 100,000-Input Exam (`re` Mode)
- Generated 100,000 unique inputs using `kit/make_pool.py` (`count=100000`, `seed=42`).
- Froze reference answers twice using `kit/answers.py` (`PYTHONHASHSEED=1` and `2`):
  - Pool inputs: `100000`
  - Kept (stable): `100000`
  - Dropped (unstable): `0`
  - Mode: Python stdlib `re` (`REGEX_AVAILABLE = False`), documented in `task/instruction.md`.
- Saved frozen files to `task/tests/data/hidden_inputs.txt` and `task/tests/data/hidden_expected.txt`.
- Fixed two edge cases uncovered in `task/solution/solve.sh` (consecutive spaces in `splitWords` and non-greedy `_` handling in `capfirst`).

## 3. Old Exam (2,000) vs New Exam (100,000) Measurement
Saved in `measure/`:
- `measure/KanishkaSharma.txt`: `0` wrong of `100000` (100% chance a random 2,000 suite sees none)
- `measure/AbhishekNain.txt`: `4017` wrong of `100000` (0% chance a random 2,000 suite sees none)
- `measure/AlokKumarJaiswal.txt`: `28043` wrong of `100000` (0% chance a random 2,000 suite sees none)

## 4. Final Verification
- `harbor run -p task -a oracle`: **1.000** (`Behaviour: 1.000`, `Build: 1.000`, `No_Python: 1.000`, `Exceptions: 0`)
- `harbor run -p task -a nop`: **0.000** (`Exceptions: 0`)
