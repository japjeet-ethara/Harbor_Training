# Attack Report - Shreed Vyas

## 1. Target Information

- Attacker: Saket Kukatkar
- Target: Shreed Vyas
- Repository: Harbor_Training_3
- Target commit SHA: `0e16eba90d64ec3ac08275a502006956a99cf866`
- Target task path: `Shreed_Vyas/titlecase-go`
- Date of testing: 2026-11-20

## 2. Target Task Analysis

The target requires a Go program at `/workspace/repo` that reads one title per line from stdin and produces the original Python `titlecase()` output byte for byte. It forbids remaining `.py` files and requires `go build ./...` to succeed (instruction.md lines 7-19).

The environment copies the Python titlecase source into `/workspace/repo` (`environment/Dockerfile` lines 1-4). The verifier separately builds the submitted Go program and uses 2000 generated hidden inputs (tests/gen.py lines 104-121). Behaviour is the fraction of 2000 hidden output lines matched exactly (tests/checks.py lines 51-83). Reward uses weighted mean: build 1, no-Python 1, behaviour 4 (tests/checks.py lines 85-87; reward.toml line 2).

Three weakest points:

1. **Independent partial-credit checks:** `build` and `no_python` pass even when behaviour is zero. This is visible at tests/checks.py lines 28-47 and 85-87.
2. **Visible sample answers are separate but available in the task data:** tests/gen.py lines 43-48 create 2000 visible lines and lines 118-119 write visible inputs/outputs. An exact-input lookup can earn limited credit, although the hidden set is disjoint (gen.py lines 111-112).
3. **Line-level hidden behaviour gives partial credit:** checks.py lines 60-81 counts matched lines independently. It does not require a coherent implementation, so a few accidental or guessed lines can raise reward.

## 3. Cheat 1 - Lookup Table / Visible Information

- What the cheat does: Embeds 12 exact entries from the visible input/expected data and prints unchanged input for all other lines.
- How it works: It only answers the visible examples from which the expected output is known; no hidden answer file is read.
- Files created: `SaketKukatkar/attack/cheat1/solve.sh`
- Harbor command: `harbor run -p SaketKukatkar\attack\scratch-cheat1 -a oracle -o SaketKukatkar\attack\jobs\cheat1-rerun`
- Actual reward: `0.334`
- Individual check scores: build `1.0`; no_python `1.0`; behaviour `0.001`
- Job folder: `SaketKukatkar/attack/jobs/cheat1-rerun/2026-11-20__10-41-11/scratch-cheat1__xf862GL`
- Why it worked or failed: It failed to implement the task, but the independent build and restriction checks supplied 2/6 weighted credit. It matched only 2 of 2000 hidden lines.
- Relevant target file and line: `tests/checks.py:28-47`, `tests/checks.py:51-83`, `tests/gen.py:118-119`
- Suggested fix: Keep all test cases genuinely disjoint and add semantic coverage that rejects lookup-only implementations, or weight a complete-behaviour gate separately from build checks.

## 4. Cheat 2 - Partial Implementation

- What the cheat does: Capitalizes only the first word and lowercases later words, while ignoring punctuation and titlecase small-word rules.
- How it works: This is deliberately incomplete and cannot reproduce the Python titlecase behaviour.
- Files created: `SaketKukatkar/attack/cheat2/solve.sh`
- Harbor command: `harbor run -p SaketKukatkar\attack\scratch-cheat2 -a oracle -o SaketKukatkar\attack\jobs\cheat2`
- Actual reward: `0.334`
- Individual check scores: build `1.0`; no_python `1.0`; behaviour `0.001`
- Job folder: `SaketKukatkar/attack/jobs/cheat2/2026-11-20__10-43-47/scratch-cheat2__fkvETAx`
- Why it worked or failed: It passed both non-behaviour checks and matched 2 of 2000 hidden lines. It was not a complete implementation.
- Relevant target file and line: `tests/checks.py:51-83`, `tests/checks.py:85-87`
- Suggested fix: Use property-based or edge-case-heavy hidden inputs and require a stronger full-task threshold rather than relying only on line fraction.

## 5. Cheat 3 - Build / Restriction / Evaluation Weakness

- What the cheat does: Builds a Go program that outputs `NOT IMPLEMENTED` for every input.
- How it works: It passes compilation and removes all Python files, but implements no titlecasing behaviour.
- Files created: `SaketKukatkar/attack/cheat3/solve.sh`
- Harbor command: `harbor run -p SaketKukatkar\attack\scratch-cheat3 -a oracle -o SaketKukatkar\attack\jobs\cheat3`
- Actual reward: `0.3333`
- Individual check scores: build `1.0`; no_python `1.0`; behaviour `0.0`
- Job folder: `SaketKukatkar/attack/jobs/cheat3/2026-11-20__10-46-11/scratch-cheat3__amWx7tQ`
- Why it worked or failed: It passed the build and no-Python checks and received 2/6 of the weighted reward despite zero behaviour.
- Relevant target file and line: `instruction.md:9-15`, `tests/checks.py:28-47`, `tests/checks.py:85-87`
- Suggested fix: Add a minimum behaviour threshold or gate submission success on passing a meaningful behaviour fraction before awarding build/restriction credit.

## 6. Comparison of Results

| Cheat | Strategy | Actual Reward | Job Folder | Result |
|---|---|---:|---|---|
| Cheat 1 | Visible lookup table | 0.334 | `2026-11-20__10-41-11/scratch-cheat1__xf862GL` | Failed complete task |
| Cheat 2 | Partial implementation | 0.334 | `2026-11-20__10-43-47/scratch-cheat2__fkvETAx` | Failed complete task |
| Cheat 3 | Build/restriction-only | 0.3333 | `2026-11-20__10-46-11/scratch-cheat3__amWx7tQ` | Failed complete task |

## 7. Strongest Cheat

Cheat 1 was tied for strongest with Cheat 2 at `0.334`; neither reproduced the required behaviour. Cheat 1 was marginally highest because it matched 2 hidden lines, versus the partial implementation's same `0.001` behaviour score.

## 8. Recommended Fixes

- Make build and no-Python prerequisites, not independently rewarded achievements.
- Require a substantial behaviour threshold before a submission can receive build/restriction credit.
- Do not let visible answers be reusable as an exact lookup without verifying an implementation against unseen, diverse inputs.
- Remove or isolate source fixtures that make superficial implementations easy to infer.
- Improve hidden coverage for empty lines, small words, punctuation, apostrophes, hyphens, slash words, Unicode, acronyms, and mixed-case forms.
- Publish aggregate and per-criterion output so individual check weaknesses are visible.

## 9. Conclusion

All three experiments were genuine Harbor runs. The 6-point weighted system assigned 2 points to build and no-Python checks in every run, allowing incomplete and nonfunctional solutions to receive roughly one-third reward without implementing titlecasing.
