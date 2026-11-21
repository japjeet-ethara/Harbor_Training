# Day 4 - Break a Classmate's Task

## 1. Attacker and Target Information

- Attacker: NiharikaMudgal
- Target: JiyaPatel
- Target task path: C:\Users\NiharikaMudgal\Desktop\task3\JiyaPatel\titlecase-go
- Target commit SHA: 4a5d1a812e5d7a9ffca5fbedd98918e091443113
- Attack execution date: 2026-11-20
- Available repository: C:\Users\NiharikaMudgal\Desktop\task3
- Repository mismatch: the requested name `Harbor_Training_3` was not present. The available repository remote is `https://github.com/japjeet-ethara/Harbor_Training.git`.

## 2. Prerequisite and Target Analysis

The likely practice task is committed in the available repository at commit `ee7e3dfbb6da17d4eafa86734973ec53e08206bc` under `Niharika_mudgal/titlecase-go`. The local repository is on `main` at that commit, with `origin/main` at the same commit. This is evidence that the practice task prerequisite was met at repository level; the assignment PDF confirming exact rubric was not present.

The target is a title-casing Go port. Its requirements are in `instruction.md`: read stdin line by line, write titlecased lines, use only the Go standard library, remove every `.py` file, and pass `go build ./...`. The grader in `tests/test.sh`, `tests/behaviour.py`, `tests/build.py`, `tests/no_python.py`, and `tests/reward.toml` evaluates build, absence of Python files, and exact hidden behavior.

Evidence of weaknesses:

- `tests/gen.py` generates the visible and hidden input files by resetting the same `random.Random(1)` seed before each dataset. The visible and hidden input data are therefore reproducible copies; `tests/data/expected.txt` is visible and contains the corresponding visible outputs.
- `tests/behaviour.py` uses `zip(exp, out)` and gives no check for equal output length. A short output can score only for its matching prefix.
- `tests/test.sh` also computes behavior only if a binary builds and otherwise falls back to explicit reward fields.
- `tests/reward.toml` weights behavior four times more than build or no-Python checks.

## 3. Cheat 1 - Lookup or Visible-Information Approach

The scratch solution maps each stdin line to the corresponding line in visible `tests/data/expected.txt`, removing Python files and building a Go binary. This targets the deterministic reuse of visible and hidden generated data.

- Scratch location: C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\scratch1
- Solution script: C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\cheat1\solve.sh
- Exact Harbor command: `harbor run -p C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\scratch1 -a oracle`
- Actual reward: `0.3416666666666666`
- Individual checks: build `1.0`, no_python `1.0`, behaviour `0.0125`
- Actual job directory: `C:\Users\NiharikaMudgal\Desktop\task3\jobs\2026-11-20__14-13-33`
- Reward JSON: `C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\results\cheat1-reward.json`
- Why it scored as it did: the lookup implementation built and removed Python files. It obtained only 25 of 2000 behavior matches, so behavior was low.

## 4. Cheat 2 - Partial Implementation Approach

The scratch solution implements a small Go capitalization fallback and removes Python files. It does not attempt to read hidden answers.

- Scratch location: C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\scratch2
- Solution script: C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\cheat2\solve.sh
- Exact Harbor command: `harbor run -p C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\scratch2 -a oracle`
- Actual reward: `0.40700000000000003`
- Individual checks: build `1.0`, no_python `1.0`, behaviour `0.1105`
- Actual job directory: `C:\Users\NiharikaMudgal\Desktop\task3\jobs\2026-11-20__14-17-23`
- Reward JSON: `C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\results\cheat2-reward.json`
- Why it scored as it did: the partial implementation built and passed the Python-removal check, while basic capitalization matched 221 of 2000 hidden inputs.

## 5. Cheat 3 - Evaluation or Restriction Weakness

The scratch solution outputs only the 25 known visible prefix lines. The target behavior check uses `zip(exp, out)`, so output length is not enforced. This targets that missing line-count restriction.

- Scratch location: C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\scratch3
- Solution script: C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\cheat3\solve.sh
- Exact Harbor command: `harbor run -p C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\scratch3 -a oracle`
- Actual reward: `0.3416666666666666`
- Individual checks: build `1.0`, no_python `1.0`, behaviour `0.0125`
- Actual job directory: `C:\Users\NiharikaMudgal\Desktop\task3\jobs\2026-11-20__14-18-42`
- Reward JSON: `C:\Users\NiharikaMudgal\Desktop\task3\NiharikaMudgal\attack\results\cheat3-reward.json`
- Why it scored as it did: the prefix-only implementation built and removed Python files, and matched only 25 behavior lines.

## 6. Results Comparison

| Cheat | Approach | Actual Reward | Result |
|---|---|---:|---|
| Cheat 1 | Lookup / visible information | 0.3416666666666666 | Completed; 25 behavior matches |
| Cheat 2 | Partial implementation | 0.40700000000000003 | Completed; 221 behavior matches |
| Cheat 3 | Evaluation weakness | 0.3416666666666666 | Completed; 25 behavior matches |

No cheat passed completely. The behavior scores confirm partial implementations did not reproduce the hidden suite.

## 7. Strongest Cheat

Cheat 2 was the strongest cheat. It achieved the highest actual reward (`0.40700000000000003`) and highest behavior score (`0.1105`), with build and no-Python both at `1.0`.

## 8. Recommended Fixes

- Strengthen hidden-test independence in `tests/gen.py`: generate visible and hidden datasets with separate seeds or values. This reduces the visible-information shortcut and may require replacing the visible/hidden overlap.
- Enforce exact output cardinality in `tests/behaviour.py`: reject as behavior 0.0 when `len(out) != len(exp)` before the `zip` comparison.
- Make the behavior and hidden answer handling explicit in `tests/test.sh` and reward configuration; test a complete, line-by-line result rather than relying on zip truncation.
- Keep hidden expected fixtures out of agent-readable locations and prohibit solutions from reading `/tests` where possible.
- Retain independent build and no-Python checks, but do not let them be outweighed or bypassed by a partial prefix match.

These fixes were not implemented in JiyaPatel's original task.

## 9. Conclusion

The available target and evaluator were inspected, three independent scratch approaches were created, and all three corrected implementations completed through actual Harbor runs. Cheat 2 was strongest. The original JiyaPatel task was not modified.
