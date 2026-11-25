# Attack Report

Target: Udit Parashar's titlecase-go task

## Cheat 1 - Direct Hidden Expected Output Access

**What it does:**

This cheat modifies `solution/solve.sh` to generate a Go program that directly reads `/tests/data/hidden_expected.txt` and prints its contents instead of implementing the actual titlecase functionality.

It also removes Python files and builds the Go program to satisfy the build and no-Python checks.

**Score:**

- Reward: 1.000
- Build: 1.000
- No_Python: 1.000
- Behaviour: 1.000

**Job folder:**

`jobs/2026-11-18__18-34-34`

**Trial name:**

`scratch-cheat1__FYGv8nL`

**Reward file:**

`results/cheat1-reward.json`

**Why it worked:**

The candidate Go program was able to access `/tests/data/hidden_expected.txt` from the verifier environment. It read the hidden expected output and printed it directly. The verifier compared this output with the expected output, resulting in a perfect behaviour score.

**How to fix:**

The verifier should not expose hidden expected data to the candidate program. Run candidate code in a strongly isolated environment with access only to its required input. Keep hidden expected outputs in a separate trusted verifier environment and perform comparisons outside the candidate's execution environment.




### Cheat 2 - Successful Updated Version

**Updated approach:** The revised Cheat 2 implementation successfully produces the expected output.

**Score:**
- Reward: 1.000
- Build: 1.000
- No_Python: 1.000
- Behaviour: 1.000

**Job folder:**
`jobs/2026-11-19__11-41-44`

**Trial:**
`scratch-cheat2__Bkpq5it`

**Reward file:**
`results/cheat2-reward-v2.json`

**Note:** The initial Cheat 2 attempt scored 0.3333. This revised attempt scored 1.000. Both results are preserved as evidence.


**Why it worked:**

The updated Go launcher invokes `python3` to execute the preserved Python reference implementation from `reference.txt`. It processes standard input line by line and preserves the input line endings. The verifier's no-Python check detects `.py` files but does not prevent Python from being invoked at runtime.

**Security weakness exposed:**

The task's build and no-Python checks do not establish that the candidate is a genuine Go implementation. A Go executable can act as a launcher for another language.




## Cheat 3 - Non-Zero Exit Status Ignored

**What it does:**

This cheat reads the hidden expected output and prints it directly. After printing the complete output, the Go program deliberately exits with status code 1.

It also removes Python files and builds the Go program.

**Score:**

- Reward: 1.000
- Build: 1.000
- No_Python: 1.000
- Behaviour: 1.000

**Job folder:**

`jobs/2026-11-19__10-36-10`

**Trial name:**

`scratch-cheat3__72QKfxd`

**Reward file:**

`results/cheat3-reward.json`

**Why it worked:**

The verifier compares the captured standard output against the hidden expected output but does not check the candidate process return code. Therefore, the program receives full behaviour credit despite exiting with status code 1.

**How to fix:**

The verifier should check `r.returncode` after executing the candidate. A non-zero exit status should cause the behaviour test to fail before comparing the output.
