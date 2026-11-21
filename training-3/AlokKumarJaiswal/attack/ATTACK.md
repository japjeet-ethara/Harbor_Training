# Defensive Review: Practice 1 — titlecase-go

- **Target Task:** `practice/titlecase-go`
- **Author:** Lokesh Deshwal
- **Target Commit:** `01d11b155117f1e8bd9e842c4a943789ca3bed0d`
- **Status:** Draft Defensive Review

---

## 1. Verified Results

### Standard Controls
| Control | Overall Reward | Build | No Python | Behaviour | Job ID |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Published Oracle** (Standard Control) | `1.000000` | 1 | 1 | `1.000000` | `lokesh-practice1-oracle-20261118-165055` |
| **Nop** (Standard Control) | `0.000000` | 0 | 0 | `0.000000` | `lokesh-practice1-nop-20261118-164751` |

### Measured Submissions
Five behaviour-only submissions were measured and the three highest-scoring submissions were selected; trainer acceptance remains unconfirmed. All had build 1, no_python 1, and zero exceptions.

| Submission | What it implements | Behaviour | Overall | Harbor job |
| :--- | :--- | :--- | :--- | :--- |
| **cheat1** | Compound-word control (capitalizes after hyphens and slashes; leaves interior small-word and all-caps handling out) | `0.359500` | `0.573000` | `lokesh-practice1-compound-control-20261118-184133` |
| **cheat2** | Capitalization with interior small words | `0.436000` | `0.624000` | `lokesh-practice1-small-words-control-20261118-180601` |
| **cheat3** | Combined partial port (handles interior small words, hyphen and slash compounds, all-caps normalization, and dotted initials; leaves URL exception and other rules incomplete) | `0.858000` | `0.905333` | `lokesh-practice1-combined-control-20261119-100151` |
| Baseline (unnumbered) | Basic first-character capitalization | `0.206500` | `0.471000` | `lokesh-practice1-basic-control-20261118-173105` |
| All-caps-only (unnumbered) | All-caps normalization with dotted initials preserved | `0.229500` | `0.486333` | `lokesh-practice1-all-caps-control-20261118-181636` |

### Summary of Results
- **Published Oracle (Standard Control):** Achieved `1.000000` overall reward (`build: 1`, `no_python: 1`, `behaviour: 1.000000`) in job `lokesh-practice1-oracle-20261118-165055`.
- **Nop (Standard Control):** Achieved `0.000000` overall reward (`build: 0`, `no_python: 0`, `behaviour: 0.000000`) in job `lokesh-practice1-nop-20261118-164751`.
- **cheat1:** Achieved `0.573000` overall reward (`build: 1`, `no_python: 1`, `behaviour: 0.359500`, zero exceptions) in job `lokesh-practice1-compound-control-20261118-184133` (trial `compound-titlecase-task__LbbZUCY`). It capitalizes after hyphens and slashes and leaves interior small-word and all-caps handling out. The compound control improved reported behaviour by 15.30 percentage points over basic capitalization.
- **cheat2:** Achieved `0.624000` overall reward (`build: 1`, `no_python: 1`, `behaviour: 0.436000`, zero exceptions) in job `lokesh-practice1-small-words-control-20261118-180601`.
- **cheat3:** Achieved `0.905333` overall reward (`build: 1`, `no_python: 1`, `behaviour: 0.858000`, zero exceptions) in job `lokesh-practice1-combined-control-20261119-100151` (trial `combined-titlecase-task__9BMwz5H`). It handles interior small words, hyphen and slash compounds, all-caps normalization, and dotted initials, leaving the URL exception and other titlecase rules incomplete.
- **Basic Capitalization (Unnumbered Baseline):** Achieved `0.471000` overall reward (`build: 1`, `no_python: 1`, `behaviour: 0.206500`, zero exceptions) in job `lokesh-practice1-basic-control-20261118-173105`.
- **All-Caps Only (Unnumbered Comparison):** Achieved `0.486333` overall reward (`build: 1`, `no_python: 1`, `behaviour: 0.229500`, zero exceptions) in job `lokesh-practice1-all-caps-control-20261118-181636`.

---

## 2. Findings & Vulnerability Analysis

### 2.1 Scoring Description Mismatch (`instruction.md:44`, `tests/test.sh:63`)
- `instruction.md:44` states:
  > *"Your solution will be graded automatically by hidden tests. Partial credit is awarded: the score is the fraction of test lines your program gets exactly right."*
- `tests/test.sh:63` computes reward as a weighted composite score:
  ```bash
  reward=$(awk "BEGIN { printf \"%.6f\", ($build_score * 1 + $no_python_score * 1 + $behaviour_score * 4) / 6 }")
  ```
- **Analysis:** Contrary to the instructions indicating that the score is purely based on line accuracy, the evaluation awards 1/6 for passing compilation (`build`) and 1/6 for the absence of `.py` files (`no_python`), while test line correctness (`behaviour`) accounts for only 4/6 of the overall reward. Under the formula, `0.333333` is the conditional reward when both structural checks score 1 and behaviour scores 0. By comparison, for the basic capitalization control, the verifier’s reported behaviour score was `0.206500`, yielding the measured overall reward of `0.471000`.

### 2.2 Tab-Delimited Comparison (`tests/test.sh:54`)
- In `tests/test.sh:54`, actual vs. expected outputs are compared using:
  ```bash
  matched=$(paste "$actual_file" "$TESTS_DIR/data/hidden_expected.txt" | awk -F'\t' '$1 == $2 { count++ } END { print count+0 }')
  ```
- **Analysis:** `paste` merges lines using a tab character (`\t`). If any actual or expected output lines contain tab characters, `awk -F'\t'` will split on those intra-line tabs, causing field misalignment where `$1` and `$2` no longer correspond to the complete actual and expected lines.
- The effect of the tab comparison on the measured score is unknown.

### 2.3 `.pyc` Check Gap (`tests/test.sh:24`)
- In `tests/test.sh:24`, the check for prohibited Python source files is implemented as:
  ```bash
  py_count=$(find "$WORKSPACE" -name "*.py" 2>/dev/null | wc -l)
  ```
- **Analysis:** This check only looks for files ending in `.py`. It does not detect compiled bytecode files (`.pyc`), `__pycache__` directories, or Python executed through alternative file naming or packaging mechanisms.

### 2.4 Reference Package in the Agent Image (`environment/Dockerfile:5`)
- In `environment/Dockerfile:5`, the reference implementation is installed directly into the container environment:
  ```dockerfile
  pip3 install --break-system-packages titlecase==2.4.1 && \
  ```
- **Analysis:** Having `titlecase==2.4.1` pre-installed inside the agent container makes the reference package accessible to the agent at runtime, providing an opportunity for agents to inspect or query the reference implementation.

---

## 3. Submission 1: cheat1 — Compound-Word Control

- **Raw Reward File:** [`results/cheat1-reward.json`](results/cheat1-reward.json)
- **What it implements:** Compound-word control. It capitalizes after hyphens and slashes and leaves interior small-word and all-caps handling out.
- **Harbor Job:** `lokesh-practice1-compound-control-20261118-184133`
- **Trial:** `compound-titlecase-task__LbbZUCY`
- **Verified Outcome:** Build: `1`, No Python: `1`, Exceptions: `0` (zero exceptions).
  - Behaviour Score: `0.359500`
  - Overall Reward: `0.573000`

### Behaviour Score Computation (`tests/test.sh:54`)
In `tests/test.sh:54`, the verifier compares the candidate binary's standard output on `hidden_inputs.txt` against `hidden_expected.txt`:
```bash
matched=$(paste "$actual_file" "$TESTS_DIR/data/hidden_expected.txt" | awk -F'\t' '$1 == $2 { count++ } END { print count+0 }')
behaviour_score=$(awk "BEGIN { printf \"%.6f\", $matched / $total }")
```
The behaviour score implies 719 matches under the verifier’s comparator on 2,000 lines:
$$\text{behaviour\_score} = \frac{719}{2000} = 0.359500$$
The effect of the tab-delimited comparator on these scores remains unknown, and the number of byte-exact matches is unverified.

### Structural Credit Addition (`tests/test.sh:63`)
In `tests/test.sh:63`, the verifier aggregates the overall reward:
```bash
reward=$(awk "BEGIN { printf \"%.6f\", ($build_score * 1 + $no_python_score * 1 + $behaviour_score * 4) / 6 }")
```
Successful compilation (`build = 1`) contributes $1/6$, and having zero `.py` files (`no_python = 1`) contributes $1/6$. Together, these two structural checks inject $2/6 = 0.333333$ of baseline structural credit before assessing any behavioural correctness. Factoring in the behaviour score weighted at $4/6$:
$$\text{reward} = \frac{1 \times 1 + 1 \times 1 + 0.359500 \times 4}{6} = \frac{2 + 1.438000}{6} = \frac{3.438000}{6} = 0.573000$$

### Baseline Comparison (Basic Capitalization)
Basic capitalization is kept as an unnumbered comparison baseline with job `lokesh-practice1-basic-control-20261118-173105`, behaviour `0.206500`, and overall reward `0.471000`. The compound control improved reported behaviour by 15.30 percentage points.

### Defensive Fix
1. **Test Hyphen and Slash Compounds Alongside URL Exception:** Propose testing hyphen and slash compounds alongside the public contract’s URL exception.
2. **Gate Structural Credit:** Require a minimum behavioural accuracy threshold (e.g., at least 50% or 75%) before awarding credit for compilation (`build`) and cleanliness (`no_python`), or score strictly on functional accuracy as advertised in `instruction.md:44`.

---

## 4. Submission 2: cheat2 — Capitalization with Interior Small Words

- **Raw Reward File:** [`results/cheat2-reward.json`](results/cheat2-reward.json)
- **What it implements:** Capitalization with interior small words. It defines an in-memory set of common English small words (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`). Words at the first or last index of a line are capitalized, while interior words present in the small words table are lowercased.
- **Harbor Job:** `lokesh-practice1-small-words-control-20261118-180601`
- **Verified Outcome:** Build: `1`, No Python: `1`, Exceptions: `0` (zero exceptions).
  - Behaviour Score: `0.436000`
  - Overall Reward: `0.624000`

### Behaviour Score Computation (`tests/test.sh:54`)
In `tests/test.sh:54`, the verifier executes the tab-delimited paste and match count:
```bash
matched=$(paste "$actual_file" "$TESTS_DIR/data/hidden_expected.txt" | awk -F'\t' '$1 == $2 { count++ } END { print count+0 }')
behaviour_score=$(awk "BEGIN { printf \"%.6f\", $matched / $total }")
```
The reported behaviour score of 0.436000 implies 872 matches under the verifier’s comparator, an inferred match count from the verified 2,000-line expected-output file:
$$\text{behaviour\_score} = \frac{872}{2000} = 0.436000$$
The effect of the tab-delimited comparator on these scores remains unknown, and these figures represent inferred match counts rather than confirmed byte-exact matches across the full lines.

### Structural Credit Addition (`tests/test.sh:63`)
In `tests/test.sh:63`, the verifier computes:
```bash
reward=$(awk "BEGIN { printf \"%.6f\", ($build_score * 1 + $no_python_score * 1 + $behaviour_score * 4) / 6 }")
```
The structural checks (`build = 1` and `no_python = 1`) contribute $2/6 = 0.333333$ of structural credit. The behaviour contribution contributes $(4 \times 0.436000)/6 = 1.744000 / 6 = 0.290667$. The combined score:
$$\text{reward} = \frac{1 \times 1 + 1 \times 1 + 0.436000 \times 4}{6} = \frac{2 + 1.744000}{6} = \frac{3.744000}{6} = 0.624000$$

### Defensive Fix
1. **Require Advanced Syntax Rules:** Test titlecasing rules that go beyond a simple interior word dictionary, including hyphenated compounds (`Step-by-Step`), subtitle capitalization following colons (`Movie: The Sequel`), contractions and possessives (`don't`, `O'Connor`), and custom ignore rules.
2. **Subtractive / Penalty Grading:** Deduct score when words are erroneously lowercased or improperly capitalized instead of simple match counting, penalizing naive dictionary lookups that miss contextual grammar.

---

## 5. Submission 3: cheat3 — Combined Partial Port

- **Raw Reward File:** [`results/cheat3-reward.json`](results/cheat3-reward.json)
- **What it implements:** Combined partial port. It handles interior small words, hyphen and slash compounds, all-caps normalization, and dotted initials. It leaves the URL exception and other titlecase rules incomplete.
- **Harbor Job:** `lokesh-practice1-combined-control-20261119-100151`
- **Trial:** `combined-titlecase-task__9BMwz5H`
- **Verified Outcome:** Build: `1`, No Python: `1`, Exceptions: `0` (zero exceptions).
  - Behaviour Score: `0.858000`
  - Overall Reward: `0.905333`

### Behaviour Score Computation (`tests/test.sh:54`)
In `tests/test.sh:54`, the verifier checks line matches:
```bash
matched=$(paste "$actual_file" "$TESTS_DIR/data/hidden_expected.txt" | awk -F'\t' '$1 == $2 { count++ } END { print count+0 }')
behaviour_score=$(awk "BEGIN { printf \"%.6f\", $matched / $total }")
```
The reported behaviour score of 0.858000 implies 1,716 matches under the verifier’s comparator across 2,000 lines:
$$\text{behaviour\_score} = \frac{1716}{2000} = 0.858000$$
The effect of the tab-delimited comparator on these scores remains unknown, and byte-exact matches remain unverified across the full lines.

### Structural Credit Addition (`tests/test.sh:63`)
In `tests/test.sh:63`, the verifier calculates:
```bash
reward=$(awk "BEGIN { printf \"%.6f\", ($build_score * 1 + $no_python_score * 1 + $behaviour_score * 4) / 6 }")
```
With `build = 1` and `no_python = 1` providing $2/6 = 0.333333$ of structural credit, and the behaviour component adding $(4 \times 0.858000)/6 = 3.432000 / 6 = 0.572000$:
$$\text{reward} = \frac{1 \times 1 + 1 \times 1 + 0.858000 \times 4}{6} = \frac{2 + 3.432000}{6} = \frac{5.432000}{6} = 0.905333$$

### Baseline Comparisons (Unnumbered Controls)
All-caps-only is kept as an unnumbered comparison with job `lokesh-practice1-all-caps-control-20261118-181636`, behaviour `0.229500`, and overall reward `0.486333`. Basic capitalization is kept as the other unnumbered comparison with job `lokesh-practice1-basic-control-20261118-173105`, behaviour `0.206500`, and overall reward `0.471000`.

### Defensive Fix
1. **Byte-Exact Comparison:** Replace the tab-delimited paste comparison with a strict byte-exact comparison across full lines, ensuring intra-line tab characters do not misalign comparison fields and unverified matches are avoided.
2. **Cases Combining Documented Rules with the URL Exception:** Propose cases that combine documented rules with the URL exception, ensuring that partial ports omitting the URL exception cannot attain near-perfect scores.

---

## 6. Review Summary & Submission Status

Five behaviour-only submissions were measured and the three highest-scoring submissions were selected; trainer acceptance remains unconfirmed. Published Oracle and Nop remain identified as standard controls.

Highest measured submission score — 0.905333 (cheat3)

---

## Day 6 retest — Lokesh Deshwal’s hardened task

I retested Lokesh’s task at commit `dcbe88466f7281cfb7969a6ff9288f2be331de32`. Each submission ran in a fresh copy with only `solution/solve.sh` replaced. The oracle used the published solution. All five Harbor runs reported zero trial exceptions.

| Run | Day 4 reward | Day 6 reward | Harbor job |
| --- | ---: | ---: | --- |
| Cheat 1 — compound words | 0.573000 | 0.0 | `lokesh-day6-cheat1-20261120-155620` |
| Cheat 2 — interior small words | 0.624000 | 0.0 | `lokesh-day6-cheat2-20261120-155730` |
| Cheat 3 — combined partial port | 0.905333 | 0.0 | `lokesh-day6-cheat3-20261120-155840` |
| Published oracle | 1.0 | 1.0 | `lokesh-day6-oracle-20261120-160100` |
| New control — omit the `Mc` rule | — | 0.0 | `lokesh-day6-mc-omission-20261120-162242` |

The new control built in a separate smoke test. It returned `The Story of Mcdonald` for `the story of mcdonald`, while the Python reference returns `The Story of McDonald`.

The verifier zeros all reported components when raw behaviour is below 0.98. The published zeroes alone cannot establish raw accuracy or build status inside Harbor. The verified outcome is that all three original submissions scored below 0.2 and the published oracle retained its 1.0 score.

### Static Review: tests/test.sh

Static review of `tests/test.sh`: the comparator does not check that output and reference have the same number of lines, and the verifier ignores the candidate’s exit status. Recommend requiring a successful exit and checking the full output line count before awarding credit. Reading tests/test.sh showed that the comparator does not check whether the output and reference have the same number of lines, and the verifier ignores the candidate’s exit status. Require a successful exit and verify that the line counts match before awarding credit.
