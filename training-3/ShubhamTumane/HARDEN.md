# Task Hardening Report: `ShubhamTumane/titlecase-go`

## 1. Benchmark Suite Reconstruction (100,000 Frozen Titles)
- **Pool Generation (`kit/make_pool.py`):** Generated 100,000 unique synthetic inputs (`count = 100000`, `seed = 1`) covering stop words, boundary words, `Mc`/`Mac` prefixes, `d'`/`o'`/`l'` apostrophes, honorifics (`mr`, `Mrs`, `MS`, `Dr`), dotted abbreviations, URLs, slash/hyphen compounds, consonant-only acronyms, mixed-case brand names (`iPhone`, `eBay`, `macOS`, `gTLD`), Unicode letters (`straße`, `İstanbul`, `αlpha`, `дом`), surrounding punctuation, and consecutive/non-ASCII whitespace (` `, `\t`, `\u00a0`, `\u2009`).
- **Frozen Answer Key (`kit/answers.py` & `kit/report.txt`):** Evaluated twice under isolated Python (`-I`) with `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2` against the original `python-titlecase` source in standard-library `re` mode (`REGEX_AVAILABLE = False`):
  - `pool inputs`: `100000`
  - `kept (stable)`: `100000`
  - `dropped (unstable)`: `0`
  - `regex module used`: `False`

## 2. Three-Port Comparative Measurement (100,000-Title Exam)

| Port | Author | 100k Exam Errors | Miss Chance on 2,000 Suite | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `my-oracle` (Initial v1) | Shubham Tumane | `46,440 of 100,000` | `0%` | Missed consecutive whitespace splitting, `all_caps` empty-string behavior, ASCII-only consonant check, and `small_last` punctuation boundaries. |
| `my-oracle` (Fixed v2) | Shubham Tumane | `0 of 100,000` | `100%` | Exact byte-for-byte parity with `python-titlecase` (`re` stdlib mode). |
| `KanishkaSharma` | Kanishka Sharma | Crashed at line 135 (`135 / 100,000` lines) | `0%` | Panicked (`index out of range [21] with length 20` in `main.joinWords`) on consecutive whitespace tokens. |
| `Isha-Jakhad` | Isha Jakhad | `0 of 100,000` | `100%` | Exact byte-for-byte parity across all 100,000 titles. |

## 3. Vulnerabilities Closed in `ShubhamTumane/task`

| Vulnerability | Root Cause in Original Task | Hardening Fix Implemented |
| :--- | :--- | :--- |
| **Hidden Test Suite Leakage & Runtime Read** | Small 2,000-line fixture and readable `/tests/data` during binary execution allowed lookup/file-read cheats. | Replaced the fixture with the 100,000-line frozen suite (`tests/data/inputs.txt` and `tests/data/answers.txt`) and locked `/tests/data` (`chmod 000`) while running the untrusted binary as `nobody`. |
| **Free Points for Stubs & Identity (`echo`)** | `check_build` and `check_no_python` awarded `1.0` independently (`2/11 = 0.1818`), and unchanged lines inflated `behaviour`. | Gated `check_build` and `check_no_python` behind `evaluate_behaviour(workspace) > 0.25`, and restricted `behaviour` scoring strictly to lines where `input != expected` (requiring `100%` accuracy on unchanged lines). |
| **Extra Output Lines / Marker Cheats** | Prefix/line-based parsing allowed appending extra diagnostic lines. | Enforced strict exact line-count equality (`len(actual_lines) == len(exp_lines)`), returning `0.0` on any mismatch. |
| **Runtime Python / Shell Wrapper Cheats** | `no_python.py` only checked for `*.py` files on disk. | Removed `python3` from `environment/Dockerfile` and updated `tests/no_python.py` to reject `.py`/`.pyc`/`.sh` files, `os/exec`/`syscall`/`python` imports in Go code, and `python3`/`/bin/sh` strings in compiled binaries. |

## 4. Verification Proof Summary
- **Oracle (`jobs/2026-11-20__12-29-20`, `proof/oracle-reward.json`):** `reward = 1.0` (`build = 1.0`, `no_python = 1.0`, `behaviour = 1.0` across 100,000 titles).
- **NOP (`jobs/2026-11-20__12-30-31`, `proof/nop-reward.json`):** `reward = 0.0`.
- **Incoming Attacker Cheats — Isha Jakhad (`proof/cheats-reward.txt` & `proof/isha-cheat*-reward.json`):**
  - Cheat 1 (Python Inside, `defense_jobs/cheat1/2026-11-20__11-53-43`): `reward = 0.0` (down from `1.0000`).
  - Cheat 2 (Half Port, `defense_jobs/cheat2/2026-11-20__11-48-52`): `reward = 0.0` (down from `0.7027`).
  - Cheat 3 (Build Trick, `defense_jobs/cheat3/2026-11-20__11-50-21`): `reward = 0.0` (down from `0.6667`).
- **Self-Hardening Stress Cheats (`proof/self-cheats-reward.txt`):**
  - Self Cheat 1 (`jobs/2026-11-19__23-05-11`): `reward = 0.0`.
  - Self Cheat 2 (`jobs/2026-11-19__23-06-10`): `reward = 0.0`.
  - Self Cheat 3 (`jobs/2026-11-19__23-07-14`): `reward = 0.0`.