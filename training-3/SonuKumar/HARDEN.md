# Task Hardening & Verification Report: `titlecase-go`

- **Task Target**: `Harbor_Day4_Workspace/Sonu Kumar/task/`
- **Trainee / Maintainer**: Sonu Kumar
- **Repository Branch**: Active branch `training-3`
- **Working Tree Status**: Uncommitted changes maintained in working tree (commit/push withheld pending final sign-off)
- **Harbor CLI Version**: 0.25.0 (Docker Desktop 29.9.2 on Windows x86_64 host)
- **Evaluation Suite**: 100,000-title high-entropy exam (`pool.txt`, seed `1`, mode: `WITHOUT regex`)
- **Scoring Policy**: Policy B (`weights = { build = 0.5, no_python = 0.5, behaviour = 9.0 }`)

---

## 1. Holes Closed

Three distinct attacker vulnerabilities were identified, audited, patched, and verified in Harbor:

### Cheat 1: Phantom Criteria Registration & Delete-Only Exploitation
- **Original Attacker Reward**: `0.7619` (Job `jobs/2026-11-19__17-04-18`, Trial `cheat1__UkgYnTx`)
- **Final Hardened Reward**: `0.0500` (Job `jobs/2026-11-20__12-35-45`, Trial `cheat1_main__qJ6r3aQ`)
- **Vulnerability Mechanism**:
  1. *Duplicate Criteria Scoring*: In the original task, `criteria.py` used `@criterion` decorators while simultaneously being imported by standalone check scripts (`build.py`, `no_python.py`, `behaviour.py`). RewardKit registered duplicate criteria under a phantom `criteria` group, inflating the unearned base reward from $\approx 0.67$ to $\frac{16}{21} \approx 0.7619$.
  2. *Delete Trick*: The attacker simply deleted all `.py` files and compiled a trivial echo binary (`fmt.Print(stdin)`). Since no `.py` files remained, `no_python_check` scored `1.0`, and `build` scored `1.0`.
- **Hardening Fix**:
  1. Converted `task/tests/criteria.py` into a pure un-decorated helper module, eliminating all duplicate criteria registration.
  2. Hardened `no_python_check` by adding an isolated functional smoke test: the submission must successfully compile and correctly titlecase `"a tale of two cities"` $\to$ `"A Tale of Two Cities"`. Trivial echo stubs fail this smoke test and receive `0.0`.
  3. Adopted Policy B, reducing `build` weight to `0.5` out of `10.0` ($\frac{0.5}{10.0} = \mathbf{0.0500}$).

### Cheat 2: Ground-Truth Answer Leakage at Runtime
- **Original Attacker Reward**: `1.0000` (Job `jobs/2026-11-19__17-06-26`, Trial `cheat2__VPcsc95`)
- **Final Hardened Reward**: `0.1481` (Job `jobs/2026-11-20__12-39-46`, Trial `cheat2_leak_main__R8g3t2c`)
- **Vulnerability Mechanism**:
  The attacker binary ignored `stdin` and read ground-truth answers directly from the grader's filesystem (`/tests/data/hidden_expected.txt`) using Go's `os.ReadFile`, completely circumventing the titlecasing requirement.
- **Distinction Between Leakage Exploit & Naive Half-Port**:
  - *Leakage Exploit (`scratch/cheat3/...`, original `attack/cheat2/solve.sh` target)*: Actively attempted to read `/tests/data/` files at runtime; scored `1.0000` before hardening. On the hardened task, because access is denied, it falls back to a procedural `naiveTitle()` routine.
  - *Naive Half-Port (`attack/cheat2/solve.sh`, Job `jobs/2026-11-20__12-37-57`)*: Directly executes `naiveTitle()` without attempting filesystem reads. It was isolated as an independent evaluation variant during the 100K exam investigation and was not independently tested before hardening.
  - *Result on Hardened Task*: Because filesystem access was blocked, both variants executed identical capitalization logic, matching 10,905 of 100,000 titles and scoring an identical legitimate partial credit of **`0.1481`**.
- **Hardening Fix**:
  1. Hardened `task/tests/Dockerfile`: Set `chown -R root:root /tests && chmod -R 700 /tests`. Untrusted users have zero read, write, or execute permissions on the `/tests` tree.
  2. Hardened `task/tests/criteria.py`: Executes all user binaries under unprivileged user `nobody:nogroup` (UID 65534, GID 65534) inside ephemeral scratch directories (`/tmp/tc-exec-...`).
  3. Ground-truth inputs are piped solely via standard input (`stdin`); ground-truth answers remain strictly in memory within the root verifier process.

### Cheat 3: Embedded Reference Delegation via External Python Subprocess
- **Original Attacker Reward**: `1.0000` (Job `jobs/2026-11-19__17-08-12`, Trial `cheat3__BDty7Hm`)
- **Final Hardened Reward**: `0.0500` (Job `jobs/2026-11-20__12-43-47`, Trial `cheat3_main__y8HqZ2c`)
- **Vulnerability Mechanism**:
  The attacker embedded a base64-encoded copy of `python-titlecase` inside `main.go`, deleted all `.py` files to satisfy the file tree scan, and at runtime unpacked the Python module to `/tmp` and spawned `/usr/local/bin/python3` via Go's `os/exec` package.
- **Hardening Fix**:
  1. *Host-Level DAC Restriction (`task/tests/Dockerfile`)*: Set `chmod 700 /usr/local/bin/python* /usr/local/bin/uv*` owned by `root:root`. The unprivileged child process `nobody:nogroup` is denied execute permissions (`EACCES`).
  2. *Environment Sanitization (`task/tests/criteria.py`)*: Sanitized child process execution environment to `PATH="/usr/bin:/bin"`, removing Python from search paths.
  3. *Static Import Policy Guard (`task/tests/criteria.py`)*: Added `has_banned_imports()` using `go list -f '{{range .Imports}}{{.}} {{end}}' ./...` to strictly reject submissions importing `os/exec`, `syscall`, `syscall/js`, or `plugin`.

### Summary Matrix of Verification Jobs

| Evaluation Target | Script Evaluated | Before Hardening Reward | Hardened Task Job Path | Hardened Score | Target Status |
|:---|:---|:---:|:---|:---:|:---:|
| **Genuine Go Oracle** | `task/solution/solve.sh` | 1.0000 | `jobs/2026-11-20__12-33-13` | **1.0000** | **PASSED** ($\ge 1.00$) |
| **Cheat 1 (Delete trick)** | `attack/cheat1/solve.sh` | 0.7619 | `jobs/2026-11-20__12-35-45` | **0.0500** | **PASSED** ($< 0.10$) |
| **Cheat 2 (Leakage)** | `scratch/cheat3/...` | 1.0000 | `jobs/2026-11-20__12-39-46` | **0.1481** | **PASSED** ($< 0.20$) |
| **Naive Go Half-Port** | `attack/cheat2/solve.sh` | Not independently tested | `jobs/2026-11-20__12-37-57` | **0.1481** | **PASSED** ($< 0.20$) |
| **Cheat 3 (Python inside)**| `attack/cheat3/solve.sh` | 1.0000 | `jobs/2026-11-20__12-43-47` | **0.0500** | **PASSED** ($< 0.10$) |

---

## 2. Exam: Before and After

| Parameter | Old Exam Baseline | New Hardened Exam |
|---|---|---|
| **Case Count** | 2,000 cases | **100,000 cases** |
| **Generation Seed** | Unspecified / synthetic | **Fixed Seed `1`** (Trainer `kit/make_pool.py`) |
| **Reference Engine** | Python titlecase | `task/environment/repo-source` (`python-titlecase 2.4.1`) |
| **Reference Mode** | Unspecified / ambiguous | **WITHOUT regex** (`REGEX_AVAILABLE = False`, standard `re`) |
| **Pool Stability** | Unverified | **100,000 stable cases kept, 0 unstable cases dropped** |
| **Dataset Hashes (LF)** | `inputs.txt`: 76,974 B | `hidden_inputs.txt`: `b5b839621b4d7b1e2ddba50e716aa57b6ce437d2ee22777590810d155c72a331`<br>`hidden_expected.txt`: `c898bf68e5fc0e392867b90213c41e8814af0c57417f045c6d796425c5d60095` |
| **Go Oracle Performance** | 2,000 / 2,000 (100.0%) | **100,000 / 100,000 (100.00% exact match)**<br>- Pure Go binary throughput: **~1.7s** (`real 0m1.74s` in Docker benchmark)<br>- Full Harbor trial duration: **1m 22s** (82.5s recorded in `jobs/2026-11-20__12-33-13/result.json`) |

### Why the New Exam Provides Superior Verification
1. **Elimination of Toy Bias**: The old 2,000-case exam consisted almost entirely of standard, simple English phrases (e.g. `"a tale of two cities"`, `"rules: and exceptions"`), allowing flawed or naive ports to pass with 100% scores.
2. **Exhaustive Edge-Case Density**: The trainer-generated 100,000-title exam includes Unicode letter scripts (Greek, Cyrillic), unusual whitespace characters (non-breaking spaces `\xa0`, thin spaces `\u2009`), compound punctuation (`"word"`, `\data`, `road{`), version numbers (`v1.2`), and hyphenated/slashed terms.
3. **Strict Mode Specificity**: By pinning generation strictly to `REGEX_AVAILABLE = False`, the suite deterministically penalizes ports that copied regular expressions from the alternate `regex` module branch.

---

## 3. Three Go Port Comparison

Each port was compiled natively and evaluated on the 100,000-case suite using the trainer's unmodified `kit/compare.py` against `key/` (reported in `measure/`):

| Port Identifier | Author | Implementation Architecture | Lines of Go | Wrong Answers (100K) | Accuracy (%) | Old 2K Exam Caught It? | Chance Random 2K Misses It |
|---|---|---|---:|---:|---:|:---:|:---:|
| **Genuine Go Oracle** | Sonu Kumar | Native non-regex Go state machine | 319 | **0 of 100,000** | **100.00%** | n/a (0 wrong) | 100% |
| **Classmate A Port** | Sanyam Sehrawat | Go `regexp` port (regex-branch rules) | 447 | **3,053 of 100,000** | **96.95%** | **NO** (0 / 2,000 wrong) | **$6.19 \times 10^{-28}$** ($\approx 0\%$) |
| **Classmate B Port** | Alok Kumar Jaiswal | Procedural rune scanner without `regexp` | 679 | **28,064 of 100,000** | **71.94%** | **NO** (0 / 2,000 wrong) | **$2.82 \times 10^{-290}$** ($\approx 0\%$) |

### Important Distinction: Original 2K Exam vs Random 2K Draw
- **Original Hand-Crafted 2K Exam**: Both Sanyam and Alok scored **100.00% (0 errors)** on the original 2,000-case baseline. Because the original exam lacked version strings, non-Latin scripts, and exotic punctuation, it was completely blind to their bugs.
- **Random 2K Draw from New 100K Pool**: A random sample of 2,000 cases drawn uniformly from the new pool has an error-detection probability of $1 - \frac{\binom{N-B}{k}}{\binom{N}{k}}$. The chance of missing all 3,053 errors in Sanyam's port is $6.19 \times 10^{-28}$, and the chance of missing all 28,064 errors in Alok's port is $2.82 \times 10^{-290}$—both mathematically virtually impossible to escape.

### Representative Mismatches and Root Causes

#### 1. Sanyam Sehrawat (`measure/sanyam-sehrawat.txt`)
- **Observed Errors**:
  - `input 'v1.2'` $\to$ `want 'v1.2'` | `got 'V1.2'`
  - `input 'mrs. in star“ v1.2\u2009the|'` $\to$ `want 'Mrs. In Star“ v1.2\u2009The|'` | `got 'Mrs. In Star“ V1.2\u2009The|'`
  - `input "to eBay BOOK D'Angelo\xa0o'neil v1.2 WORLD"` $\to$ `want "... v1.2 WORLD"` | `got "... V1.2 WORLD"`
- **Root Cause**:
  In python-titlecase without regex, `INLINE_PERIOD = re.compile(r'[\w][.][\w]', re.I)`. Because standard `\w` includes digits `0-9`, `1.2` matches and preserves `v1.2` in lowercase. Sanyam ported the `regex` module pattern `[\p{Letter}][.][\p{Letter}]`, which fails on digits and incorrectly capitalizes `V1.2`.

#### 2. Alok Kumar Jaiswal (`measure/alok-kumar-jaiswal.txt`)
- **Observed Errors**:
  - `input "Dr D'Angelo  vs.\u2009αlpha..."` $\to$ `want "Dr d'Angelo  vs.\u2009Αlpha..."` | `got "Dr d'Angelo  Vs.\u2009αlpha..."`
  - `input 'FTP://HOST/FILE ... "ΑLPHA'` $\to$ `want '... "Αlpha'` | `got '... "αlpha'`
  - `input 'war\xa0\\data\u2009%summer'` $\to$ `want 'War\xa0\\Data\u2009%Summer'` | `got 'War\xa0\\data\u2009%summer'`
- **Root Cause**:
  Alok avoided the standard `regexp` library and implemented manual scanning routines. His parser fails to capitalize Greek characters (`α` $\to$ `Α`), mishandles casing after leading quotes (`"Αlpha`), fails word segmentation around non-breaking spaces (`\xa0`) and backslashes (`\\data`), and mishandles small words when separated by thin spaces (`\u2009`).

---

## 4. What I Learned

1. **Separation of Grader and Helper Logic**: Evaluation criteria must never import helper modules that declare criteria annotations themselves; uncoupling test execution from helper utilities prevents silent criteria duplication and accidental grading inflation.
2. **Kernel-Enforced Privilege Boundaries**: Security cannot rely on language-level file scans or regex filters; genuine enforcement requires running untrusted submissions under isolated unprivileged identities (`nobody:nogroup`), stripping search paths, and applying kernel DAC permissions (`0700`) to both answers and host interpreters.
3. **The Necessity of High-Entropy Scaling**: Small, clean test suites breed a false sense of correctness. Scaling to a deterministic, high-entropy 100,000-case exam immediately exposes subtle divergence in regex engines, Unicode handling, and incomplete procedural ports that scored 100% on toy suites.

---

## 5. Remaining Limitations

1. **Kernel DAC Boundaries vs Deep Isolation**: File system permissions (`0700 root:root`) and unprivileged user accounts (`nobody`) effectively block direct file reads and system binaries, but they do not provide full container namespacing (seccomp, eBPF, network namespaces) against kernel-level privilege escalation or memory inspection if the untrusted binary were to exploit kernel vulnerabilities.
2. **Static Import Analysis Limits**: Checking `go list` imports detects explicit dependencies on `os/exec` or `syscall`, but cannot prevent obfuscated syscalls invoked via direct assembly stubs (`.s` files) or dynamic runtime manipulation if Go cgo or raw assembly were permitted.
3. **Empirical Robustness vs Formal Proof**: Defeating the three specific demonstrated attacks confirms resilience against the known attack surface, but does not constitute mathematical proof of immunity against novel, unmodeled side-channel attacks, CPU timing leaks, or grader memory inspection.

---

## 6. Artifact & File References

- **Hardened Task Directory**: `Harbor_Day4_Workspace/Sonu Kumar/task/`
- **Measurement Reports**:
  - `measure/my-oracle.txt`
  - `measure/sanyam-sehrawat.txt`
  - `measure/alok-kumar-jaiswal.txt`
- **Exam Kit Verification**: `kit/report.txt` (Identical to `key/report.txt`)
- **Pre-Hardening Evidence**: `proof(Before Hardening)/`
- **Validation Audit Logs**: `CHEAT1_VALIDATION.md`, `CHEAT2_VALIDATION.md`, `CHEAT3_VALIDATION.md`, `EXAM_100K_MAIN_VALIDATION.md`
