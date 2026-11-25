# Attack on Annu Kumari's `titlecase-go` task

## Test status

All three attacks were executed through real Harbor jobs using the `oracle` agent. Results below are taken from the actual verifier `reward.json` files, not local emulation.

**Target:** See `TARGET.txt`.

**Experiment isolation:** Each attack used an independent copy of the target task. Only `solution/solve.sh` was replaced in each experiment. The original target was preserved.

## Actual Harbor results

| Attack | Behaviour | Build | No Python | Reward |
|---|---:|---:|---:|---:|
| Cheat 1 | 0.1255 | 1.0 | 1.0 | 0.417 |
| Cheat 2 | 0.1255 | 1.0 | 1.0 | 0.417 |
| Cheat 3 | 1.0000 | 1.0 | 1.0 | 1.000 |

### Cheat 1 — Lookup table (visible answers + half-port fallback)

**What it does:** Embeds the 2,000 visible input/output pairs as a Go map. Other inputs use the simplified fallback rules from Cheat 2.

**Actual Harbor score:** 0.417
**Behaviour:** 0.1255
**Build:** 1.0
**No Python:** 1.0

**Job folder:** `results/cheat1/cheat1__f232NkB/`

**Reward evidence:** `results/cheat1/cheat1__f232NkB/verifier/reward.json`

**Why it performed poorly:** The hidden inputs differ from the visible inputs, so the lookup table provides little benefit. The simplified fallback does not reproduce the full titlecase behaviour.

**Suggested fix:** No specific fix is required for this attack beyond maintaining distinct hidden test data.

### Cheat 2 — Half port (easy rules only)

**What it does:** Uses a short Go implementation that splits on spaces, lowercases small words except at the beginning and end, capitalises the first letter of other words, and leaves certain all-caps and mixed-case words unchanged.

**Actual Harbor score:** 0.417
**Behaviour:** 0.1255
**Build:** 1.0
**No Python:** 1.0

**Job folder:** `results/cheat2/cheat2__9BLuo9x/`

**Reward evidence:** `results/cheat2/cheat2__9BLuo9x/verifier/reward.json`

**Why it performed poorly:** Exact line-by-line comparison exposes differences involving Unicode whitespace, punctuation, dashes, tabs, apostrophes, and other edge cases.

However, the build and no-Python criteria still award credit even though the implementation is incomplete.

**Suggested fix:** Consider making behavioural correctness a prerequisite for reward, or reducing the independent reward contribution of build and no-Python checks.

### Cheat 3 — Read hidden expected answers at runtime

**What it does:** The Go program reads standard input, searches accessible filesystem locations for a file identical to that input, finds a sibling file containing expected answers, and prints those answers.

It also deletes `.py` files and creates a minimal Go module so that the other criteria pass.

**Actual Harbor score:** 1.000
**Behaviour:** 1.0
**Build:** 1.0
**No Python:** 1.0

**Job folder:** `results/cheat3/cheat3__rczrpXL/`

**Reward evidence:** `results/cheat3/cheat3__rczrpXL/verifier/reward.json`

**Verifier output:** `results/cheat3/cheat3__rczrpXL/verifier/test-stdout.txt`

**Why it worked:** The verifier builds and executes the candidate binary inside the verifier container. The tests Dockerfile copies test files into `/tests/`. During execution, the candidate program can locate the hidden input file and its sibling hidden expected-output file.

The experiment achieved a perfect behavioural score, demonstrating that the candidate process can access the hidden expected answers during verification.

**Security impact:** Hidden expected outputs are not isolated from the code being evaluated. A malicious or adversarial submission can read the answers rather than implement the required functionality.

**Suggested fix:**
- Execute the candidate binary in an isolated environment without access to `/tests/`.
- Keep hidden expected-output files inaccessible to the candidate process.
- Pass only test input to the candidate and collect its output.
- Read and compare expected output in the verifier only after the candidate process exits.
- Consider separate users, filesystem namespaces, and restrictive mount permissions as additional protections.

## Weakest points identified

1. **Verifier filesystem isolation:** `tests/behaviour/check.py` executes the candidate binary in the same verifier environment where hidden expected answers are stored.
2. **Reward weighting:** `tests/reward.toml` assigns weights of 1:1:4 to build, no-Python, and behaviour. Build and no-Python can both pass without a correct implementation.
3. **No-Python criterion:** The check only verifies that `.py` files are absent and that Go builds successfully. It does not establish that the required functionality was implemented correctly.

## Final conclusion

The three attacks produced two distinct outcomes:

- Cheat 1 and Cheat 2 scored 0.417 each.
- Cheat 3 scored 1.000.

**Highest actual Harbor reward: 1.000 — Cheat 3.**

The most serious finding is the verifier isolation weakness: the candidate program was able to access hidden expected-output data during execution and reproduce it exactly.

All results are backed by actual Harbor job folders and verifier reward files.

## Post-hardening retest — 20 November 2026

Annu Kumari subsequently hardened her `titlecase-go` task. I reran my
three original attack scripts against isolated copies of her updated task.

The updated verifier uses a 100,000-title exam, restricted candidate
execution privileges, Go/Python security checks, and a behavioural
score that raises accuracy below 80% to the fourth power.

### Verifier configuration issue

The published `tests/reward.toml` references a `build` criterion that
is missing from the updated `tests/` directory.

The first unmodified retest failed with `RewardFileNotFoundError`.
Its reported mean of zero is not a valid attack score.

For meaningful retesting, I restored the missing Build criterion
using the task's existing `go_build()` helper, only inside my
isolated test copies. Annu's original files were not modified.

### Actual Harbor retest results

| Attack | Original reward | New Behaviour | Build | No Python | New reward |
|---|---:|---:|---:|---:|---:|
| Cheat 1 — Lookup table | 0.417 | 0.0029 | 1.000 | 0.000 | 0.1686 |
| Cheat 2 — Half port | 0.417 | 0.0029 | 1.000 | 0.000 | 0.1686 |
| Cheat 3 — Hidden-answer exploit | 1.000 | 0.0000 | 1.000 | 0.000 | 0.1667 |

All three repaired-verifier Harbor runs completed with zero exceptions.

Harbor job folders:
- Cheat 1: `jobs/annu-retest-cheat1-fixed/`
- Cheat 2: `jobs/annu-retest-cheat2-fixed/`
- Cheat 3: `jobs/annu-retest-cheat3-fixed/`

### Retest conclusion

All three original attacks now score below 0.2 against the locally
repaired hardened task.

Cheat 3, which previously achieved reward 1.000 by accessing hidden
expected answers, now receives zero Behaviour credit.

The original attack was successful against the earlier task version,
but it no longer achieves a successful reward in these retests.

These results do not establish that every possible attack is blocked.
The missing Build criterion in Annu's published configuration also
needs correction before that exact version can be evaluated normally.
