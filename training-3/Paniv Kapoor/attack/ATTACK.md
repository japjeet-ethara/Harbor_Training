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
