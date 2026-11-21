# Attack Report — Prashant Kumar

Target: Prashant Kumar fe970011a7693e9344be4e3e2b03bea40494a475

## Cheat 1 — Read hidden answers from disk
What it does:   At runtime, cats /tests/data/hidden_expected.txt directly as output instead of running the Go binary.
Score:          reward 1.000 (build 1.0, no_python 1.0, behaviour 1.0)
Job folder:     jobs/2026-11-18__16-37-53
Why it worked:  tests/behaviour/check.py line 7 defines EXPECTED = Path("/tests/data/hidden_expected.txt"). The file is readable by the agent at runtime because tests/ is mounted into the container with no access restrictions.
How to fix:     Move hidden answer files outside the agent-visible container, or compare output against answers computed at check time rather than stored in a readable file.

## Cheat 2 — Build trick and delete Python files
What it does:   Writes a minimal Go echo program into /workspace/repo, deletes all .py files, and builds. Produces no correct titlecase output.
Score:          reward 0.394 (build 1.0, no_python 1.0, behaviour 0.091)
Job folder:     jobs/2026-11-18__16-45-49
Why it worked:  tests/no_python/check.py line 7-16 gives full no_python credit just for go build passing and no .py files present, with no check that answers are correct. tests/build/check.py line 7 only checks return code == 0.
How to fix:     Gate no_python credit on behaviour also being above a minimum threshold, so deleting .py files alone gives no reward.

## Cheat 3 — Half port
What it does:   Implements only simple titlecase (capitalize first letter, lowercase small words) with no edge case handling — no Unicode, no punctuation, no McX, no apostrophes.
Score:          reward 0.338 (build 1.0, no_python 1.0, behaviour 0.006)
Job folder:     jobs/2026-11-18__16-48-07
Why it worked:  tests/behaviour/check.py line 10-17 gives partial credit proportional to correct answers, so even a weak port earns build and no_python points freely.
How to fix:     Require a minimum behaviour score (e.g. 0.5) before build and no_python contribute to reward, so a half port cannot score above 0.2 overall.

## Highest score achieved
Cheat 1: reward 1.000

---

## Day 6 — Re-attack on Hardened Task

Target: Prashant Kumar `edcf6407123db76fe9752dc2947693055725cbe7`

### Re-attack Results

| Cheat | Day 4 Score | Day 6 Score | Build | No_Python | Behaviour | Job Folder | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Cheat 1** (Cat hidden answers) | 1.000 | **0.167** | 1.000 | 1.000 | 0.000 | `jobs/2026-11-20__16-46-45` | Closed (< 0.200) |
| **Cheat 2** (Echo build & delete .py) | 0.394 | **0.167** | 1.000 | 1.000 | 0.000 | `jobs/2026-11-20__16-46-55` | Closed (< 0.200) |
| **Cheat 3** (Half port) | 0.338 | **0.167** | 1.000 | 1.000 | 0.000 | `jobs/2026-11-20__16-47-05` | Closed (< 0.200) |

### Analysis of Defenses
1. **Cheat 1 closed:** Prashant renamed the test data files to `exam_inputs.txt` and `exam_answers.txt`, and runs the test binary as unprivileged `user=65534, group=65534` (`nobody`), so catting the legacy `/tests/data/hidden_expected.txt` yields nothing.
2. **Cheats 2 & 3 closed:** Prashant made behavior strictly all-or-nothing (`return float(matches == len(expected))`), completely eliminating partial credit.
3. **Weight rebalancing:** In `tests/reward.toml`, Prashant rebalanced weights to `{ build = 1.0, no_python = 1.0, behaviour = 10.0 }` (total weight 12.0). Any solution that passes build and no_python but fails behavior receives at most `2.0 / 12.0 = 0.1667` (< 0.200).

### Summary
All three cheats now score **0.167**, which is strictly below 0.200. Prashant Kumar's hardened task successfully defends against all three attacks.
