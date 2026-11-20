# Task Hardening Report: Go Titlecase Port (`titlecase-go`)

**Trainee**: Paniv Kapoor (`training-3/Paniv Kapoor/task`)
**Attacker**: Bhavesh Parihar (`BhaveshParihar/attack`)
**Target Commit**: `6615bc924ccc582fd09a7c8cca6c5685546d00e7`
**Hardened Date**: 2026-11-20

---

## 1. Original Attack Techniques Used by Bhavesh

Bhavesh Parihar analyzed the practice task and identified three structural vulnerabilities in the evaluation harness:
1. **Uncoupled Superficial Checks**: The `build` (`tests/checks/build/build.py`) and `no_python` (`tests/checks/no_python/no_python.py`) checks awarded points independently of functionality, yielding 2 out of 6 weighted points (33.3%) even if the program produced no valid titlecase output.
2. **Fractional Scoring Gradient**: `behaviour.py` scored submissions by the fraction of lines matching the expected output (`matched / total`), rewarding incomplete or approximate heuristics.
3. **Public Fixture Overlap**: The public test suite (`tests/data/inputs.txt`) contained canonical examples that overlapped with hidden evaluation patterns.

Bhavesh implemented three cheats demonstrating these vulnerabilities:
- **Cheat 1 (Lookup Table)**: Embedded 35 canonical public input/output pairs in a hardcoded Go map and echoed unknown inputs unchanged (`BhaveshParihar/attack/cheat1/solve.sh`).
- **Cheat 2 (Partial Implementation)**: Implemented naive whitespace splitting, first-letter capitalization, and a basic small-word list while omitting complex rules (hyphen/slash recursion, apostrophes, URLs, `Mc`, acronyms, Unicode spacing; `BhaveshParihar/attack/cheat2/solve.sh`).
- **Cheat 3 (Build/Restriction Exploitation)**: A stub program that prints `"not implemented\n"` for every line, doing no titlecasing (`BhaveshParihar/attack/cheat3/solve.sh`).

---

## 2. Root Cause of Each Cheat's Initial Success

| Cheat | Strategy | Old Reward | Behaviour | Build | No_Python | Why It Succeeded on the Old Task |
|---|---|---:|---:|---:|---:|---|
| **Cheat 1** | Lookup Table | **0.3690** | 0.0535 | 1.000 | 1.000 | The hardcoded lookup matched 5.35% of hidden lines; combined with 2/6 free points from build/no-python, it cleared over 36% reward. |
| **Cheat 2** | Partial Port | **0.8827** | 0.8240 | 1.000 | 1.000 | The old 2,000-line exam had high synthetic redundancy with simple word patterns. A basic capitalization heuristic matched 82.4% of lines, yielding an 88.3% overall reward. |
| **Cheat 3** | Stub Program | **0.3333** | 0.0000 | 1.000 | 1.000 | Despite 0% behavioral accuracy, passing the two superficial build checks awarded 1/3 of the total score. |

---

## 3. Hardening Changes Made to Verifier and Solution

### Verifier Hardening
1. **All-Pass Reward Aggregation (`tests/checks/reward.toml`)**:
   - Replaced weighted mean (`aggregation = "weighted-mean"`, weights 1:1:4) with `aggregation = "all-pass"`.
   - Under `all-pass`, all three criteria (`build`, `no_python`, `behaviour`) must score 1.0. If any criterion scores below 1.0, the overall reward is strictly **0.000**.
2. **Strict Exact-Match Verifier (`tests/checks/behaviour/behaviour.py`)**:
   - Replaced fractional line counting with byte-for-byte exact comparison: `ran.stdout == expected_bytes`.
   - Any single mismatched character or line yields `behaviour = 0.0`.
   - Retained and enforced jailed execution (`_run_jailed`) using a clean chroot directory to prevent the submission from inspecting verifier files.
3. **Execution Robustness (`tests/test.sh`)**:
   - Pinned and isolated the rewardkit verifier runner in `tests/test.sh`.

### Solution Hardening (`solution/solve.sh`)
Performed a comprehensive behavioral audit against Python's fallback `re` implementation (`titlecase/__init__.py`), fixing multiple subtle semantic differences:
1. **Subphrase Casing (`applySubphrase`)**: Made small-word matching after subphrase delimiters (`:`, `;`, `.`, `?`, `!`, `-`, `–`, `‒`, `—`, `―`) case-sensitive (lowercase only), matching Python's `SUBPHRASE = regex.compile(r'([:.;?!\-–‒—―][ ])(%s)' % SMALL)` (compiled without `regex.I`). Uppercase words following delimiters (e.g. `BBC: OF`) are preserved.
2. **Trailing Small Word Matching (`applySmallLast`)**: Removed invalid post-word boundary constraints from `SMALL_LAST`, allowing optional trailing punctuation (`\b(%s)[%s]?$`) on words like `VS.}` and `v./`.
3. **Leading Small Word Matching (`applySmallFirst`)**: Ensured greedy punctuation handling followed by candidate alternation and word boundary checks.
4. **Internal Uppercase Protection (`hasUCElsewhere`)**: Restricted character classes in `UC_ELSEWHERE` to ASCII `[a-zA-Z]` and `[A-Z]`, matching Python fallback regex `[%s]*?[a-zA-Z]+[A-Z]+?`.
5. **Apostrophe Recasing (`aposTail`)**: Aligned word-tail detection with `isRegexWord` (`\w`) to properly handle suffixes containing underscores (e.g. `D'Angelo_`, `d'ARCY_`).
6. **Initials Detection (`isUCInitials`)**: Enforced ASCII uppercase matching (`[A-Z]`).
7. **Character Classification (`isRegexWord`)**: Aligned character classification with Python `re`'s `\w` (`unicode.IsLetter`, `unicode.IsNumber`, `unicode.Pc`).
8. **Whitespace Mapping (`whitespace`)**: Included all 29 whitespace code points recognized by Python `re` `\s` (adding `0x1c`–`0x1f`).
9. **Line Ending Sanitization**: Stripped both `\r` and `\n` on every input line.

---

## 4. Why All-Pass Aggregation Matters

Weighted averaging creates a dangerous vulnerability where non-functional submissions receive substantial credit for trivial compliance checks. In software porting exercises, a program that compiles but produces garbage or hardcoded echoes has zero utility.

Under `all-pass`:
- Build compliance and Python elimination become **hard preconditions** rather than score boosters.
- A submission must fulfill every specification criterion simultaneously to receive credit.
- Cheats 1, 2, and 3 are reduced to **0.000**, completely closing the partial-credit exploit.

---

## 5. 100K Exam Generation Methodology

To prevent lookup attacks and adequately sample rare titlecasing edge cases, a 100,000-input exam was generated using Aman Tiwari's test generation kit (`training-3/AmanTiwari/kit/`):
1. **Adversarial Grammar-Based Pool (`make_pool.py`)**:
   - Synthesizes titles across 18 distinct grammatical categories: small words at boundaries, subphrase punctuation, hyphenated compounds, single/double slash paths, apostrophe names (`d'`, `l'`, `o'`), Scottish names (`Mc`/`Mac`), honorifics (`Mr`, `Mrs`, `Ms`, `Dr`), acronyms and consonant clusters, domain names/URLs, all-caps strings, Unicode whitespace variations, and multi-script characters.
   - Generated 100,000 titles with deterministic PRNG seed 1.
2. **Differential Stability Verification (`answers.py`)**:
   - Evaluated each title through Python's reference `titlecase()` twice under different hash seeds (`PYTHONHASHSEED=1` and `PYTHONHASHSEED=2`).
   - Retained only titles where both runs produced identical outputs.
   - **Result**: Exactly 100,000 of 100,000 titles were verified stable (0 dropped).
3. **Installation (`tests/data/`)**:
   - Installed as `hidden_inputs.txt` and `hidden_expected.txt` in `training-3/Paniv Kapoor/task/tests/data/`.

---

## 6. Why "WITHOUT REGEX" Mode Was Selected

In `python-titlecase` (commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`), the package checks if the third-party `regex` module is available:
```python
try:
    import regex
except ImportError:
    import re as regex
    REGEX_AVAILABLE = False
else:
    REGEX_AVAILABLE = True
```
When `regex` is absent (`REGEX_AVAILABLE = False`), the code falls back to Python's standard library `re` module.

The standard-library `re` fallback mode was chosen because:
1. **Self-Contained Standard**: It requires only Python's standard library, avoiding external wheel dependencies and C-extension variations.
2. **Deterministic Rules**: Fallback regexes use well-defined ASCII and standard Unicode categories rather than external Unicode property databases.
3. **Fairness**: Across 100,000 test cases, 3,053 titles produce differing outputs between `regex` and `re` modes (due to `\p{Letter}` vs `[a-zA-Z]` in `UC_ELSEWHERE` and mark handling in `\w`). Fixing the verifier mode strictly to `re` ensures full determinism across all platforms.

---

## 7. Hardened Oracle Results

The fully hardened task was evaluated with the official Harbor command:
```powershell
harbor run -p ".\training-3\Paniv Kapoor\task" -a oracle
```

- **Job Reference**: `jobs/2026-11-20__14-07-37` (Trial `task__EvgSRRV`)
- **Behaviour**: `1.000` (100,000 / 100,000 hidden test lines matched byte-for-byte)
- **Build**: `1.000`
- **No_Python**: `1.000`
- **Overall Reward**: `1.000`

---

## 8. Hardened Attack Results (All Three Cheats)

Bhavesh's three attack scripts were re-run against fresh copies of the hardened task:

| Cheat | Harbor Job Reference | Behaviour | Build | No_Python | Overall Reward | Status |
|---|---|---:|---:|---:|---:|---|
| **Cheat 1** (Lookup) | `jobs/2026-11-20__14-10-02` (`final-cheat1-task__X2pidao`) | 0.000 | 0.000 | 1.000 | **0.000** | Defeated |
| **Cheat 2** (Partial) | `jobs/2026-11-20__14-12-27` (`final-cheat2-task__oYVQWi9`) | 0.000 | 1.000 | 1.000 | **0.000** | Defeated |
| **Cheat 3** (Stub) | `jobs/2026-11-20__14-14-54` (`final-cheat3-task__2jmAvwJ`) | 0.000 | 0.000 | 1.000 | **0.000** | Defeated |

*Saved result artifacts*:
- `BhaveshParihar/attack/results/cheat1-100k-reward.json`
- `BhaveshParihar/attack/results/cheat2-100k-reward.json`
- `BhaveshParihar/attack/results/cheat3-100k-reward.json`

---

## 9. Old vs. New Exam Measurement Across All Three Ports

Measurements were conducted on:
1. **Paniv Kapoor** (`training-3/Paniv Kapoor/task`)
2. **Aman Tiwari** (`training-3/AmanTiwari/task`)
3. **Ayush Khurana** (`training-3/AyushKhurana/task`)
4. **Cheat 2 Baseline** (`BhaveshParihar/attack/cheat2`)

Using:
- **Old Exam**: `day5-work/old-exam/` (2,000 titles)
- **New Exam**: `day5-work/key/` (100,000 titles)
- **Tool**: `training-3/AmanTiwari/kit/compare.py`

### Measured Results Table

| Port | Old Exam (2,000 Titles)<br>Wrong Answers | Old Exam<br>Error Rate | New Exam (100,000 Titles)<br>Wrong Answers | New Exam<br>Error Rate | Random 2K Miss Probability |
|---|---|---|---|---|---|
| **Paniv Kapoor** | **0 of 2,000** | 0.00% | **0 of 100,000** | 0.00% | 100% |
| **Aman Tiwari** | **0 of 2,000** | 0.00% | **0 of 100,000** | 0.00% | 100% |
| **Ayush Khurana** | **0 of 2,000** | 0.00% | **0 of 100,000** | 0.00% | 100% |
| **Cheat 2 (Partial Port)** | **352 of 2,000** | 17.60% | **90,758 of 100,000** | 90.76% | 0% |

### Key Observations
1. **No False Positives**: All three genuine Go implementations achieve 100.0% accuracy on both suites.
2. **Discriminative Power**: The new 100K suite exposes Cheat 2's failure across 90.76% of inputs (up from 17.60% on the old suite). A random 2,000-sample test from the 100K pool has a **0% chance** of missing Cheat 2's errors.

*Measurement files saved in*: `training-3/Paniv Kapoor/measure/`

---

## 10. Limitations and Scope of the Task

1. **API Scope**: The task implements `titlecase(text)` with default parameters: `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`. Optional parameters (`preserve_blank_lines=True`, `normalise_space_characters=True`) and custom abbreviation callbacks are excluded by specification.
2. **Execution Environment**: Input processing assumes standard UTF-8 text streams with POSIX line normalization (`\n`) as enforced by the verifier environment.
3. **Engine Assumptions**: Behavior strictly mirrors Python 3.12 standard-library `re` fallback mode (`REGEX_AVAILABLE = False`).
