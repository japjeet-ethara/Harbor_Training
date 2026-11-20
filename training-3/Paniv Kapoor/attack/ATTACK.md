# Day 4 - Break and Harden: Attack Report

## 1. Target Information

- Target owner: Yuvraj Singh
- Target task: titlecase-go
- Target commit: e70a69476ae4fe28a046f4a7c526ed7f77b45396
- Attacker: Paniv Kapoor
- Attack date: 2026-11-18

## 2. Results Summary

| Cheat | Strategy | Actual Reward | Harbor Job |
|---|---|---:|---|
| Cheat 1 | Visible-input lookup table | 0.3653 | 2026-11-18__18-24-46 |
| Cheat 2 | Python hidden in extensionless file | 1.0000 | 2026-11-18__18-28-10 |
| Cheat 3 | Partial Go implementation | 0.3653 | 2026-11-18__18-31-34 |

All rewards above are actual overall rewards from Harbor runs. The saved reward JSON files contain only the overall reward, not individual verifier scores.

## 3. Cheat 1 - Visible Input Lookup Table

### What it does

The solution reads the visible input-output dataset during attack preparation and embeds the known input-output pairs in a Go map.

For inputs not present in the map, it uses a fallback titlecase implementation.

### Evidence

- `cheat1/solve.sh:24` - Lookup map declaration.
- `cheat1/solve.sh:2027` - Fallback implementation comment.
- `cheat1/solve.sh:2028` - Fallback function.
- `cheat1/solve.sh:2057` - Fallback used for unknown inputs.

### Actual result

- Reward: 0.3653
- Harbor job: `2026-11-18__18-24-46`
- Saved result: `results/cheat1-reward.json`

### Why it worked

The solution could reproduce outputs for inputs already present in the visible dataset. However, unseen hidden inputs were not covered by the lookup table, and the fallback did not fully reproduce the original titlecase behaviour.

### How to defend against it

Use hidden test inputs that are not present in the visible dataset. Include edge cases and verify that the implementation generalizes instead of memorizing known examples.

## 4. Cheat 2 - Python in an Extensionless File

### What it does

The solution copies Python titlecase logic into a file named `py_titlecase_engine`, which has no `.py` extension.

A Go wrapper executes this file using `python3`.

### Evidence

- `target/tests/no_python.py:29` - The verifier scans for files ending in `.py`.
- `cheat2/solve.sh:8` - Creates the extensionless Python engine.
- `cheat2/solve.sh:311` - Makes the engine executable.
- `cheat2/solve.sh:330` - Defines the engine path.
- `cheat2/solve.sh:340` - Executes Python using `exec.Command`.

### Actual result

- Reward: 1.0000
- Harbor job: `2026-11-18__18-28-10`
- Saved result: `results/cheat2-reward.json`

### Why it worked

The verifier checked for Python files using the `.py` extension. The extensionless Python file was not detected by that scan. Python was available in the runtime environment, so the Go wrapper could execute the original Python logic and reproduce the expected behaviour.

### How to defend against it

Do not rely only on filename extensions to detect forbidden languages. Inspect executable files and runtime processes, restrict interpreters where appropriate, and enforce the intended implementation language through stronger sandbox and environment controls.

## 5. Cheat 3 - Partial Go Implementation

### What it does

This solution uses a basic Go implementation. It processes characters, uppercases the first rune of a word, and lowercases subsequent runes.

It does not fully implement the original titlecase rules.

### Evidence

- `cheat3/solve.sh:29` - Creates a strings.Builder.
- `cheat3/solve.sh:31` - Iterates over runes.
- `cheat3/solve.sh:37` - Uppercases a rune.
- `cheat3/solve.sh:40` - Lowercases a rune.

### Actual result

- Reward: 0.3653
- Harbor job: `2026-11-18__18-31-34`
- Saved result: `results/cheat3-reward.json`

### Why it worked

The implementation handled basic titlecase transformations but did not reproduce special rules such as small words, acronyms, punctuation, hyphenated words, and names with special capitalization patterns.

### How to defend against it

Use comprehensive hidden behavioural tests covering special titlecase rules, punctuation, acronyms, names, and edge cases. Verify exact output rather than checking only whether the program builds.

## 6. Final Comparison

Cheat 2 achieved the highest reward of 1.0000.

Cheat 1 and Cheat 3 both achieved 0.3653, despite using different approaches.

The equal rewards do not mean the implementations were identical. They only indicate that their overall weighted rewards were equal.

The saved reward files do not provide enough information to claim an exact component-wise score breakdown.

## 7. Conclusion

The strongest attack was Cheat 2. It exposed a weakness in relying exclusively on `.py` filename detection to enforce a no-Python requirement.

The main hardening lesson is that a verifier must validate actual runtime behaviour and implementation constraints, not just filenames or basic build success.

---

# Day 6 - Attack Re-evaluation Report

## 8. Day 6 Target Information

- Target owner: Yuvraj Singh
- Target task: titlecase-go
- Target commit: e70a69476ae4fe28a046f4a7c526ed7f77b45396
- Attacker: Paniv Kapoor
- Attack date: 2026-11-20
- Test environment: Local copied target at `attack/target`
- Original Yuvraj task was not modified.

## 9. Day 6 Results Summary

All four attacks were executed against Yuvraj's updated hardened task using Harbor.

| Cheat | Strategy | Day 4 Reward | Day 6 Reward | Harbor Job |
|---|---|---:|---:|---|
| Cheat 1 | Visible-input lookup table | 0.3653 | 0.1250 | 2026-11-20__19-15-09 |
| Cheat 2 | Python hidden in extensionless file | 1.0000 | 0.0625 | 2026-11-20__19-22-12 |
| Cheat 3 | Partial Go implementation | 0.3653 | 0.1250 | 2026-11-20__19-26-24 |
| Cheat 4 | Hidden Python engine with Go wrapper | Not recorded | 0.0625 | 2026-11-20__19-30-58 |

All four runs completed with zero exceptions.

### Saved result files

- `results/cheat1-day6-result.json`
- `results/cheat2-day6-result.json`
- `results/cheat3-day6-result.json`
- `results/cheat4-day6-result.json`

## 10. Cheat-by-Cheat Analysis

### Cheat 1 - Visible Input Lookup Table

- Day 6 reward: 0.1250
- Harbor job: `2026-11-20__19-15-09`
- Evidence: `cheat1/solve.sh`

The lookup-table strategy still obtained a non-zero reward, but its reward decreased from 0.3653 to 0.1250.

Yuvraj's updated hidden tests and reward configuration significantly reduced the value of memorizing visible input-output pairs.

### Cheat 2 - Python in an Extensionless File

- Day 6 reward: 0.0625
- Harbor job: `2026-11-20__19-22-12`
- Evidence: `cheat2/solve.sh`

The attack hides Python logic in a file without a `.py` extension and invokes it through a Go wrapper.

The reward decreased from 1.0000 to 0.0625 after hardening.

This demonstrates that the updated verifier and runtime restrictions substantially reduced the effectiveness of this bypass.

### Cheat 3 - Partial Go Implementation

- Day 6 reward: 0.1250
- Harbor job: `2026-11-20__19-26-24`
- Evidence: `cheat3/solve.sh`

The partial implementation still receives a non-zero reward, but its reward decreased from 0.3653 to 0.1250.

The stronger hidden behavioural tests make incomplete titlecase implementations much less effective.

### Cheat 4 - Hidden Python Engine

- Day 6 reward: 0.0625
- Harbor job: `2026-11-20__19-30-58`
- Evidence: `Yuvraj-Singh/attack/cheat4/solve.sh`

This attack creates an extensionless Python file named `engine` and uses a Go wrapper to execute it.

The attack obtained only 0.0625 reward against the updated target.

This provides additional evidence that the extensionless Python execution strategy is substantially less effective after hardening.

## 11. Final Oracle Restoration Verification

After all four attacks, the original Yuvraj solution was restored from:

`Yuvraj-Singh/task/solution/solve.sh`

The restored solution was tested again using Harbor.

- Reward: 1.0000
- Exceptions: 0
- Harbor job: `2026-11-20__19-41-16`
- Saved result: `results/oracle-restored-day6-result.json`

This confirms that the copied target was restored to a working original solution after attack testing.

## 12. Day 4 vs Day 6 Comparison

The three original attacks showed substantial reward reductions:

- Cheat 1: 0.3653 -> 0.1250
- Cheat 2: 1.0000 -> 0.0625
- Cheat 3: 0.3653 -> 0.1250

Cheat 4 also achieved only 0.0625 against the updated task.

However, none of the four attacks achieved a zero reward. Therefore, these results demonstrate partial attack suppression, not complete attack elimination.

## 13. Conclusion

Yuvraj's hardening substantially reduced the effectiveness of all four tested attacks.

The most significant reduction occurred in Cheat 2, which went from a perfect reward of 1.0000 to 0.0625.

The updated hidden behavioural tests, no-Python enforcement, and reward configuration made the attacks considerably less successful.

The final original Oracle verification achieved 1.0000, confirming that the target remained functional after the experiments.

