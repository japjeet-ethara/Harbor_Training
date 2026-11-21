# Hardening Report — Vishu Porwal / titlecase-go

## 1. Published Baseline & Attacker Findings

- **Published Baseline Revision:** `512aba1` (`512aba1c0f0a70c960b7d2fded998276b6445310`)
- **Attacker Evaluation:** Omar Ghyas (`training-3/OmarGhyas/attack/ATTACK.md`) tested Practice 1 commit `9a08b05d247a16f3c1448b03711add5a8392bbe9`, whose task tree matches the unchanged published baseline `512aba1`. Omar demonstrated three successful attack vectors against this baseline:
  - **Cheat 1 (Build trick / Empty program):** Baseline score **`0.3333`** (earned unearned structural credit by deleting `.py` files and compiling an empty Go module without producing any behavioral outputs).
  - **Cheat 2 (Read the exam / Static answer leak):** Baseline score **`1.0000`** (read `/tests/data/hidden_expected.txt` directly from the verifier filesystem and echoed the answers to stdout).
  - **Cheat 3 (Python inside / Subprocess execution):** Baseline score **`1.0000`** (stashed Python code under an extensionless file and invoked `python3` via Go subprocess at runtime).

---

## 2. Verifier Hardening

### Scoring Model
- Replaced the decoupled weighted-sum scoring rubric (`build: 1.0, no_python: 1.0, behaviour: 4.0`) with a strict prerequisite model.
- `build` and `no_python` are now hard prerequisites for earning behavioral credit:
  - If either `build` or `no_python` fails, the final reward is strictly **`0.0`**.
  - When both pass, the reward equals the behavioral score (`behaviour`), preserving partial credit proportional to exact matching outputs.
  - In `reward.toml`, the weights are configured as `build = 0.0, no_python = 0.0, behaviour = 1.0`.

### Filesystem Jail Isolation
- **Verified Isolation Properties:** Verified via trusted diagnostic execution using the production verifier image (`titlecase-verifier:latest`) and jail launcher (`chroot --userspec=65534:65534 --groups=`):
  - **Effective User & Group ID:** `65534:65534` (`nobody:nogroup`).
  - **Supplementary Groups:** Empty (`[]`), verified cleared.
  - **Working Directory:** `/`.
  - **Filesystem Root Entries:** Only the executable itself is present and visible at root (`/`). Grader scripts, answer keys (`hidden_expected.txt`), source files, and Python interpreters are outside the jail and not visible or accessible to the program.
  - **Standard I/O:** Exam inputs are received via `stdin`, while `stdout` and `stderr` are captured.
- **Unverified / Non-Isolated Capabilities:**
  - The jail provides filesystem isolation and credential drop only.
  - It does **not** provide network namespace isolation (network access remains unisolated).
  - It does **not** provide PID/process namespace isolation.
- **Grader Integration & Scoring:**
  - The submitted Go binary is built into a fresh, isolated, verifier-owned directory.
  - Permissions are set so the executable is readable and traversable without write access by the runtime user.
  - All inherited file descriptors except standard I/O are closed (`close_fds=True`).
  - If jail setup fails or the binary exits with a non-zero code, zero behavioral credit (`0.0`) is awarded.

### Byte-Level Output Comparator & Record Count Enforcement
- **Record Parsing & Delimitation:** Replaced string-decoded line splitting (`run.stdout.decode("utf-8").splitlines()`) with byte-level parsing using LF (`\n`) as the record delimiter (`_split_records`). Blank records (`b""`) and trailing spaces within records are strictly preserved.
- **Fixture Validation:** Validates that `hidden_inputs.txt` and `hidden_expected.txt` contain the exact same nonzero number of records; any mismatch or empty fixture awards zero behavioral credit (`0.0`).
- **Record Count Enforcement:** Missing or extra output records earn strictly zero behavioral credit (`0.0`).
- **Byte-for-Byte Comparison:** When the record count matches expected, partial credit is awarded by comparing corresponding records byte for byte (`matches / total_records`). Outputs using CRLF (`\r\n`) in place of LF retain the trailing `\r` byte and fail byte-for-byte comparison against expected LF records.
- **Synthetic Test Verification:** All ten synthetic test cases passed cleanly inside the production verifier container:
  - Exact output scores `1.0`.
  - One wrong record out of two scores `0.5`.
  - Extra records score `0.0`.
  - Missing records score `0.0`.
  - CRLF in place of LF scores `0.0`.
  - Nonzero process exit scores `0.0`.
  - Blank records and trailing spaces preserved scores `1.0`.
  - Fixture record length mismatch scores `0.0`.
  - Empty input fixture scores `0.0`.
  - Empty expected fixture scores `0.0`.

---

## 3. Hardened Exam Dataset

A large-scale, hardened exam dataset was generated using the exam kit scripts (`make_pool.py` and `answers.py`):
- **Runtime Environment:** Python `3.14.10` managed by `uv`.
- **Mode:** Standard-library `re` mode (forced `-S` to disable site-packages, preventing optional third-party `regex` loading so that `REGEX_AVAILABLE = False`).
- **Input Generation:** Seed `42`, retaining `100,000` unique title inputs.
- **Answer Stability:** Evaluated twice under independent hash seeds (`PYTHONHASHSEED=1` and `PYTHONHASHSEED=2`); **0** titles dropped (100% stability across all 100,000 inputs).
- **Verified SHA-256 Hashes:**
  - `hidden_inputs.txt`: `BAAD841E7CF87E774357BAD7A9B7E216062CF59B09E2DA1B4D619FEA746F43F1`
  - `hidden_expected.txt`: `9A7A29EA1BCE70DCABAE1F0B877A28F6C5E48D76C1B187EBD719022CB29D4111`
- The exam files were installed byte for byte with explicit LF line endings.

---

## 4. Controls & Port Measurements

Detailed comparative measurements and original verifier reward files are recorded in [measure/RESULTS.md](measure/RESULTS.md).

### Verified Controls
- **Old Exam (2,000 titles):**
  - **Oracle:** `1.0` (Harbor Job ID: `063bc1c5-c2af-43fa-9150-d310612a5805`)
  - **Nop:** `0.0` (Harbor Job ID: `652ee0c3-8011-4a5a-8219-1b0f0911a5cf`)
- **Initial 100,000-Title Controls (Predating Comparator Fix):**
  - **Oracle:** `1.0` (Harbor Job ID: `8cd0739c-c9d9-4e6d-8aef-9fb7e60d71fa`)
  - **Nop:** `0.0` (Harbor Job ID: `1d16f76f-6111-4f49-998f-eadf615330e9`, completed one trial with zero exceptions on the same snapshot as oracle job `8cd0739c-c9d9-4e6d-8aef-9fb7e60d71fa`)
- **Final 100,000-Title Controls (Post-Comparator Fix):**
  - **Oracle:** `1.0` (Harbor Job ID: `003429de-506e-42c0-b09c-bf47bd278d5d`)
  - **Nop:** `0.0` (Harbor Job ID: `c0b520d0-5732-4466-bc6d-28f656f79182`)

### Reference Port Measurements on 100k Exam (Predating Comparator Fix)
*Note: The following measurements were recorded prior to the byte-level comparator fix.*
- **Vishu Porwal Reference Solution (`512aba1`):** `1.0` reward (Harbor Job ID: `8cd0739c-c9d9-4e6d-8aef-9fb7e60d71fa`).
- **Nikhil Choudhary Reference Port (`a1173ff`):** `0.9602` reward (96,017 / 100,000 matches, Job ID: `df426668-ac1c-46ac-9dd9-0bfbc523db23`).
- **Omar Ghyas Reference Port (`1aea2bf`):** `0.9697` reward (96,971 / 100,000 matches, Job ID: `f1ce426f-97b9-4173-9146-785e991c60cd`).

---

## 5. Post-Hardening Cheat Evaluations

Post-hardening evaluation trials for Omar Ghyas's three reported attack cases:

| Attack Case | Baseline Score | Post-Hardening Status | Harbor Job ID |
| :--- | :--- | :--- | :--- |
| **Cheat 1 (Build Trick / Empty Program)** | `0.3333` | **Pending** | Pending |
| **Cheat 2 (Read the Exam / File Leak)** | `1.0000` | **Pending** | Pending |
| **Cheat 3 (Python Inside / Subprocess)** | `1.0000` | **Pending** | Pending |

*Status Note:* Because formal post-hardening evaluations for these three specific attack cases remain pending, no claim is made that the below-0.20 threshold requirement has been verified for them.
