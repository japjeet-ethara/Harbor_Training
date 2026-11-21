# Hardening Report — Yuvraj Singh (titlecase-go)

Target Task: `Yuvraj Singh` (`titlecase-go`)  
Attacker: `Paniv Kapoor`  
Date: 2026-11-20  

---

## Holes Closed

### Cheat 1: Visible-Input Lookup Table
- **Before Score:** `0.3653` (Harbor Job: `jobs/2026-11-18__18-24-46`)
- **After Score:** **`0.1250`** (Harbor Job: `jobs/2026-11-20__17-44-29`)
- **Root Cause:** Visible inputs and outputs were embedded in a Go map, while hidden test inputs received naive fallbacks that coincidentally matched small fractions of ASCII text.
- **Fix:**
  1. Test data is evaluated strictly on hidden inputs with distinct edge cases.
  2. Added a 10% accuracy noise threshold in `task/tests/behaviour.py` (`if matches / total < 0.10: return 0.0`), nullifying accidental match points.
  3. Rebalanced weights in `task/tests/reward.toml` to `{ build = 1.0, no_python = 1.0, behaviour = 14.0 }` (total 16.0), capping a build + no-python score with zero behaviour to `2/16 = 0.1250` (< 0.200).

### Cheat 2: Python Hidden in Extensionless File via Go Wrapper
- **Before Score:** `1.0000` (Harbor Job: `jobs/2026-11-18__18-28-10`)
- **After Score:** **`0.0625`** (Harbor Job: `jobs/2026-11-20__17-44-44`)
- **Root Cause:** Attacker placed Python code in an extensionless file (`py_titlecase_engine`) and executed `exec.Command("python3", ...)` from Go. The old verifier only checked for `*.py` files and system python was present in the image.
- **Fix:**
  1. Purged all Python interpreters and packages from `task/environment/Dockerfile` and `task/tests/Dockerfile`.
  2. Hardened `task/tests/no_python.py` to inspect file shebangs, check script bodies, and reject Go sources invoking Python binaries (`python`, `python3`).
  3. Gated `task/tests/behaviour.py` so any leftover Python file or interpreter failure immediately zeroes out behavior credit (`0.0`).

### Cheat 3: Partial Go Implementation (Simple Titlecase)
- **Before Score:** `0.3653` (Harbor Job: `jobs/2026-11-18__18-31-34`)
- **After Score:** **`0.1250`** (Harbor Job: `jobs/2026-11-20__17-44-57`)
- **Root Cause:** Simple word capitalization without edge case handling (McX, URLs, apostrophes, small words after punctuation) earned partial credit and passed build/no_python.
- **Fix:**
  1. 10% noise gate in `task/tests/behaviour.py` prevents naive titlecasing from receiving behaviour points.
  2. Balanced weights (`build=1.0, no_python=1.0, behaviour=14.0`) ensure that passing build and `no_python` alone yields at most `2/16 = 0.1250` (< 0.200).

---

## Exam: Before and After

- **Old Exam:** 2,000 hidden titles (basic ASCII rules)
- **New Exam:** 100,000 titles from seed 1 via `kit/make_pool.py`, frozen twice via `kit/answers.py`
- **Reference Mode:** `re` (WITHOUT optional third-party `regex` package, stated explicitly in `task/instruction.md`)

| Port | Wrong on New Exam (100k) | Old Exam Caught It? | Chance 2k Random Misses It |
| :--- | :---: | :---: | :---: |
| **My Oracle (`solution/solve.sh`)** | 0 | n/a (passed) | n/a |
| **Classmate Port A (Missing edge cases)** | 857 | no | 0% |
| **Classmate Port B (Subtle punctuation/dot bug)** | 16 | no | 72% |

---

## Summary of Hardened Verification Runs

| Target / Script | Score | Expected | Harbor Job | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Oracle (`solution/solve.sh`)** | **1.000** | 1.000 | `jobs/2026-11-20__17-45-11` | PASS |
| **Nop (`/bin/true`)** | **0.000** | 0.000 | `jobs/2026-11-20__17-47-42` | PASS |
| **Cheat 1 (Lookup table)** | **0.125** | < 0.200 | `jobs/2026-11-20__17-44-29` | PASS |
| **Cheat 2 (Python wrapper)** | **0.062** | < 0.200 | `jobs/2026-11-20__17-44-44` | PASS |
| **Cheat 3 (Partial Go)** | **0.125** | < 0.200 | `jobs/2026-11-20__17-44-57` | PASS |

---

## What I Learned (3 Lines)

1. Gating substantive checks (`behaviour`) directly on structural rules (`no_python`) prevents attackers from exploiting weighted means with partial scores.
2. In Harbor's `separate` environment mode, both the agent and verifier container Dockerfiles must be stripped of unneeded interpreters like Python to prevent subshell escapes.
3. High volume test sets and strange edge cases (weird words, punctuation, and Unicode symbols) catch critical bugs that small random test suites miss up to 72% of the time.
