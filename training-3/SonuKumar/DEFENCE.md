# Day 6 Defence Report: `titlecase-go`

- **Maintainer**: Sonu Kumar
- **Repository**: `Harbor_Training` (Branch: `training-3`)
- **Main Workspace**: `Harbor_Day4_Workspace/Sonu Kumar/`
- **Assigned Attacker**: Ayush Parasher (commit `50af008cd3074a19282cc0bfc5d8b07a448fe4ed`)
- **Evaluation Harness**: Harbor 0.25.0 (`golang:1.23`, Docker / Ubuntu WSL)
- **Scoring Policy**: Policy B with Quadratic Behaviour Scoring (`build = 0.5`, `no_python = 0.5`, `behaviour = 9.0`; Total = 10.0)
- **Reference Specification**: `python-titlecase 2.4.1`, mode: **WITHOUT regex** (`REGEX_AVAILABLE = False`)

---

## 1. Final Hardening

To suppress weak partial Go ports below the 0.2000 threshold without resorting to fragile all-or-nothing step cutoffs (such as 95% or 99% hard cliffs), we applied **quadratic behavioural scoring** within `task/tests/criteria.py`:

```python
matching = sum(a == e for a, e in zip(actual, expected))
accuracy = matching / max(len(actual), len(expected))
return accuracy ** 2
```

Under our adopted Policy B weights (`build = 0.5`, `no_python = 0.5`, `behaviour = 9.0` out of 10.0 total):
$$\text{Reward} = \frac{0.5 \times \text{build} + 0.5 \times \text{no\_python} + 9.0 \times (\text{accuracy})^2}{10.0}$$

This adjustment preserves mathematical continuity and strict monotonicity: every additional correct line increases the score, a fully compliant Oracle retains `1.0 ** 2 = 1.0` (100% credit), while incomplete heuristic implementations that only solve the easiest subset of cases have their behavioural contribution convexly suppressed.

---

## 2. Strongest Cheat Before and After

The strongest attack against our hardened task was **Cheat 4 (Half-Port Go)**, authored by Ayush Parasher:
- **Technique**: A 107-line pure Go implementation (`training-3/AyushParasher/attack/cheat4/solve.sh`) implementing standard capitalization, lowercase small words, internal uppercase retention, and all-caps downcasing, but omitting Mc-prefixes, apostrophes, hyphen/slash recursion, acronyms, and Unicode normalization.
- **Why It Earned Partial Credit**: Cheat 4 is a genuine Go program that solved **32,630 of 100,000 titles (32.63% accuracy)**. Under linear scoring, 32.63% accuracy contributed $9.0 \times 0.3263 = 2.9367$ points, yielding an authentic reward of **`0.3936`** in job `jobs/2026-11-20__08-38-02`.
- **Authentic Fresh Harbor Result After Quadratic Hardening**:
  - **Harbor Job**: `jobs/2026-11-21__01-24-18` (trial: `final_eval_cheat4__AZYhqLW`)
  - **Criterion Breakdown**: `build = 1.0`, `no_python = 1.0`, `behaviour = 0.1065` (raw: $0.3263^2 = 0.106452$)
  - **Calculation**: $(0.5 \times 1.0 + 0.5 \times 1.0 + 9.0 \times 0.106452) / 10.0 = 1.95807 / 10.0 = \mathbf{0.1958}$
  - **Status**: **`0.1958 < 0.2000` [PASS]**. The strongest cheat is now fully suppressed below 0.20.

---

## 3. Final Proof Results

All six required fresh evaluations were executed in Harbor 0.25.0 against the final hardened task:

| Evaluation Target | Agent / Candidate | Authentic Reward | Harbor Job Folder | Criterion Breakdown (`build` / `no_py` / `behav`) | Threshold Check |
|---|---|:---:|---|---|:---:|
| **Genuine Oracle** | `oracle` | **`1.0000`** | `jobs/2026-11-21__01-16-20` | `1.0` (0.50 pts) / `1.0` (0.50 pts) / `1.0000` (9.00 pts) | Exact `1.0` [PASS] |
| **Nop Baseline** | `nop` | **`0.0000`** | `jobs/2026-11-21__01-18-08` | `0.0` (0.00 pts) / `0.0` (0.00 pts) / `0.0000` (0.00 pts) | Exact `0.0` [PASS] |
| **Cheat 1 (Delete + Echo)** | `oracle` | **`0.0502`** | `jobs/2026-11-21__01-19-32` | `1.0` (0.50 pts) / `0.0` (0.00 pts) / `0.0002` (0.0017 pts) | `< 0.2000` [PASS] |
| **Cheat 2 (Read Exam)** | `oracle` | **`0.0502`** | `jobs/2026-11-21__01-21-10` | `1.0` (0.50 pts) / `0.0` (0.00 pts) / `0.0002` (0.0017 pts) | `< 0.2000` [PASS] |
| **Cheat 3 (Python Wrapper)**| `oracle` | **`0.0500`** | `jobs/2026-11-21__01-22-44` | `1.0` (0.50 pts) / `0.0` (0.00 pts) / `0.0000` (0.0000 pts) | `< 0.2000` [PASS] |
| **Cheat 4 (Half-Port Go)** | `oracle` | **`0.1958`** | `jobs/2026-11-21__01-24-18` | `1.0` (0.50 pts) / `1.0` (0.50 pts) / `0.1065` (0.9581 pts) | `< 0.2000` [PASS] |

*Proof Files Generated*:
- `proof/oracle-reward.json` (SHA-256: `CA274AA96D4535004E2C8D61633D4DEA80C26CB38C9F5C3F143BA21147174DFF`)
- `proof/nop-reward.json` (SHA-256: `7AF50836F84864C1BF8FC1D78CD10520662F9166B688F8252CC5609ACC886FF5`)
- `proof/cheats-reward.txt` (SHA-256: `F29483AA940F4C0A3C2A59A7C99384DCC2E95DECE1EEB9A6E43542EF659AAFDF`)

---

## 4. Three-Port Measurement

Using the trainer's unmodified `kit/compare.py` against `key/` (verified outputs in `measure/`):

| Port Author | Implementation Architecture | Lines of Go | Wrong Answers (100K) | Raw Accuracy (%) | Old 2K Exam Mismatches | Chance 2K Misses All Bugs |
|---|---|---:|---:|---:|:---:|:---:|
| **Sonu Kumar (Oracle)** | Native non-regex Go state machine | 319 | **0 / 100,000** | **100.00%** | 0 wrong | 100% |
| **Sanyam Sehrawat** | Go `regexp` port (regex-branch rules) | 447 | **3,053 / 100,000** | **96.95%** | 0 wrong | 0% |
| **Alok Kumar Jaiswal** | Procedural rune scanner without `regexp` | 679 | **28,064 / 100,000** | **71.94%** | 0 wrong | 0% |

### Analysis of Port Divergence
1. **Sanyam Sehrawat (3,053 mismatches)**: Followed the third-party `regex` module behavior rather than standard library `re`. The 100K pool exposed subtle regex-mode discrepancies (such as version numbers like `v1.2` $\to$ `V1.2`).
2. **Alok Kumar Jaiswal (28,064 mismatches)**: Failed on non-ASCII Unicode letter capitalization (Greek `αlpha` $\to$ `Αlpha`), non-breaking spaces (`\xa0`), thin spaces (`\u2009`), backslash separators, and compound punctuation boundaries.
3. **Old Exam Weakness**: Both ports scored 100% on the old 2,000-case exam. A random 2,000-case draw has a 0% statistical probability of missing all 3,053 or 28,064 errors if titles are uniformly distributed. The old test suite failed to catch them due to poor structural edge-case coverage.

---

## 5. Surprising Discovery

The most significant technical discovery was that **Sanyam Sehrawat's reference Oracle failed its own hardened grader in Harbor (`jobs/2026-11-20__18-57-24`) with an authentic score of 0.1667 (0 / 100,000 matches)**.

Investigation revealed that Sanyam committed the 100,000-line answer dataset using Windows CRLF (`\r\n`) line endings, protected from Git conversion by `.gitattributes`. His Go verifier (`tests/grade.go:117`) split answers on `\n` without stripping `\r`, leaving trailing `0x0D` bytes on every expected line. Because standard POSIX programs print LF lines via `fmt.Println`, every comparison failed byte-equality checks. This exposed how subtle line-ending parsing bugs in verifiers can catastrophically invalidate reference solutions.

---

## 6. Remaining Limitations

1. **Kernel DAC Boundaries vs Deep Isolation**: File system permissions (`0700 root:root`) and unprivileged user accounts (`nobody`) effectively block direct file reads and system binaries, but they do not provide full container namespacing (seccomp, eBPF, network namespaces) against kernel-level privilege escalation or memory inspection if the untrusted binary were to exploit kernel vulnerabilities.
2. **Static Import Analysis Limits**: Checking `go list` imports detects explicit dependencies on `os/exec` or `syscall`, but cannot prevent obfuscated syscalls invoked via direct assembly stubs (`.s` files) or dynamic runtime manipulation if Go cgo or raw assembly were permitted.
3. **Empirical Robustness vs Formal Proof**: Defeating the three specific demonstrated attacks confirms resilience against the known attack surface, but does not constitute mathematical proof of immunity against novel, unmodeled side-channel attacks, CPU timing leaks, or grader memory inspection.

---
