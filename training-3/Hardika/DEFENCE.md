# Day 6 — Defence notes (Hardika)

Task: `training-3/Hardika/task/` (titlecase, Python → Go). Attacker: Sneha Sadhukhan.

## 1. Strongest cheat: before and after

**Sneha's cheat 2 (partial port)** was the strongest attack: it ports only the easy rules and deletes the Python files.

| | Reward | Behaviour | Build | No_python | Job folder |
|---|---|---|---|---|---|
| Before (Sneha's run, old task) | **0.3597** | 0.0395 | 1 | 1 | `2026-11-19__14-53-28` |
| After (my run, hardened task) | **0.0905** | 0.1357 | 0 | 0 | `2026-11-23__09-45-25` |

**Why it worked:** `tests/grade.py` paid `build` and `no_python` (2 of 6 points) as soon as the code compiled, even with almost no correct titles.

**The fix:** `build` and `no_python` are now paid only when `behaviour >= 0.5` (`GATE` in `tests/grade.py`). Cheats 1 and 3 dropped from 0.3333 to 0.0087 for the same reason.

## 2. Exam: before and after

Old exam: 2,000 hidden titles. New exam: 100,000 titles from `kit/make_pool.py 100000 1`. The answers were frozen twice with the regex package (0 dropped). The mode is stated in `instruction.md`.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---|---|---|
| my oracle | 0 of 100,000 | n/a (0 of 2,000) | n/a |
| Madhur Jain | 3,053 | yes (187 of 2,000) | 0% |
| Kushal Soni | 3,053 | yes (296 of 2,000) | 0% |

Proofs (Harbor 0.26.0): oracle **1.0** (`2026-11-23__09-31-53`), nop **0.0** (`2026-11-23__09-42-42`), all three cheats **below 0.2**.

## 3. What surprised me

- **The bigger exam made a cheat stronger.** On the 100k pool, cheat 2 gets 13.6% right instead of 4%, because the pool has more plain words. Without the gate its reward would have gone *up*, from 0.3597 to 0.4238.
- **Both classmates' 3,053 wrong answers come from the mode, not from bugs.** Against answers frozen without regex, both ports get 0 wrong. Madhur's instruction says "without regex"; Kushal's names no mode at all.

## Honest list: what is not perfect

- `tests/gen.py`, `tools/` and `evidence/` still describe the old 2,000-title exam. `docs/DATASET.md` says so.
- `SHA256SUMS` was already wrong before Day 5: about 40 stale hashes, plus 3 files listed that do not exist. I updated only the lines for files I changed.
- The Python lock in `tests/Dockerfile` has not been attacked yet. It is only proven by the build-time check and by the oracle still scoring 1.0.
- Windows needed workarounds:
  - the kit's child Python needed `-X utf8`;
  - the CRLF output had to be converted to LF;
  - Device Guard blocked running Kushal's port natively, so it was measured in Docker only.

## Likely questions, short answers

- **Why 0.5 for the gate?** Any port that is honestly trying gets far more than half right. Below the gate the maximum reward is 4 × 0.5 / 6 = 0.33. In practice, every cheat stays near behaviour 0.01–0.14, which is far under 0.2.
- **Could the gate hurt a real port?** Only a port that is wrong on more than half the titles. My oracle and both classmates score about 0.97 on behaviour (96,947 of 100,000 right).
- **Why lock Python if nobody used it?** The verifier image needs Python for rewardkit. Without the lock, a submission running as uid 65534 could call it, which is the "Python inside" cheat.
