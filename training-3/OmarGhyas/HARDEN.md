# HARDEN.md — Day 5: Harden Your Own Task

Task: `OmarGhyas/task` (`titlecase-go`)  
Attacker: **Ashish** — report at `Ashish-Reference/attack/ATTACK.md` (target commit `1aea2bf3fb67c8ec034a3c9467c011c4c65e1514`)  
Hardened evaluation runs conducted with Harbor (`golang:1.23`, `harbor-rewardkit==0.2.*`).

---

## 1. Holes closed

All three cheats identified in Ashish's attack report scored above 0.20 on the original task. Following the hardening changes in Step 5.2, all three cheats now score ≤ 0.037 (well below 0.20), while the genuine Oracle retains a perfect 1.0000 score.

| Cheat | Original Score | Hardened Score | Job / Result Proof | Primary Vulnerability | Fix Applied |
|---|---|---|---|---|---|
| **Cheat 1: Lookup table** | **0.3897** | **0.0000** | `hardened_results/cheat1.json` (`titlecase-go__xQ6dDls`) | Leaked answers in container + identity fallback + structural floor | Removed `visible.jsonl` COPY from `Dockerfile`, gated behaviour on prerequisites, filtered fixed points in data generator |
| **Cheat 2: Half port** | **0.7213** | **0.0370** | `hardened_results/cheat2.json` (`titlecase-go__Z7F2jdf`) | Free structural points (2/6) + weak representation of complex rules | Shifted 100% weight to behaviour, added dense complex categories (acronyms, hyphens, prefixes, subphrases) |
| **Cheat 3: Silent binary** | **0.3333** | **0.0000** | `hardened_results/cheat3.json` (`titlecase-go__wTkm1Wl`) | Structural floor awarded for compiling and deleting `.py` files | Gated behavioural credit behind `build` and `no_python` checks with 0.0 standalone weight |

### Detailed Cheat Fixes

### Cheat 1 — Lookup table (`cheat1/solve.sh`)
- **Original score before hardening:** `0.3897` (build: 1.0, no_python: 1.0, behaviour: 0.0845 [169/2,000 matches from unchanged identity inputs], overall: `(1 + 1 + 4 × 0.0845) / 6 = 0.3897`).
- **Score after hardening:** `0.0000` (build: 1.0, no_python: 1.0, behaviour: 0.0000 with weight 1.0 on behaviour).
- **Specific fixes applied:**
  1. Removed line 4 (`COPY titlecase-go/tests/data/visible.jsonl /workspace/repo/visible.jsonl`) from `environment/Dockerfile`, completely preventing visible answer leakage to the agent workspace.
  2. Set structural weights in `tests/reward.toml` to `weights = { build = 0.0, no_python = 0.0, behaviour = 1.0 }`.
  3. Made compilation and absence of Python files strict prerequisites inside `tests/support.py` (`if not go_build_succeeds(workspace) or not python_files_absent(workspace): return 0.0`).
  4. Modified `tests/generate_data.py` to filter out fixed-point inputs where `titlecase(text) == text`, preventing fallback echoes from earning any behavioural matches.

### Cheat 2 — Half port (`cheat2/solve.sh`)
- **Original score before hardening:** `0.7213` (build: 1.0, no_python: 1.0, behaviour: 0.5820 [1,164/2,000 matches], overall: `(1 + 1 + 4 × 0.5820) / 6 = 0.7213`).
- **Score after hardening:** `0.0370` (build: 1.0, no_python: 1.0, behaviour: 0.0370 [74/2,000 matches], overall: `0.0370`).
- **Specific fixes applied:**
  1. Eliminated the unearned 0.3333 base score by setting structural weights to 0.0 and allocating 100% of reward to behavioural correctness.
  2. Significantly expanded and deepened complex category generation in `tests/generate_data.py`:
     - Added lowercased consonant acronyms (`http`, `sql`, `xml`, `html`) that require full capitalization.
     - Added subphrase boundaries with small words (`: an`, ` - the`, `; on`).
     - Added hyphenated and slash compounds (`step-by-step`, `and/or`, `follow-up`).
     - Added apostrophe stems and proper names (`o'reilly`, `d'angelo`).
     - Added `Mc`/`Mac` surname prefix patterns (`mcdonald`, `macneil`).
     - Added all-caps downcasing rules and non-breaking space preservation.
  3. With the test suite densely testing the complete Python titlecase 2.4.1 specification, the naive half-port's match rate plummeted from 58.2% to 3.7%.

### Cheat 3 — Silent binary (`cheat3/solve.sh`)
- **Original score before hardening:** `0.3333` (build: 1.0, no_python: 1.0, behaviour: 0.0000, overall: `(1 + 1 + 4 × 0.0) / 6 = 0.3333`).
- **Score after hardening:** `0.0000` (build: 1.0, no_python: 1.0, behaviour: 0.0000, overall: `0.0000`).
- **Specific fixes applied:**
  1. Reconfigured `tests/reward.toml` to award points exclusively for behavioural accuracy (`behaviour = 1.0`, `build = 0.0`, `no_python = 0.0`).
  2. Enforced `build` and `no_python` as gates in `tests/support.py`: a binary that compiles and has no Python files must still correctly process inputs. A silent binary that outputs zero lines matches 0 inputs and receives a final score of 0.0000.

---

## 2. Exam: before and after

- **Old exam:** 2,000 inputs (`tests/data/hidden.jsonl`, generated with seed 1).
- **New exam:** 100,000 inputs (`tests/data/inputs.txt`, answers frozen in `tests/data/answers.txt` via `kit/answers.py`).
- **Mode:** `regex` (using Python `titlecase 2.4.1` with the `regex` module enabled, as explicitly specified in `task/instruction.md`).

### Port Comparison Table

The following measurements were obtained by running each port in Docker (`golang:1.23`, `--network none`) against all 100,000 inputs and evaluating with `kit/compare.py key got.txt 2000`:

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---|---|---|
| `my-oracle` | 0 of 100000 | No (0 errors; 100% pass) | 100% |
| `AlokKumarJaiswal` | 30142 of 100000 | Yes (301 of 2000 errors) | 0% |
| `AmanTiwari` | 3053 of 100000 | Yes (29 of 2000 errors) | 0% |

### Analysis of Results
- **`my-oracle` (`solution/solve.sh`)**: Achieves 0 wrong answers across all 100,000 inputs. The Go port perfectly reproduces Python `titlecase 2.4.1` with `regex` mode, confirming zero false positives in the enlarged exam suite.
- **`AlokKumarJaiswal`**: Fails on 30,142 inputs (30.14% error rate). The port misses key titlecasing rules including punctuation boundaries (e.g., `war\xa0\\data\u2009%summer`), subphrase casing, multi-word hyphenation/slashes, and Greek/Unicode capitalization. When evaluated against the actual original pre-hardening 2,000-input hidden exam (`git HEAD`), it failed 301 of 2,000 inputs (15.05%), confirming the old exam caught it (`Yes`). (Note: when evaluated against the Step 5.2 hardened 2,000-input working copy dataset, it failed 183 of 2,000 inputs).
- **`AmanTiwari`**: Fails on exactly 3,053 inputs (3.05% error rate). This failure is a clean mode mismatch: Aman's port targeted the standard Python `re` mode, whereas our task specification explicitly mandates the `regex` module mode. The differences are concentrated in version strings (e.g. `v1.2` $\rightarrow$ `V1.2`) and Unicode regex patterns. When evaluated against the actual original pre-hardening 2,000-input hidden exam (`git HEAD`), it failed 29 of 2,000 inputs (1.45%), confirming the old exam caught it (`Yes`). (Note: when evaluated against the Step 5.2 hardened 2,000-input working copy dataset, it failed 6 of 2,000 inputs).
- **Probability Values**: The values in the "Chance 2K random misses it" column (`100%`, `0%`, `0%`) strictly reflect the exact output of the comparison script (`kit/compare.py`) as recorded in `measure/my-oracle.txt`, `measure/AlokKumarJaiswal.txt`, and `measure/AmanTiwari.txt`.

---

## 3. What I learned (3 lines)

1. Awarding standalone points for structural actions like compiling or removing files creates an unearned scoring floor that cheats can easily exploit without solving the actual task.
2. Hardening task evaluation requires gating behavioural credit behind prerequisite checks and eliminating fixed-point inputs so that fallback heuristics cannot earn unearned matches.
3. Scaling to a 100,000-input exam transforms edge-case detection from statistical chance to certainty, cleanly isolating subtle specification differences like `regex` versus `re` engine semantics.
