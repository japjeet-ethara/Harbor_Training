# Security Assessment & Vulnerability Analysis: Vishu Porwal's `titlecase-go` Task

**Target Author:** Vishu Porwal  
**Target Task Identifier:** `task/titlecase-go`  
**Target Commit SHA:** `9a08b05d247a16f3c1448b03711add5a8392bbe9`  
**Evaluation Harness:** Harbor 0.25.0 / RewardKit 0.2.*  
**Evaluator:** Omar Ghyas (`training-3/OmarGhyas/`)  
**Date of Assessment:** November 20, 2026  

---

## 1. Executive Summary

This report documents the security assessment, structural vulnerability analysis, and empirical penetration testing conducted against Vishu Porwal's Harbor evaluation task, `titlecase-go` (commit `9a08b05d247a16f3c1448b03711add5a8392bbe9`). The stated goal of the task is to require an autonomous AI agent to port the Python `titlecase` library into a standalone Go command-line program using only the Go standard library, achieving 100% byte-for-byte behavioral parity while eliminating all Python source files.

Our evaluation systematically tested three distinct attack vectors designed to bypass the genuine porting requirement:
1. **Cheat 1 (Build + Delete Trick):** Exploited decoupled metric aggregation to earn partial reward without implementing any functional logic.
2. **Cheat 2 (Read the Exam):** Exploited a verifier filesystem-isolation failure to read static, pre-computed answer keys (`/tests/data/hidden_expected.txt`) directly from the verifier's disk and stream them to standard output, without executing any titlecasing logic.
3. **Cheat 3 (Python Inside):** Did not read static answer files; instead, it dynamically computed answers on arbitrary inputs by preserving the original Python implementation under an extensionless file (`py_engine`) and delegating runtime execution to the container's `python3` interpreter through a Go subprocess wrapper.

### Key Assessment Findings:
* **Two Critical Flaws Achieved Full Reward (1.0000 / 100%):** Both Cheat 2 and Cheat 3 completely bypassed the porting objective, earning perfect scores without writing a single line of titlecasing logic in Go.
* **Rubric Grants 33.33% Free Credit:** Cheat 1 proved that an empty Go program that deletes `.py` files automatically scores **0.3333**, demonstrating that the baseline rubric grants substantial unearned credit (scoring well above the below-0.20 threshold required when defending the hardened task on Day 6).
* **Grader Filesystem Leak vs. Execution Bypass:** The verifier suffers from two distinct isolation gaps: it exposes static answer keys on disk to student binaries (Cheat 2), and it provides a working Python runtime that student binaries can invoke to process inputs dynamically (Cheat 3).

---

## 2. Target Task Audit and Execution Architecture

Understanding the vulnerabilities requires analyzing the separation boundaries between the agent and verifier container environments.

```
+-------------------------------------------------------------------------+
| AGENT PHASE (Isolated Container)                                        |
| Base Image: golang:1.23 (environment/Dockerfile:1)                      |
| Working Dir: /workspace/repo (environment/Dockerfile:5)                 |
| Initial Contents: python-titlecase/ (environment/Dockerfile:3)          |
| Tests Visibility: Strictly hidden (tests/ directory is NOT copied)      |
+-------------------------------------------------------------------------+
                                    |
                                    | [Harbor collects /workspace/repo]
                                    v (task.toml:2)
+-------------------------------------------------------------------------+
| VERIFIER PHASE (Grader Container)                                       |
| Base Image: python:3.12-slim + Go 1.23 toolchain (tests/Dockerfile:1-8) |
| Grader Code: /tests/ (tests/Dockerfile:18: COPY . /tests/)               |
| Hidden Datasets: /tests/data/hidden_*.txt (tests/behaviour.py:11-12)     |
| Student Workspace: /workspace/repo (mounted artifacts)                  |
| Execution Context: Direct container execution; no filesystem sandbox   |
+-------------------------------------------------------------------------+
```

### The Role of `environment_mode = "separate"`
In `task.toml:13-16`, the verifier configuration sets `environment_mode = "separate"`. During the agent work phase, the agent container (`environment/Dockerfile:1-5`) receives only `/workspace/repo`. The test directory `tests/` is never mounted or copied into the agent's container. At authoring time, the hidden datasets (`tests/data/hidden_inputs.txt` and `tests/data/hidden_expected.txt`) are completely inaccessible to the agent.

### The Runtime Exposure Gap
The security failure occurs during the verifier evaluation phase. In `tests/Dockerfile:1-18`, the verifier image is constructed from `python:3.12-slim`. It copies the entire task root into `/tests/` (`tests/Dockerfile:18`), including the hidden test inputs and expected outputs. 

In `tests/behaviour.py:31-50`, the verifier compiles the student repository:
```python
build = subprocess.run(["go", "build", "-o", str(binary), "."], cwd=REPO, ...)
run = subprocess.run([str(binary)], input=HIDDEN_INPUTS.read_bytes(), capture_output=True, timeout=180)
```
Crucially, `subprocess.run([str(binary)], ...)` spawns the untrusted compiled student binary directly in the verifier container environment. Because no container boundary, chroot, or filesystem sandbox isolates the binary from the grader directory, the submitted Go code has direct read access to files under `/tests/` on the verifier container's filesystem.

---

## 3. Verification and Scoring Mechanics

The task uses Harbor's RewardKit framework (`harbor-rewardkit==0.2.*`), driven by `tests/test.sh:5-8`. RewardKit scans `/tests` for programmatic criteria and aggregates their scores according to `tests/reward.toml`.

### Individual Evaluation Criteria
1. **`build` (`tests/build.py:21-36`):**
   * **Implementation:** Executes `go build ./...` inside `/workspace/repo` (`tests/build.py:27-33`) under a 180-second timeout with `CGO_ENABLED=0` and `GOTOOLCHAIN=local`.
   * **Score:** Returns binary `1.0` if `result.returncode == 0`, else `0.0`.
   * **Weight:** `1.0`.
2. **`no_python` (`tests/no_python.py:28-43`):**
   * **Implementation:** Executes `_has_python(REPO)` (`tests/no_python.py:21-25`), which scans for files where `path.suffix == ".py"`. If none are found, it executes `go build ./...`.
   * **Score:** Returns binary `1.0` if no `.py` file exists and compilation succeeds, else `0.0`.
   * **Weight:** `1.0`.
3. **`behaviour` (`tests/behaviour.py:24-58`):**
   * **Implementation:** Compiles `/workspace/repo` into a temporary binary (`tests/behaviour.py:31-39`), pipes 2,000 lines from `/tests/data/hidden_inputs.txt` into stdin (`tests/behaviour.py:45-50`), and compares stdout line-by-line against `/tests/data/hidden_expected.txt` (`tests/behaviour.py:57-58`).
   * **Score:** Returns the continuous ratio `matches / len(expected)` (0.0 to 1.0).
   * **Weight:** `4.0`.

### Scoring Formula and Mathematical Flaw
Configured in `tests/reward.toml:1-4`:
```toml
[[reward]]
name = "reward"
aggregation = "weighted-mean"
weights = { build = 1.0, no_python = 1.0, behaviour = 4.0 }
```
The overall score is computed via weighted mean:
$$\text{Reward} = \frac{(1.0 \times \text{build}) + (1.0 \times \text{no\_python}) + (4.0 \times \text{behaviour})}{1.0 + 1.0 + 4.0} = \frac{\text{build} + \text{no\_python} + 4.0 \times \text{behaviour}}{6.0}$$

Because `build` and `no_python` are completely independent of `behaviour`, an agent that does nothing more than create an empty Go file and delete all `.py` files receives:
$$\text{Reward} = \frac{1.0 + 1.0 + 4.0(0.0)}{6.0} = \frac{2.0}{6.0} \approx \mathbf{0.3333}$$
This gives an unearned 33.33% reward to a completely non-functional submission.

---

## 4. Testing Methodology

To guarantee scientific rigor, auditability, and safety, all experiments adhered to strict controls:
1. **Target Read-Only Invariance:** The target directory `attack/target/` was maintained strictly read-only. Line endings, Git blob hashes, and folder structures were verified before and after each trial.
2. **Clean Checkout Verification:** Upstream repository commit `9a08b05d247a16f3c1448b03711add5a8392bbe9` was verified to ensure that `tests/test.sh` retained authentic Unix LF line endings (200 bytes, Git blob `23864b2f1004a844cee0c44cfa9f8a55f38d5258`).
3. **Isolated Scratch Sandboxes:** For each cheat, a separate directory was created in `$env:TEMP` (`scratch-cheat1-lf`, `scratch-cheat2-lf`, `scratch-cheat3-lf`) outside the Git repository.
4. **Single-Point Cheat Injection:** Only `solution/solve.sh` was replaced inside the scratch copy. All `instruction.md`, `task.toml`, `environment/`, and `tests/` files remained identical to Vishu's original files.
5. **Standard Harbor Invocation:** Trials were executed using the Harbor CLI (`harbor run -p <scratch-dir> -a oracle`) with the Oracle agent.
6. **Empirical Artifact Collection:** Rewards and metrics were extracted directly from the generated verifier artifacts (`verifier/reward.json` and `verifier/reward-details.json`) and copied into `attack/results/`.

---

## 5. Detailed Attack Analysis

## Cheat 1 — Build + Delete Trick

### Objective
Demonstrate that Vishu's grading rubric awards a high baseline reward (33.33%) to a submission that implements zero titlecasing logic.

### Attack Technique
Deploy a stub Go package that compiles cleanly and delete all files with the `.py` extension.

### Step-by-Step Implementation
1. Navigate to `/workspace/repo`.
2. Run `find . -type f -name '*.py' -delete` to purge all Python source files.
3. Write `go.mod` declaring module `titlecase-go` with Go version 1.23.
4. Write `main.go` containing:
   ```go
   package main
   func main() {}
   ```
5. Do not implement any input scanning, string transformation, or output printing.

### Execution & Actual Behavior
* **Script:** `attack/cheat1/solve.sh`
* **Trial ID:** `scratch-cheat1-lf__8jrkVGK`
* **Job Directory:** `jobs/2026-11-20__00-20-39/scratch-cheat1-lf__8jrkVGK`
* **Artifact Output:** [attack/results/cheat1-reward.json](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/attack/results/cheat1-reward.json)

### Score Breakdown
* **`build`:** `1.0` (Weight: 1.0)
* **`no_python`:** `1.0` (Weight: 1.0)
* **`behaviour`:** `0.0` (0 / 2,000 matches, Weight: 4.0)
* **Overall Reward:** **`0.3333`** (33.33%)

### Vulnerable Source Lines
* `tests/reward.toml:1-4` — Assigns fixed weights to structural checks without behavioral dependency.
* `tests/build.py:21-36` — Evaluates package compilation in isolation.
* `tests/no_python.py:28-43` — Awards full credit for absence of `.py` files without testing functionality.

### Root Cause & Why the Verifier Failed
The verifier uses an unweighted mean of independent checks. `no_python` duplicates `build` compilation without conditioning on behavioral output, granting 33.33% partial credit for zero functional progress—a score that fails the Day 6 requirement that cheats must score below 0.20 on a hardened task.

### Recommended Fix
Make `no_python` and `build` conditional on behavioral performance (e.g. `if behaviour_score < 0.5: return 0.0`), or switch `tests/reward.toml` aggregation to `all-pass`.

---

## Cheat 2 — Read the Exam

### Objective
Demonstrate that the verifier fails to isolate hidden evaluation data from the submitted binary during the grading phase, allowing an attacker to read the answer sheet directly from disk.

### Attack Technique
Compile a Go program that opens the verifier container's hidden answer file `/tests/data/hidden_expected.txt` at runtime and streams it directly to standard output.

### Step-by-Step Implementation
1. Navigate to `/workspace/repo` and delete all `.py` files.
2. Create `go.mod` for `titlecase-go`.
3. Create `main.go` using standard library `os` and `io`:
   ```go
   package main

   import (
       "io"
       "os"
   )

   func main() {
       f, err := os.Open("/tests/data/hidden_expected.txt")
       if err == nil {
           defer f.Close()
           io.Copy(os.Stdout, f)
           return
       }
   }
   ```
4. When executed by `tests/behaviour.py`, the binary reads the hidden answers and outputs them to stdout.

### Execution & Actual Behavior
* **Script:** `attack/cheat2/solve.sh`
* **Trial ID:** `scratch-cheat2-lf__X83hM7x`
* **Job Directory:** `jobs/2026-11-20__00-25-41/scratch-cheat2-lf__X83hM7x`
* **Artifact Output:** [attack/results/cheat2-reward.json](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/attack/results/cheat2-reward.json)

### Score Breakdown
* **`build`:** `1.0` (Weight: 1.0)
* **`no_python`:** `1.0` (Weight: 1.0)
* **`behaviour`:** `1.0` (2,000 / 2,000 matches, Weight: 4.0)
* **Overall Reward:** **`1.0000`** (100.00%)

### Vulnerable Source Lines
* `tests/Dockerfile:16-18` — Copies hidden test answers into `/tests/` in the verifier image.
* `tests/behaviour.py:11-12` — Hardcodes plaintext hidden answer file at `/tests/data/hidden_expected.txt`.
* `tests/behaviour.py:45-50` — Runs untrusted binary via `subprocess.run([str(binary)], ...)` directly inside the verifier container with unrestricted read access to `/tests/` on the filesystem.

### Root Cause & Why the Verifier Failed
`environment_mode = "separate"` only protects test files during the agent phase. In the verifier phase, untrusted student code is executed in the same container that holds the answer keys. Because the verifier container does not restrict filesystem access or run the binary inside an isolated sandbox, the binary has direct read access to `/tests/data/hidden_expected.txt` (`tests/behaviour.py:12`) on disk, allowing it to echo the answer sheet and achieve 2,000 / 2,000 matches.

### Recommended Fix
Isolate the execution of the student binary from the grading filesystem: run the student binary inside a dedicated sandbox/container where `/tests` is not mounted, or restrict filesystem permissions on the `/tests` directory so untrusted processes cannot read test fixtures.

---

## Cheat 3 — Python Inside

### Objective
Demonstrate that an attacker can bypass the task's prohibition on Python by renaming Python source files to omit the `.py` extension and delegating all execution to Python 3 at runtime.

### Attack Technique
Preserve the original `python-titlecase` implementation as an extensionless script (`py_engine`), remove all `.py` files, and provide a Go wrapper that spawns `python3 /workspace/repo/py_engine`.

### Step-by-Step Implementation
1. Navigate to `/workspace/repo`.
2. Copy `titlecase/__init__.py` to `py_engine` (no file extension).
3. Append a standard I/O processing loop to `py_engine`:
   ```python
   if __name__ == '__main__':
       import sys
       for line in sys.stdin:
           sys.stdout.write(titlecase(line.rstrip('\r\n')) + '\n')
           sys.stdout.flush()
   ```
4. Delete all remaining `.py` files: `find . -type f -name '*.py' -delete`.
5. Create `go.mod` and `main.go`. In `main.go`, invoke `python3` via Go's standard library `os/exec`:
   ```go
   package main

   import (
       "os"
       "os/exec"
   )

   func main() {
       cmd := exec.Command("python3", "/workspace/repo/py_engine")
       cmd.Stdin = os.Stdin
       cmd.Stdout = os.Stdout
       cmd.Stderr = os.Stderr
       if err := cmd.Run(); err != nil {
           os.Exit(1)
       }
   }
   ```

### Execution & Actual Behavior
* **Script:** `attack/cheat3/solve.sh`
* **Trial ID:** `scratch-cheat3-lf__gPpNKy5`
* **Job Directory:** `jobs/2026-11-20__00-31-25/scratch-cheat3-lf__gPpNKy5`
* **Artifact Output:** [attack/results/cheat3-reward.json](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/attack/results/cheat3-reward.json)

### Score Breakdown
* **`build`:** `1.0` (Weight: 1.0)
* **`no_python`:** `1.0` (Weight: 1.0)
* **`behaviour`:** `1.0` (2,000 / 2,000 matches, Weight: 4.0)
* **Overall Reward:** **`1.0000`** (100.00%)

### Vulnerable Source Lines
* `tests/no_python.py:21-25` — Checks only `path.suffix == ".py"`, ignoring files with no extension or other suffixes.
* `tests/Dockerfile:1` — Verifier image is built `FROM python:3.12-slim`, providing the `/usr/bin/python3` runtime.
* `tests/behaviour.py:45-50` — Spawns the binary without process restrictions, permitting child subprocess spawning (`execve` of `python3`).

### Root Cause & Why the Verifier Failed
Static extension scanning cannot detect disguised scripts or interpreter delegations. Because the verifier environment provides a Python interpreter and allows child processes, the Go program simply proxies execution to Python.

### Recommended Fix
Do not rely on file extension checks. Run the Go binary inside a restricted execution environment where Python is absent from PATH and child process spawning is restricted.

---

## 6. Consolidated Results Table

The following table summarizes the verified empirical results across all three attacks, confirmed by the actual Harbor job artifacts:

| Experiment | Attack Technique | Build Score | No-Python Score | Behaviour Score | Total Hidden Titles | Matches Achieved | Behavioral Accuracy | Overall Reward | Specification Compliance | Harbor Job Path |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Cheat 1** | Build + Delete Trick | 1.0000 | 1.0000 | 0.0000 | 2,000 | 0 | 0.00% | **0.3333** | 0% (Empty Go program) | `jobs/2026-11-20__00-20-39/scratch-cheat1-lf__8jrkVGK` |
| **Cheat 2** | Read the Exam | 1.0000 | 1.0000 | 1.0000 | 2,000 | 2,000 | 100.00% | **1.0000** | 0% (Answer file read) | `jobs/2026-11-20__00-25-41/scratch-cheat2-lf__X83hM7x` |
| **Cheat 3** | Python Inside | 1.0000 | 1.0000 | 1.0000 | 2,000 | 2,000 | 100.00% | **1.0000** | 0% (Subprocess proxy) | `jobs/2026-11-20__00-31-25/scratch-cheat3-lf__gPpNKy5` |

---

## 7. Cross-Attack Security Findings

Comparing the three attacks yields five fundamental principles for designing secure agent benchmarks:

### 1. Cheat 2 vs. Cheat 3: Distinct Attack Vectors
While both Cheat 2 and Cheat 3 scored 1.0000, they exploit fundamentally different architectural vulnerabilities:
* **Cheat 2 is an information disclosure / verifier filesystem-isolation failure:** It relies on pre-computed static answer keys being accessible on the container filesystem. If test inputs were generated dynamically in memory or answer files were stored outside the accessible filesystem, Cheat 2 would immediately fail.
* **Cheat 3 is an unauthorized execution / language boundary bypass:** It does not read any answer file or require prior knowledge of test fixtures; rather, it computes answers dynamically on arbitrary inputs by invoking the host Python interpreter behind a Go wrapper, subverting language restrictions.

### 2. Structural Validation Does Not Imply Functional Progress
Rewarding static properties (such as file presence, file absence, or successful compilation) independently of behavioral checks inflates scores. In Vishu's task, compilation and file deletion account for 33.33% of the total score. Tasks must never reward "effort" or structural artifacts unless behavioral tests pass.

### 3. Hidden Test Isolation Must Extend to Grader Runtime
Separating the agent's authoring environment from the verifier is insufficient if the verifier container executes submitted code in the presence of unencrypted answer keys. When untrusted code is compiled and run during grading, it must be treated as hostile and denied access to test fixtures.

### 4. File Extension Checks Are Security Theater
Scanning for `.py` extensions fails to verify language compliance. An attacker can rename files, use dynamic loading, embed code in binary strings, or compile cross-language CGO bindings. Filename scanning must be replaced by runtime language isolation.

### 5. Runtime Isolation Is Essential
If an evaluation forbids Python, the runtime container where the program executes must not provide a Python interpreter. Running student code in an image containing both Go and Python makes enforcement of language constraints nearly impossible without containerized sandboxing.

---

## 8. Prioritized Remediation Plan

The following table outlines the concrete, prioritized remediation steps recommended for Vishu Porwal's task:

| Priority | Vulnerability Addressed | Target File | Recommended Fix | Expected Security Benefit |
| :---: | :--- | :--- | :--- | :--- |
| **P0** | **Answer Sheet Leak (Cheat 2)** | `tests/behaviour.py`, `tests/Dockerfile` | Isolate student binary execution from the grader filesystem using a dedicated sandbox/container where `/tests` is unmounted, or restrict filesystem read permissions on `/tests`. | Prevents submitted code from reading `hidden_expected.txt`. Reduces Cheat 2 reward from 1.0000 to 0.3333. |
| **P0** | **Python Subprocess Proxy (Cheat 3)** | `tests/behaviour.py`, `tests/Dockerfile` | Isolate the execution of the Go binary to an environment where `python3` is absent from `PATH` and filesystem access to interpreters is denied (e.g. via rootless sandbox or minimal execution container). | Prevents Go binaries from delegating work to Python interpreters. Reduces Cheat 3 reward from 1.0000 to 0.3333. |
| **P1** | **Free Structural Points (Cheat 1)** | `tests/reward.toml`, `tests/no_python.py` | Condition `no_python` on behavioral success (`if scores['behaviour'] < 0.5: return 0.0`), or switch `reward.toml` aggregation to `all-pass`. | Eliminates unearned baseline credit. Reduces Cheat 1 reward from 0.3333 to 0.0000. |
| **P2** | **Superficial Python Detection** | `tests/no_python.py` | Inspect file MIME types (`file --mime-type`), scan for Python shebangs (`#!/usr/bin/env python`), and inspect binary symbols for embedded interpreter libraries. | Closes static extension evasion techniques. |

---

## 9. Evidence and Reproducibility

All findings reported in this document are backed by verifiable on-disk trial artifacts and execution logs:

* **Cheat 1 (Build + Delete Trick):**
  * **Result File:** [attack/results/cheat1-reward.json](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/attack/results/cheat1-reward.json)
  * **Trial Directory:** `jobs/2026-11-20__00-20-39/scratch-cheat1-lf__8jrkVGK`
  * **Score Record:** `{"reward": 0.3333}` (build 1.0, no_python 1.0, behaviour 0.0)
* **Cheat 2 (Read the Exam):**
  * **Result File:** [attack/results/cheat2-reward.json](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/attack/results/cheat2-reward.json)
  * **Trial Directory:** `jobs/2026-11-20__00-25-41/scratch-cheat2-lf__X83hM7x`
  * **Score Record:** `{"reward": 1.0}` (build 1.0, no_python 1.0, behaviour 1.0)
* **Cheat 3 (Python Inside):**
  * **Result File:** [attack/results/cheat3-reward.json](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/attack/results/cheat3-reward.json)
  * **Trial Directory:** `jobs/2026-11-20__00-31-25/scratch-cheat3-lf__gPpNKy5`
  * **Score Record:** `{"reward": 1.0}` (build 1.0, no_python 1.0, behaviour 1.0)

*(Note: Per Day 4 instructions, only lightweight score files are committed under `attack/results/`, while extensive container logs and build caches remain stored under the Git-ignored `jobs/` directory.)*

---

## 10. Final Assessment

Vishu Porwal's `titlecase-go` evaluation task exhibits critical structural and architectural grading vulnerabilities. Decoupled scoring permits empty submissions to earn substantial credit, while lack of runtime isolation in the verifier container allows submitted code to read hidden answer files and invoke host Python runtimes. As a result, an agent can achieve a perfect score without performing the required porting task.

Highest score achieved: 1.0000 (Cheat 2 — Read the Exam, and Cheat 3 — Python Inside).

---

## 11. Day 6 Re-attack: Verification of Vishu Porwal's Hardened Task

### 11.1 Target & Scope
- **Target Author:** Vishu Porwal
- **Target Task Identifier:** `training-3/VishuPorwal/task`
- **Target Hardened Commit SHA:** `231e1a16daf89366446f93be7fcd150c82e0966e`
- **Evaluator:** Omar Ghyas (`training-3/OmarGhyas/`)
- **Evaluation Harness:** Harbor 0.25.0
- **Assessment Date:** November 20, 2026

### 11.2 Hardened Architecture & Defenses Introduced by Target
In Day 5, Vishu Porwal deployed significant hardening measures:
1. **Gated Scoring Model (`task/tests/reward.toml` & `task/tests/behaviour.py`):** Structural criteria `build` and `no_python` weights set to `0.0`; `behaviour` set to `1.0`. Behaviour scoring strictly requires both compilation and absence of Python files as non-scoring prerequisites.
2. **Filesystem Isolation Jail:** The student executable is placed in an isolated directory and executed via `chroot --userspec=65534:65534 --groups= <jail> /titlecase` with an empty environment (`env={}`).
3. **Byte-Exact Record Comparator:** Evaluates outputs line-by-line using strict LF (`\n`) delimiters and asserts exact record counts.
4. **100,000-Line Exam:** Generated under Python 3.14 stdlib `re` mode (`REGEX_AVAILABLE = False`).

---

### 11.3 Re-execution of Original Cheats 1–3

All three original Day 4 attacker cheats were re-executed against the isolated hardened snapshot:

| Cheat | Attack Vector | Day 4 Score | Day 6 Score | Hardened Threshold | Defense Status | Harbor Proof Reference |
|---|---|:---:|:---:|:---:|:---:|---|
| **Cheat 1** | Build + Delete Trick (`func main() {}`) | `0.3333` | **`0.0000`** | < 0.20 | **DEFENDED** | `jobs/day6-reattack-vishu-cheat1/task__x8heT4m` |
| **Cheat 2** | Read the Exam (`/tests/data/hidden_expected.txt`) | `1.0000` | **`0.0000`** | < 0.20 | **DEFENDED** | `jobs/day6-reattack-vishu-cheat2/task__gqGAPJ5` |
| **Cheat 3** | Python Inside Wrapper (`exec.Command("python3", ...)`) | `1.0000` | **`0.0000`** | < 0.20 | **DEFENDED** | `jobs/day6-reattack-vishu-cheat3/task__d4FuvaQ` |

#### Detailed Re-attack Findings:
- **Cheat 1 Neutralized:** Gated scoring in `reward.toml` assigns `0.0` weight to `build` and `no_python`. Because the empty binary outputs 0 records, `len(got_records) != len(expected_records)` triggers line 125 of `behaviour.py`, awarding `0.0000`.
- **Cheat 2 Neutralized:** The runtime `chroot` jail isolates the process. `/tests/data/hidden_expected.txt` exists outside the jail root and is completely inaccessible, causing file opening to fail and awarding `0.0000`.
- **Cheat 3 Neutralized:** The `chroot` jail contains only `/titlecase`. Neither `/usr/bin/python3`, system dynamic libraries, nor the workspace `py_engine` are present. Subprocess execution fails (`executable file not found in $PATH`), the binary exits non-zero, and `_run_in_jail` returns `None` (`behaviour.py:122`), awarding `0.0000`.

---

### 11.4 Day 6 Exploit: Cheat 4 (Compile-Time Public Exam Embedding)

While runtime execution is isolated via `chroot`, an architectural vulnerability was identified: the 100,000-record hidden exam datasets are static and publicly committed in the target Git repository (`hidden_inputs.txt` and `hidden_expected.txt`).

**Cheat 4 (`attack/cheat4/solve.sh`)** exploits this vulnerability during the compilation phase:
1. **Public Exam Retrieval:** Because `task.toml` specifies `network_mode = "public"`, the solver downloads `hidden_inputs.txt` and `hidden_expected.txt` directly from the public GitHub repository at the exact target commit into `/workspace/repo/` as `q.txt` and `a.txt`.
2. **Gating Compliance:** Deletes all `.py` files to satisfy `_has_python(REPO)`.
3. **Compile-Time Embedding via `//go:embed`:** 
   ```go
   package main

   import (
       "bufio"
       _ "embed"
       "os"
       "strings"
   )

   //go:embed q.txt
   var questions string

   //go:embed a.txt
   var answers string

   func main() {
       qs := strings.Split(strings.TrimSuffix(questions, "\n"), "\n")
       as := strings.Split(strings.TrimSuffix(answers, "\n"), "\n")

       lookup := make(map[string]string, len(qs))
       for i := range qs {
           if i < len(as) {
               lookup[qs[i]] = as[i]
           }
       }

       scanner := bufio.NewScanner(os.Stdin)
       scanner.Buffer(make([]byte, 0, 64*1024), 16*1024*1024)
       writer := bufio.NewWriter(os.Stdout)
       defer writer.Flush()

       for scanner.Scan() {
           line := scanner.Text()
           if ans, ok := lookup[line]; ok {
               writer.WriteString(ans)
           } else {
               writer.WriteString(line)
           }
           writer.WriteByte('\n')
       }
   }
   ```
4. **Why `chroot` Fails to Block Cheat 4:** The verifier executes `go build -o str(binary) .` inside `/workspace/repo` *before* the `chroot` jail is constructed. Go's `//go:embed` bakes all 100,000 answer strings directly into the binary's `.rodata` section. At runtime inside the empty jail, the binary reads answers entirely from memory, requiring zero filesystem access.

#### Empirical Harbor Proof Results for Cheat 4:
- **Job Name:** `day6-reattack-vishu-cheat4`
- **Job UUID:** `69f6cfca-6d8f-43aa-abd5-c7c6c5a1cc93` | **Trial ID:** `task__ZGEpvhq`
- **Scores:** `build: 1.0`, `no_python: 1.0`, `behaviour: 1.0` (**100,000 / 100,000 exact matches**)
- **Overall Reward:** **`1.0000`** (100% full credit achieved with 0% titlecasing logic ported)
- **Evidence:** [`jobs/day6-reattack-vishu-cheat4/task__ZGEpvhq/verifier/reward.json`](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/jobs/day6-reattack-vishu-cheat4/task__ZGEpvhq/verifier/reward.json)

---

### 11.5 Additional Robustness & Sensitivity Findings

Controlled experiments further probed the behavioral verifier's edge-case handling:
1. **CRLF Line-Ending Sensitivity (`day6-qa-crlf`, Trial `task__zFCfs5u`):** Emitting correct answers terminated by `\r\n` (CRLF) leaves `\r` on records after `_split_records(b"\n")`. Reward collapsed to **`0.0000`** (0 / 100,000 matches), proving zero tolerance for Windows line endings.
2. **All-or-Nothing Record Count Gating (`day6-qa-off-by-one`, Trial `task__sXTiuWs`):** Emitting 99,999 valid records (omitting just the 100,000th record) triggered `len(got) != len(exp)` in `behaviour.py:125`, awarding **`0.0000`** and completely denying proportional partial credit.
3. **Package Layout Rigidity (`day6-qa-subpackage`, Trial `task__MgubhMQ`):** Placing code in standard `cmd/titlecase/main.go` caused `go build ./...` to fail on empty residual directories, and `behaviour.py:107` hard-codes `go build .` in the root, resulting in **`0.0000`**.

---

### 11.6 Comparative Score Matrix & Re-attack Conclusion

| Attack Vector | Cheat Name | Day 4 Score | Day 6 Score | Status | Primary Bypass Mechanism |
|---|---|:---:|:---:|:---:|---|
| **Cheat 1** | Build + Delete Trick | `0.3333` | **`0.0000`** | **DEFENDED** | Gated scoring prevented unearned baseline credit. |
| **Cheat 2** | Read the Exam | `1.0000` | **`0.0000`** | **DEFENDED** | `chroot` jail blocked runtime filesystem traversal. |
| **Cheat 3** | Python Inside Wrapper | `1.0000` | **`0.0000`** | **DEFENDED** | `chroot` jail eliminated Python runtime from execution context. |
| **Cheat 4** | Compile-Time Exam Embedding | N/A | **`1.0000`** | **VULNERABLE** | Embedded publicly committed exam dataset at compile-time via `//go:embed`. |

**Conclusion:** Vishu Porwal's Day 5 hardening successfully closed all runtime attack surfaces (Cheats 1–3 scoring 0.0000). However, the task remains critically vulnerable to compile-time exam embedding (Cheat 4 scoring 1.0000). Complete hardening requires generating hidden exams dynamically in memory with uncommitted random seeds, enforcing `network_mode = "none"` in `task.toml`, and imposing binary size limits to prevent lookup-table memorization.
