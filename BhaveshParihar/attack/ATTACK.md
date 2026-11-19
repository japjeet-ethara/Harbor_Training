# Attack Report - Paniv Kapoor

## 1. Target Information

- Attacker: Bhavesh Parihar
- Target: Paniv Kapoor
- Repository: Harbor_Training_3
- Target commit SHA: `6615bc924ccc582fd09a7c8cca6c5685546d00e7`
- Target task path: `Paniv_Kapoor/titlecase-go`
- Date of testing: 2026-11-20

## 2. Target Task Analysis

The task requires a Go program at the repository root that reads one title per line from stdin and writes the exact Python `titlecase()` result for each line to stdout. The hard requirements are the Go standard library, no Python files, and successful `go build ./...` ([instruction.md](../../Paniv_Kapoor/titlecase-go/instruction.md):15-19). Partial credit is allowed ([instruction.md](../../Paniv_Kapoor/titlecase-go/instruction.md):25-27).

The evaluator gives build and no-Python checks equal weight and behaviour four times that weight ([tests/checks/reward.toml](../../Paniv_Kapoor/titlecase-go/tests/checks/reward.toml):1-4). The build check only runs `go build ./...` ([tests/checks/build/build.py](../../Paniv_Kapoor/titlecase-go/tests/checks/build/build.py):11-24). The no-Python check removes no code and only rejects `.py` suffixes before running the build again ([tests/checks/no_python/no_python.py](../../Paniv_Kapoor/titlecase-go/tests/checks/no_python/no_python.py):11-36). Behaviour builds and runs the binary against expected hidden lines and calculates the fraction of exact line matches ([tests/checks/behaviour/behaviour.py](../../Paniv_Kapoor/titlecase-go/tests/checks/behaviour/behaviour.py):48-84).

Important weaknesses:

1. **Build and restriction checks are independent from functionality.** `build/build.py:11-24` and `no_python/no_python.py:18-36` award full points for compilation and file naming without verifying title-casing. This yields 2 out of 6 weighted points even for a non-functional program.
2. **Reward is line-fractional, not all-or-nothing.** `behaviour.py:81-84` divides matched lines by the number of expected lines. Any approximate implementation can earn meaningful partial reward.
3. **Visible public fixtures can be copied into a lookup.** The public `tests/data/inputs.txt` and `tests/data/expected.txt` pair is accessible in the repository, while the behaviour check compares line-by-line. A fixed lookup can obtain credit for repeated or canonical inputs without general implementation.

## 3. Cheat 1 - Lookup Table / Visible Information

- What the cheat does: Copies a limited set of canonical public input/output pairs into a Go lookup map and returns the original input for unknown lines.
- How it works: The solution removes the Python package, creates `main.go` with a fixed lookup, and builds as a Go program.
- Files created: `attack/cheat1/solve.sh`
- Harbor command: `harbor run -p <scratch-copy-of-target> -a oracle`
- Actual reward: `0.369`
- Individual check scores:
  - Behaviour: `0.0535`
  - Build: `1.000`
  - No_Python: `1.000`
- Job folder: `2026-11-20__00-47-17/Harbor_Training_3_cheat1__yU3HXzA`
- Why it worked or failed: It worked partially. The fixed entries matched `5.35%` of hidden lines, and the two superficial checks supplied full credit.
- Relevant target file and line: [behaviour.py](../../Paniv_Kapoor/titlecase-go/tests/checks/behaviour/behaviour.py):81-84 and [reward.toml](../../Paniv_Kapoor/titlecase-go/tests/checks/reward.toml):3-4.
- Suggested fix: Add diverse out-of-domain and adversarial hidden inputs, remove public answer overlap from hidden fixtures, and require exact end-to-end behavior before awarding build/restriction points.

## 4. Cheat 2 - Partial Implementation

- What the cheat does: Implements basic whitespace splitting, first-character capitalization, lowercasing, and a small-word exception, but omits the full titlecase specification.
- How it works: It uses only standard Go and removes `.py` files and the `titlecase` directory so the build and no-Python checks pass.
- Files created: `attack/cheat2/solve.sh`
- Harbor command: `harbor run -p <scratch-copy-of-target> -a oracle`
- Actual reward: `0.8827`
- Individual check scores:
  - Behaviour: `0.824`
  - Build: `1.000`
  - No_Python: `1.000`
- Job folder: `2026-11-20__00-50-53/Harbor_Training_3_cheat2__Y2dtJfJ`
- Why it worked or failed: It was the strongest attack. Simple title-casing happened to match many synthetic lines, while build and no-Python checks were both full credit.
- Relevant target file and line: [behaviour.py](../../Paniv_Kapoor/titlecase-go/tests/checks/behaviour/behaviour.py):81-84 and [instruction.md](../../Paniv_Kapoor/titlecase-go/instruction.md):25-27.
- Suggested fix: Raise the threshold or weight behavior more aggressively, penalize partial matches, and include difficult edge cases for hyphenation, slash segments, apostrophes, Unicode, URLs, domains, and spacing.

## 5. Cheat 3 - Build / Restriction / Evaluation Weakness

- What the cheat does: Emits `not implemented` for every input line.
- How it works: It is a minimal standard-library Go program that builds successfully and removes all Python files.
- Files created: `attack/cheat3/solve.sh`
- Harbor command: `harbor run -p <scratch-copy-of-target> -a oracle`
- Actual reward: `0.3333`
- Individual check scores:
  - Behaviour: `0.000`
  - Build: `1.000`
  - No_Python: `1.000`
- Job folder: `2026-11-20__00-54-01/Harbor_Training_3_cheat3__bZ9NPJv`
- Why it worked or failed: It failed behavior completely but still received two-thirds of the total weighted reward because the build and no-Python checks both passed.
- Relevant target file and line: [build.py](../../Paniv_Kapoor/titlecase-go/tests/checks/build/build.py):11-24, [no_python.py](../../Paniv_Kapoor/titlecase-go/tests/checks/no_python/no_python.py):18-36, and [reward.toml](../../Paniv_Kapoor/titlecase-go/tests/checks/reward.toml):3-4.
- Suggested fix: Build checks should verify a representative smoke test or require runnable behavior. No-Python should remain a hard requirement with failure instead of independent weighted credit. A fixed-output program must receive no build/restriction reward unless it also demonstrates behavior.

## 6. Comparison of Results

| Cheat | Strategy | Actual Reward | Job Folder | Result |
|---|---|---:|---|---|
| Cheat 1 | Lookup table | 0.369 | `2026-11-20__00-47-17/Harbor_Training_3_cheat1__yU3HXzA` | Worked partially |
| Cheat 2 | Partial implementation | 0.8827 | `2026-11-20__00-50-53/Harbor_Training_3_cheat2__Y2dtJfJ` | Worked |
| Cheat 3 | Build/restriction weakness | 0.3333 | `2026-11-20__00-54-01/Harbor_Training_3_cheat3__bZ9NPJv` | Failed behavior, passed superficial checks |

## 7. Strongest Cheat

Cheat 2 was strongest with an actual reward of `0.8827`. It received full build and no-Python credit and matched `82.4%` of behavior lines. The fractional behavior scorer and synthetic common-word patterns made a basic implementation much more valuable than its real completeness.

## 8. Recommended Fixes

- Make build/no-Python checks hard gates rather than independently weighted rewards.
- Add a build-time smoke test that executes the binary on multiple distinct inputs.
- Increase behavior weight and add a minimum correctness threshold.
- Remove excessive partial credit or replace the weighted mean with multiple completeness bands.
- Add hidden edge-case families: Unicode case folding, URLs, apostrophes, McNames, small words at boundaries, hyphens, slashes, tabs, and unusual Unicode whitespace.
- Ensure public and hidden fixtures are disjoint or structurally distinct.
- Detect fixed-output programs and lookup-table-sized implementations by adding randomized unseen inputs.

## 9. Conclusion

The experiments show that the target evaluation rewards superficial build compliance separately from real functionality. A fixed-output solution still received `0.3333`, and a partial implementation reached `0.8827` by exploiting fractional behavior scoring and likely overlapping simple synthetic patterns. A small public lookup achieved partial credit, confirming that visible-answer reuse can affect reward. The target would be substantially stronger with hard build/behavior gates, disjoint hidden coverage, and more difficult unseen edge cases.
