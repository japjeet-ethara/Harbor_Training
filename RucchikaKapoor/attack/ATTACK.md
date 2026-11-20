# Attack Report — CHANDAR PRAKASH

## 1. Target Information

- Attacker: Rucchika Kapoor
- Target: CHANDAR PRAKASH
- Repository: Harbor_Training_3
- Target commit SHA: `48177206bd14bf54f0144d73089569040b597f32`
- Target task path: `Chandar Prakash/titlecase-go`
- Date of testing: 2026-11-20

## 2. Target Task Analysis

The target asks for a Go implementation that reads titles from stdin and prints titlecased lines to stdout. The solution must use the Go standard library, contain no Python files, and pass `go build ./...`. Hidden automatic tests compare behavior against the original Python implementation. Partial credit is allowed.

The verifier performs three weighted checks:

- Build: `go build ./...`
- No-Python restriction: no `.py` files in the repository
- Hidden behavior: build and run the root Go program against `hidden_inputs.txt`, then compare stdout bytes with `hidden_expected.txt`

Relevant source locations:

- Task requirements: `instruction.md:13-15,23`
- Hidden behavior reads: `tests/test_outputs.py:29-30`
- Hidden output comparison: `tests/test_outputs.py:68-69`
- Build and no-Python checks: `tests/test_outputs.py:75-86`
- Partial weights: `tests/test_outputs.py:88-92`
- Reward calculation: `tests/test_outputs.py:93-104`
- Visible and hidden data generation: `tests/gen.py:87-91`

Identified weaknesses:

1. **Fixed build and no-Python credit can be obtained without behavior.**  
   Exact file: `tests/test_outputs.py:88-92`. Every successful build and restriction check receives one weight point even when behavior is zero. The final reward is `(1 + 1 + 0) / 11 = 0.181818...`, demonstrated by the build-only solution.

2. **Behavior scoring does not require an exact line count or full output shape.**  
   Exact file: `tests/test_outputs.py:68-69`. It zips `actual` against `expected` and divides matches by the expected length. A solution that emits a matching prefix can receive partial behavior credit while omitting or adding lines. It also never separately penalizes extra output lines.

3. **Behavioral data generation is deterministic and data pairs are generated together.**  
   Exact file: `tests/gen.py:6,87-91`. `random.seed(1)` and the shared `used` set make visible and hidden datasets reproducible. An environment that exposes test files or implementation internals could derive mappings. In this run, however, the solution environment did not expose `/tests`; the lookup cheat received behavior `0`.

4. **No visible-test or independent behavioral suite is evaluated.**  
   Exact file: `tests/test_outputs.py:29-69`. Only 2,000 hidden inputs are executed. If hidden inputs are generated from a limited set of repeating patterns, approximate solutions can exploit overlap or partial patterns.

## 3. Cheat 1 — Lookup Table / Visible Information

- What the cheat does: Reads visible `inputs.txt` and `expected.txt` into a Go lookup map, returns mapped answers for visible inputs, and emits no answer for unseen inputs.
- How it works: The Go program maps visible input strings to visible expected strings.
- Files created: `attack/cheat1/solve.sh`
- Harbor command: `harbor run -p <scratch-copy> -a oracle --job-name cheat1-run-lf --jobs-dir <jobs-dir>`
- Actual reward: `0.18181818181818182`
- Individual check scores: build `1.000000`, no_python `1.000000`, behaviour `0.000000`
- Job folder: `files/jobs/cheat1-run-lf`
- Trial folder: `files/jobs/cheat1-run-lf/cheat1-target__GPg7MHh`
- Why it worked or failed: Failed behavior-wise; it received only the two fixed 1-point checks. The solution did not match the hidden inputs.
- Relevant target file and line: `tests/test_outputs.py:29-30,68-69,88-92`
- Suggested fix: Keep visible and hidden data in separate verifier-only storage, rotate or cryptographically randomize hidden inputs, and prohibit solutions from reading `/tests`.

## 4. Cheat 2 — Partial Implementation

- What the cheat does: Lowercases each word, uppercases its first character, and collapses whitespace.
- How it works: It handles only a basic word-capitalization approximation and ignores titlecase small words, acronyms, punctuation, apostrophes, hyphens, slashes, and line edge cases.
- Files created: `attack/cheat2/solve.sh`
- Harbor command: `harbor run -p <scratch-copy> -a oracle --job-name cheat2-run-lf --jobs-dir <jobs-dir>`
- Actual reward: `0.18181818181818182`
- Individual check scores: build `1.000000`, no_python `1.000000`, behaviour `0.000000`
- Job folder: `files/jobs/cheat2-run-lf`
- Trial folder: `files/jobs/cheat2-run-lf/cheat2-target__fSfLQqt`
- Why it worked or failed: Failed behavior-wise. The approximate implementation matched zero hidden outputs. It still earned fixed build/restriction credit.
- Relevant target file and line: `tests/test_outputs.py:68-69,85-92`
- Suggested fix: Use more diverse hidden edge cases, reduce or remove fixed credit for trivial checks, and require exact output length plus exact byte-for-byte comparison.

## 5. Cheat 3 — Build / Restriction / Evaluation Weakness

- What the cheat does: Reads stdin and emits no output.
- How it works: It is a valid Go module that builds and contains no Python files.
- Files created: `attack/cheat3/solve.sh`
- Harbor command: `harbor run -p <scratch-copy> -a oracle --job-name cheat3-run-lf --jobs-dir <jobs-dir>`
- Actual reward: `0.18181818181818182`
- Individual check scores: build `1.000000`, no_python `1.000000`, behaviour `0.000000`
- Job folder: `files/jobs/cheat3-run-lf`
- Trial folder: `files/jobs/cheat3-run-lf/cheat3-target__VfR4NLY`
- Why it worked or failed: Behavior failed completely, but the program still earned 18.18% reward through build and no-Python checks.
- Relevant target file and line: `tests/test_outputs.py:75-92`
- Suggested fix: Lower fixed-check weights, require behavior before awarding final reward, and require stdout to contain exactly one output line per non-trailing input line.

## 6. Comparison of Results

| Cheat | Strategy | Actual Reward | Job Folder | Result |
|---|---|---:|---|---|
| 1 | Visible lookup | `0.18181818181818182` | `cheat1-run-lf` | Failed behavior; fixed checks passed |
| 2 | Partial implementation | `0.18181818181818182` | `cheat2-run-lf` | Failed behavior; fixed checks passed |
| 3 | Build/restriction-only | `0.18181818181818182` | `cheat3-run-lf` | Failed behavior; fixed checks passed |

## 7. Strongest Cheat

There is no unique strongest cheat. All three achieved the same actual reward, `0.18181818181818182`, because each passed build and no-Python checks and received zero behavior credit.

The build-only cheat is the clearest demonstration: it proves the fixed 18.18% reward is obtainable with no titlecase behavior.

## 8. Recommended Fixes

- Assign most or all reward weight to behavior rather than build and file restrictions.
- Reject solutions unless stdout has exactly the expected number of lines and equal byte content.
- Use hidden test data that is not generated from a deterministic seed or reusable visible patterns.
- Keep test data and hidden expected answers outside the solution environment.
- Expand hidden tests across punctuation, whitespace, Unicode, acronyms, apostrophes, hyphens, slashes, and subphrases.
- Add independent visible tests and require a behavior test even when build or no-Python passes.

## 9. Conclusion

The experiments show that the target has real partial-credit weaknesses: a Go program with no titlecasing behavior can earn 18.18% simply by building and avoiding Python files. The lookup and partial solutions failed hidden behavior, while the build-only solution demonstrated that fixed checks dominate the final reward. The evaluation should strengthen output-shape validation and reduce fixed-check weight relative to actual functionality.
