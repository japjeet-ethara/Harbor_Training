# Harbor Training Submission - titlecase-go

**Author:** aahantrikha21-sudo  
**Date:** 2026-11-12  
**Task:** Port Python titlecase library to Go

---

## Test Results

| Test Type | Build | No Python | Behaviour | Total Reward |
|-----------|-------|-----------|-----------|--------------|
| Oracle    | 1.0   | 1.0       | 1.0       | **1.000** ✓  |
| Nop       | 0.0   | 0.0       | 0.0       | **0.000** ✓  |
| Cheat     | 1.0   | 1.0       | <0.1      | **<0.200** ✓ |

*(Screenshots attached)*

---

## Rules the Agent Got Wrong Most

The agent struggled most with these rules during development:

1. **MAC_MC Rule (Rule 4)** - The regex `^([Mm]c|MC)(\w.+)` only matches `Mc`, `mc`, `MC` prefixes, NOT `mac`, `Mac`, or `MAC`. The agent initially wrote case-insensitive patterns that incorrectly matched all variants.

2. **Character Class Escaping (punctClass)** - Go's regexp requires different escaping than Python inside character classes `[...]`. The agent used `regexp.QuoteMeta()` which over-escapes, creating malformed character classes. Fixed by using a pre-escaped constant.

3. **UC_INITIALS (Rule 2)** - The pattern `^(?:[A-Z]\.|[A-Z]\.[A-Z])+$` for initials like "D.C." was initially too permissive or too strict in the all-caps detection logic.

4. **Small-First-Last Logic** - Capitalizing small words at line start/end after all processing required careful ordering. The agent initially applied this too early, breaking sub-phrase rules.

---

## What Would Make This Task Harder

To increase difficulty while keeping it fair:

1. **Unicode Complexity** - Add more test cases with:
   - Combining diacritics (é vs e + ́)
   - Non-Latin scripts (Cyrillic, Greek where case rules differ)
   - Right-to-left text with mixed punctuation
   - Zero-width characters and invisible Unicode

2. **Edge Case Density** - Increase the proportion of:
   - Nested hyphen/slash combinations: `"end-to-end/side-by-side"`
   - Multiple apostrophes: `"l'homme d'affaires o'clock"`
   - Em-dash sub-phrases with small words: `"start — a thing — end"`
   - Mixed-case acronyms inside hyphenated words: `"iOS-like UI/UX"`

3. **Ambiguous Input** - Add test cases where:
   - All-caps detection is borderline (some punctuation, some letters)
   - Inline periods could be either initials or domains: `"Dr. Smith at U.S.A. today"`
   - Consonant-only words that look like acronyms but aren't: `"czr myth"`

4. **Stricter Build Requirements** - Require:
   - `go vet ./...` must pass (catches common errors)
   - `gofmt -d .` must report no changes (enforces formatting)
   - No use of `unsafe` package
   - Maximum cyclomatic complexity per function

5. **Performance Threshold** - Add a speed check:
   - Must process 10,000 titles in <1 second (prevents naive solutions)
   - This doesn't test algorithm cleverness but prevents trivial character-by-character approaches

The key is **increasing the density of interacting edge cases** without changing the core rules. This forces the agent to handle the full complexity matrix rather than getting most cases right with simple heuristics.

---

## Task Structure

```
titlecase-go/
├── task.toml              # Harbor config
├── instruction.md         # Agent instructions (checkable rules only)
├── environment/
│   ├── Dockerfile         # FROM golang:1.23, copies python-titlecase
│   └── python-titlecase/  # Original Python source (ground truth)
├── tests/
│   ├── Dockerfile         # Verifier with Go + Python + uvx
│   ├── test.sh            # Generates data, runs RewardKit
│   ├── grader.py          # Three weighted criteria
│   └── gen_verifier.py    # Deterministic data generator
├── solution/
│   └── solve.sh           # Oracle: complete Go port
├── cheat/
│   └── solve.sh           # Baseline: prints visible expected.txt
└── NOTES.md               # Rules extracted from Python source

```

---

## Key Design Decisions

1. **Runtime Data Generation** - Test data is generated inside the verifier using the original Python source, ensuring expected outputs are always ground-truth.

2. **RewardKit with Weights** - Uses `@criterion(weight=N)` decorators for clean scoring:
   - build=1, no_python=1, behaviour=4
   - Weighted mean formula: `(1 + 1 + 4×behaviour_score) / 6`

3. **Separate Verifier** - Agent cannot see test logic or data, proven by cheat detection scoring <0.2.

4. **Hidden Test Data** - 2000 visible + 2000 hidden inputs (different sets) ensures the agent cannot memorize answers.

---

## Repository

- **Python Source:** https://github.com/ppannuto/python-titlecase
- **Commit:** `<to be filled from git log>`
- **License:** MIT
