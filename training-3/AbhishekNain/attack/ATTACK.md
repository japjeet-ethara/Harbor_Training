# Day 4 Harbor Attack Report

**Author:** Abhishek Nain  
**Audience:** Mukul Bhardwaj and the Trainer  
**Target:** Mukul Bhardwaj, `training-3/MukulBhardwaj/task/`  
**Pinned Commit:** `a2bca77533dfe5c49b16c9c406d29dd5a2332039`  

---

## Target and Baseline

I evaluated the titlecase grader built by Mukul Bhardwaj (`training-3/MukulBhardwaj/task/`) pinned at Git revision `a2bca77533dfe5c49b16c9c406d29dd5a2332039` (recorded in `TARGET.txt`). All evaluations were executed using scratch copies of this pinned task in Harbor, where each control replaced only the scratch copy's `solution/solve.sh` while keeping the environment, verification harness, and test suite completely untouched.

Before evaluating adversarial and heuristic controls, I verified two standard baselines on this pinned revision:

1. **Unmodified Oracle (`mukul-baseline-a2bca77-oracle-01`):**  
   The reference oracle solution executed against the verifier and achieved a perfect score across all metrics:
   - `behaviour`: `1.0`
   - `build`: `1.0`
   - `no_python`: `1.0`
   - `reward`: `1.0`

2. **No-op Control (`mukul-baseline-a2bca77-nop-01`):**  
   The no-op agent made no changes to the repository and scored zero on every check:
   - `behaviour`: `0.0`
   - `build`: `0.0`
   - `no_python`: `0.0`
   - `reward`: `0.0`

---

## Primary Controls Summary

Below are the verified results for the three primary controls evaluated against Mukul's pinned task.

| Control | Job | Behaviour | Build | no_python | Overall | Reward file |
| :--- | :--- | ---: | ---: | ---: | ---: | :--- |
| 1. Echo only | `mukul-a2bca77-echo-control-02` | 0.096 | 1.0 | 0.0 | 0.2307 | [`results/cheat1-reward.json`](results/cheat1-reward.json) |
| 2. Build only | `mukul-a2bca77-build-only-control-01` | 0.0 | 1.0 | 0.0 | 0.1667 | [`results/cheat2-reward.json`](results/cheat2-reward.json) |
| 3. Simple ASCII capitalization | `mukul-a2bca77-simple-caps-control-01` | 0.4295 | 1.0 | 0.0 | 0.453 | [`results/cheat3-reward.json`](results/cheat3-reward.json) |

The overall reward calculation follows `tests/reward.toml:3–4`:
$$\text{weights} = \{ \text{build}: 1.0, \text{no\_python}: 1.0, \text{behaviour}: 4.0 \}$$
$$\text{Overall Reward} = \frac{\text{build} \times 1.0 + \text{no\_python} \times 1.0 + \text{behaviour} \times 4.0}{6.0}$$

---

## Primary Control 1: Echo Only (`cheat1`)

- **Job Name:** `mukul-a2bca77-echo-control-02`
- **Saved Reward File:** [`results/cheat1-reward.json`](results/cheat1-reward.json)
- **Measured Scores:**
  - `behaviour`: `0.096`
  - `build`: `1.0`
  - `no_python`: `0.0`
  - `reward`: `0.2307`

### What It Does
The echo control sets up a Go module (`harbor.local/echo-control`) whose standard-library program executes `io.Copy(os.Stdout, os.Stdin)`, streaming standard input directly to standard output byte for byte without any string transformation or titlecasing logic. It removes `.py` files within `/workspace/repo` and compiles with `go build ./...`.

### Why It Earned That Credit
In the verifier, `tests/behaviour/check.py:96–101` counts exact output-line matches between the runner output and the expected output:
```python
record_count = max(len(actual), len(expected))
matches = sum(
    actual[index] == expected[index]
    for index in range(min(len(actual), len(expected)))
)
return matches / record_count
```
Because some input titles are already in titlecase or require no modification, returning stdin verbatim yields exact matches for those lines. The echo control matched 9.6% of expected output lines (`behaviour: 0.096`). Together with full credit on compilation (`build: 1.0`, contributing $1.0 / 6.0 \approx 0.1667$), the weighted calculation $\frac{1.0 + 4.0 \times 0.096}{6.0} = \frac{1.384}{6.0}$ rounds to `0.2307`.

### Proposed Improvement
To address unearned credit from a trivial echo program, the test dataset should retain valid unchanged cases while adding more representative transformation cases, which could reduce the credit earned by echoing.

---

## Primary Control 2: Build Only (`cheat2`)

- **Job Name:** `mukul-a2bca77-build-only-control-01`
- **Saved Reward File:** [`results/cheat2-reward.json`](results/cheat2-reward.json)
- **Measured Scores:**
  - `behaviour`: `0.0`
  - `build`: `1.0`
  - `no_python`: `0.0`
  - `reward`: `0.1667`

### What It Does
The build-only control defines a Go module (`harbor.local/build-only-control`) that consumes standard input via `io.Copy(io.Discard, os.Stdin)` and emits zero bytes to standard output. It deletes `.py` files inside `/workspace/repo` and executes `go build ./...`.

### Why It Earned That Credit
The verifier checks compilation in `tests/build/check.py:11–20`:
```python
result = subprocess.run(
    ["go", "build", "./..."],
    cwd=workspace,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    timeout=120,
    check=False,
)
...
return result.returncode == 0
```
Because the Go program is valid syntax and compiles cleanly, `build_passes` returns `True` (`score: 1.0`). Under `tests/reward.toml:3–4`, `build` is assigned a weight of `1.0` out of a total weight of `6.0` ($1/6 \approx 0.1667$). Emitting zero bytes matches none of the expected output lines (`behaviour: 0.0`), so the entire `0.1667` reward stems purely from structural compilation.

### Proposed Improvement
I propose that the grader should award `build` credit only after checking for exact expected output on a known nonempty case, as simply checking for nonempty output is too weak.

---

## Primary Control 3: Simple ASCII Capitalization (`cheat3`)

- **Job Name:** `mukul-a2bca77-simple-caps-control-01`
- **Saved Reward File:** [`results/cheat3-reward.json`](results/cheat3-reward.json)
- **Measured Scores:**
  - `behaviour`: `0.4295`
  - `build`: `1.0`
  - `no_python`: `0.0`
  - `reward`: `0.453`

### What It Does
This control implements a naive single-rule capitalization program (`harbor.local/simple-caps-control`). It iterates over standard input, uppercasing the first ASCII letter (`'a'`–`'z'` to `'A'`–`'Z'`) in each space- or tab-delimited word while preserving all other bytes, whitespace, and line endings. It ignores all titlecase rules regarding small words, hyphenated compounds, apostrophes, acronyms, and phrase boundaries.

### Why It Earned That Credit
Because `tests/behaviour/check.py:96–101` evaluates line-by-line equality, any input title whose correct titlecased form coincides with simple first-letter capitalization will match byte-for-byte. In Mukul's test run, this naive approximation matched 42.95% of the test lines (`behaviour: 0.4295`). Combined with the build credit of `1.0`, the composite reward reached `0.453` ($\frac{1.0 + 4.0 \times 0.4295}{6.0} = 0.453$).

### Proposed Improvement
The test suite should incorporate more test cases that specifically separate simple first-letter capitalization from compliant titlecase behavior. In particular, adding cases that test interior small words (e.g., "in", "of", "the"), contractions and apostrophes (e.g., "don't", "O'Connor"), and phrase boundary capitalization will distinguish full ports from superficial heuristics. These represent prospective coverage improvements; the evaluation run measured aggregate behaviour only without classifying individual gains or failures.

---

## Follow-up Experiment: Small-Word Capitalization Control

As a follow-up to Control 3, I ran a local experiment (`training-3/AbhishekNain/attack/target/experiments/small-words/solve.sh`) introducing a single additional titlecasing rule: lowercasing standalone occurrences of a fixed list of thirteen small words (`a`, `an`, `and`, `as`, `at`, `by`, `for`, `in`, `of`, `on`, `or`, `the`, `to`) when they appear strictly between the first and last words of a line.

- **Job Name:** `mukul-a2bca77-small-words-control-01`
- **Measured Scores:**
  - `behaviour`: `0.5200`
  - `build`: `1.0`
  - `no_python`: `0.0`
  - `reward`: `0.5133`

### Analysis
Adding this single interior small-words rule increased the behaviour score from `0.4295` to `0.5200`, yielding a measured net increase of **9.05 percentage points** in aggregate behaviour. The overall reward rose from `0.453` to `0.5133`. The runs measured aggregate behaviour only and did not classify individual gains or failures.

---

Highest of the three primary controls: 0.453. Highest among the incomplete submissions tested: 0.5133 (small-word follow-up). The unmodified oracle scored 1.0.
