# Attack Report — Mohammad Adnan's `titlecase-go`
 
**Attacker:** Charitra<br>**Target:** Mohammad Adnan<br>**Target task:** `MohammadAdnan/titlecase-go`<br>**Repository:** `https://github.com/japjeet-ethara/Harbor_Training`<br>**Branch required for Training 3:** `training-3`<br>**Target commit SHA:** TODO — record the exact SHA checked out before copying the task<br>**Harbor job evidence:** TODO — fill in only after each real Harbor run
 
> **Status:** Static review completed from the files available on the target's `main` branch. The three proposed probes below still need to be implemented and run against a local copy of the target task. No reward scores or Harbor job-folder names are claimed in this report yet. The training instructions require real Harbor evidence for every reported score.
 

## 1\. Task summary
 
The task asks the agent to implement the Python package's `titlecase()` behaviour in Go. The program must read all standard input as one text and write byte-for-byte matching output. It must use only the Go standard library, leave no `.py` files under `/workspace/repo`, and pass `go build ./...`.
 
The instructions specify line-break behaviour in detail, including CR, LF, mixed CRLF runs, leading and trailing line breaks, collapsed consecutive breaks, and empty input.
 

## 2\. Files inspected and evidence
 

| File | Observed behaviour | Evidence |
| ---- | ------------------ | -------- |
| `instruction.md` | Defines the required Go implementation and exact behavioural contract. | Lines 6–18 |
| `task.toml` | Sets agent and verifier timeouts to 600 seconds; verifier uses separate environment mode. | Lines 12–15, 19–24 |
| `tests/test.sh` | Runs `rewardkit --workspace /workspace/repo /tests`. The detailed checks are therefore defined in the test assets under `/tests`, not in this short shell script. | Lines 1–6 |
| `environment/Dockerfile` | Copies `python-titlecase/` into `/workspace/repo/` and `go-solution/` into `/opt/python-titlecase/`. | Lines 1–7 |
| `solution/solve.sh` | Copies `go.mod`, `main.go`, and `titlecase.go` from `/opt/python-titlecase/`, deletes `.py` files under `/workspace/repo`, then runs `go test ./...` and `go build ./...`. | Lines 1–14 |

## 3\. Potential weaknesses to investigate
 

### Finding 1 — Possible reference implementation exposure
 
**Evidence:** `environment/Dockerfile`, lines 4–5, copies `go-solution/` to `/opt/python-titlecase/`. `solution/solve.sh`, lines 5–7, copies Go source files from that location into the workspace.
 
**Why it matters:** If the agent's working container can read `/opt/python-titlecase/`, the reference Go implementation may be available to the agent. That would undermine the intended implementation challenge.
 
**How to verify:** In the agent-visible environment, check whether `/opt/python-titlecase/go.mod`, `/opt/python-titlecase/main.go`, and `/opt/python-titlecase/titlecase.go` exist and are readable before the agent writes its solution. Do not infer visibility solely from the Dockerfile.
 
**Possible fix:** Keep oracle/reference implementation material out of the agent-visible image. Supply it only to the verifier through a separate, inaccessible mechanism.
 
**Status:** Potential issue; visibility has not yet been confirmed.
 

### Finding 2 — Build success may be separable from behavioural correctness
 
**Evidence:** `instruction.md`, lines 10–18, requires both Go build compliance and exact output behaviour. `solution/solve.sh`, lines 12–13, runs `go test ./...` and `go build ./...`.
 
**Why it matters:** A minimal Go program may compile while returning incorrect output. If the reward system awards a meaningful independent score for build success, a build-only solution could receive partial credit without implementing titlecase.
 
**How to verify:** Run the build-only probe below and inspect the component-level reward breakdown in the actual `verifier/reward.json`.
 
**Possible fix:** Ensure build and policy checks cannot produce a high overall score without substantial behavioural correctness. Keep behaviour tests decisive.
 
**Status:** Hypothesis; reward weights and actual score are not yet inspected.
 

### Finding 3 — Python-removal check may be independently rewarded
 
**Evidence:** `instruction.md`, line 11, requires no `.py` file under `/workspace/repo`. `solution/solve.sh`, line 9, deletes `.py` files.
 
**Why it matters:** A solution might delete Python files without implementing the required Go behaviour. If this check earns independent points, it may create another partial-credit shortcut.
 
**How to verify:** Run the delete-only probe and inspect the component-level reward breakdown.
 
**Possible fix:** Make Python-removal a necessary policy condition, not a substitute for correct behaviour; ensure the overall reward remains low when behaviour is wrong.
 
**Status:** Hypothesis; actual reward weight and score are not yet known.
 

## 4\. Cheat probes to implement and run
 
These are controlled tests of the evaluator, not claims that the target has already been beaten. Each must be placed in its own `solve.sh`, installed only into a scratch copy of the target's `solution/`, and run with Harbor. Do not modify the target's `tests/`, `task.toml`, or `environment/`.
 

### Cheat 1 — Build-only minimal Go program
 
**Purpose:** Test whether a program that compiles but does not implement titlecase can earn significant reward.
 
**Probe:** Create a minimal Go module and `main` package that builds successfully but does not transform input correctly. Do not copy the reference implementation.
 
**Expected observation:** Build-related checks may pass; behaviour should fail. The actual total and component scores must be read from Harbor's reward file.
 

*   **Reward:** PENDING — real Harbor run required
     
*   **Job folder:** PENDING
     
*   **Evidence file:** `attack/results/cheat1-reward.json`
     
*   **Interpretation:** PENDING — use the actual component breakdown.
     

### Cheat 2 — Delete-Python-only
 
**Purpose:** Test whether satisfying the no-Python-file requirement can earn points without a working Go implementation.
 
**Probe:** Remove `.py` files under `/workspace/repo` but do not implement titlecase behaviour. Run the task through Harbor on a scratch copy.
 
**Expected observation:** The Python-file policy check may pass; behaviour should fail. Confirm both from the reward breakdown.
 

*   **Reward:** PENDING — real Harbor run required
     
*   **Job folder:** PENDING
     
*   **Evidence file:** `attack/results/cheat2-reward.json`
     
*   **Interpretation:** PENDING — use the actual component breakdown.
     

### Cheat 3 — Incomplete/partial titlecase implementation
 
**Purpose:** Measure how much credit a deliberately incomplete implementation receives.
 
**Probe:** Implement only a small subset of titlecase behaviour (for example, basic word capitalization) and omit difficult cases such as small-word rules, punctuation, apostrophes, hyphens, acronyms, and the specified line-break edge cases. Do not copy the reference implementation.
 
**Expected observation:** Compilation may pass, but a robust hidden behaviour suite should catch the missing cases. The actual score will show whether the exam gives too much partial credit.
 

*   **Reward:** PENDING — real Harbor run required
     
*   **Job folder:** PENDING
     
*   **Evidence file:** `attack/results/cheat3-reward.json`
     
*   **Interpretation:** PENDING — use the actual component breakdown.
     

## 5\. Run procedure and evidence collection
 
First, copy the target task to a scratch directory. For each probe, replace only the scratch copy's `solution/solve.sh`. Do not edit the target's `tests/`, `task.toml`, or `environment/`.
 
Run each probe:
 

    harbor run -p <scratch-copy-of-target> -a oracle

For every run:
 

1.  Record the exact job folder printed by Harbor.
     
2.  Open that job's `verifier/reward.json` (or `reward.txt`).
     
3.  Record the total reward and every component score exactly as reported.
     
4.  Copy the reward file to the corresponding `attack/results/cheatN-reward.json`.
     
5.  Add the real job-folder name and score to this report.
     

Do not fill in example or estimated scores.
 

## 6\. Results summary
 <table><tbody><tr><th >Probe</th><th >Total reward</th><th >Component breakdown</th><th >Harbor job folder</th></tr><tr><td >Cheat 1 — Build-only</td><td >PENDING</td><td >PENDING</td><td >PENDING</td></tr><tr><td >Cheat 2 — Delete-Python-only</td><td >PENDING</td><td >PENDING</td><td >PENDING</td></tr><tr><td >Cheat 3 — Partial titlecase</td><td >PENDING</td><td >PENDING</td><td >PENDING</td></tr></tbody></table>
**Highest cheat score:** PENDING — calculate after all three real Harbor runs.
 

## 7\. Recommended fixes for the task owner
 

1.  Verify whether `/opt/python-titlecase/` is readable by the agent. If it contains the reference Go implementation and is agent-visible, move reference material out of the agent environment.
     
2.  Inspect the individual reward checks and weights behind `rewardkit`; ensure build success and Python-file removal cannot earn a high score without correct behaviour.
     
3.  Keep behaviour tests hidden from the agent and include edge cases from the written contract: CR, LF, CRLF, repeated breaks, leading/trailing breaks, tabs, punctuation, apostrophes, hyphens, acronyms, small words, and empty input.
     
4.  Validate that the final reward meaningfully reflects exact output correctness, not just setup or policy compliance.
     

## 8\. Limitations of this review
 
This report is based on the available `instruction.md`, `task.toml`, `tests/test.sh`, `environment/Dockerfile`, and `solution/solve.sh` files from the linked `main`\-branch task. The contents of the detailed `/tests` assets, the exact `training-3` target commit, and actual Harbor run outputs have not been verified here. Therefore, the findings labelled “potential” or “hypothesis” must not be presented as confirmed vulnerabilities until tested.
 
---
 
**Final submission check**
 

*   Confirm target commit SHA from the exact task copy used.
     
*   Implement three separate cheat `solve.sh` files.
     
*   Run all three against a scratch copy using Harbor.
     
*   Save the three real reward JSON files under `attack/results/`.
     
*   Replace every PENDING field with actual run evidence.
     
*   Confirm no target files outside your own folder were changed.
## Day 6 - Re-attack against Adnan's hardened task (2026-11-20)

I reran the same three probes described above against a private copy of Adnan's hardened task from commit `240786becf41ed7323faf933516b8fdc75d9aeb2` (`training-3/MohammadAdnan/task`). The task's `tests/`, `task.toml`, and `environment/` were unchanged. Each Harbor run used one trial with the `oracle` adapter and Docker environment.

| Cheat | Accuracy | Behaviour | Build | No_Python | Reward | Harbor job folder | Saved reward |
|---|---:|---:|---:|---:|---:|---|---|
| 1 - Build-only | 0.000 | 0.000 | 1.000 | 0.000 | **0.167** | `jobs/adnan-reattack-20261120/adnan-c1-20261120` | `attack/results/day6-adnan-cheat1-reward.json` |
| 2 - Delete-Python-only | 0.000 | 0.000 | 0.000 | 0.000 | **0.000** | `jobs/adnan-reattack-20261120/adnan-c2-20261120` | `attack/results/day6-adnan-cheat2-reward.json` |
| 3 - Partial titlecase port | 0.16741 | 0.000 | 1.000 | 0.000 | **0.167** | `jobs/adnan-reattack-20261120/adnan-c3-20261120` | `attack/results/day6-adnan-cheat3-reward.json` |

The partial port matched 16.741% of the 100,000-case exam, below Adnan's 50% behaviour-credit threshold, so it received no behaviour or no-Python credit. The highest of these three rerun scores was 0.167, below the Day 6 limit of 0.2. This confirms these three known cheats remain below the threshold on the hardened snapshot; it does not establish resistance to every possible new attack. I did not modify Adnan's repository files.
## Day 6 follow-up - one new cheat (2026-11-20)

I added a fourth probe after the three original reruns. It searches common mount locations for Adnan's reference Go port, copies it into the candidate workspace if found, removes the Python files, and builds it. Script: `attack/day6-adnan/cheat4-mount-scan/solve.sh`.

| Cheat | Accuracy | Behaviour | Build | No_Python | Reward | Harbor job folder | Saved reward |
|---|---:|---:|---:|---:|---:|---|---|
| 4 - Reference mount scan | 1.000 | 1.000 | 1.000 | 1.000 | **1.000** | `jobs/adnan-reattack-20261120/adnan-c4-mount-scan-20261120` | `attack/results/day6-adnan-cheat4-mount-scan-reward.json` |

The probe found the bundled Go reference in the Harbor Oracle run environment (the first checked path is `/solution/go`) and copied it, so the exact hidden exam matched. This is a 1.000 score in the required Oracle-based run, above the Day 6 0.2 threshold.

**Interpretation limit:** Adnan's task documentation says `/solution/go` is mounted for Oracle runs and excluded from the regular agent image. This result proves the source is readable in the Oracle run used for this probe; by itself it does not prove a normal submitted agent can read that mount. The task owner should verify the same paths from the actual agent container before treating this as a candidate-visible leak. Do not count the task as fully resistant based on the earlier three-cheat results alone.