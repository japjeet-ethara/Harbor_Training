# Day 6 — Defence Notes

## 1. The Strongest Cheat Against My Task

- **Strongest cheat:** Cheat 1 (Read the exam) and Cheat 2 (Python inside), both of which originally scored a perfect **1.000** on my practice task with zero titlecase Go logic.
- **Cheat 1 Mechanism:** In the original setup, the verifier container ran as root and left `tests/data/hidden_expected.txt` readable on disk. The cheat walked the filesystem, loaded the hidden expected answers into memory, and printed them verbatim.
- **Before score:** `1.0` (Job: `scratch/jobs/2026-11-18__20-02-46`)
- **After hardening score:** `0.0000` (Job: `jobs/2026-11-19__16-35-02`)
- **The fix:**
  1. Ran the test binary as unprivileged user `runner` in `/tmp` with restricted `PATH`.
  2. In `tests/checks/behaviour.py`, reference answers are loaded into memory and unlinked (`unlink()`) from disk before the agent binary runs. While the binary executes, the answer sheet does not exist on disk anywhere in the container.

---

## 2. Before-and-After Exam Table

- **Old exam:** 2,000 inputs (mode unstated)
- **New exam:** 100,000 inputs (mode: `re`, frozen twice with 0 dropped)

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **my oracle** | 0 | n/a | n/a | Initial oracle failed 3,232 on `_dream`; fixed `capFirst` logic |
| **NehaGaur** | 9,935 | no (scored 1.0) | 0.00% | Fails `BBC: OF`, `v1.2`, `_dream`, acronyms |
| **MadhurJain** | 3,232 | no (scored 1.0) | 0.00% | Fails `_dream` leading underscore tokenization |

---

## 3. One Surprise

- **The `_dream` leading underscore bug:**
  When I ran my own oracle against the new 100,000-input exam, it failed **3,232** inputs. Every single failure was caused by titles containing `_dream`.
  In Python `re`, `CAPFIRST = re.compile(r"^[%s]*?([\w])" % PUNCT)` has non-greedy punctuation matching. Because `_` is both in `PUNCT` and in `\w`, non-greedy match stopped at index 0 and matched `_` as `\w`, replacing `_` with `_` and leaving `d` lowercase (`_dream`). My Go port previously treated `_` strictly as punctuation and skipped it, capitalizing `d` to `D` (`_Dream`).
  Finding this bug in my own port proved that increasing diversity with weird edge cases finds real flaws that 2,000 clean titles completely miss.

---

## 4. Verification Proof Summary

- **Oracle:** `1.0000` (Job: `jobs/2026-11-19__16-29-51`) -> `proof/oracle-reward.json`
- **Nop:** `0.0000` (Job: `jobs/2026-11-19__16-32-57`) -> `proof/nop-reward.json`
- **Attacker Cheats:**
  - Cheat 1: `0.0000` (Job: `jobs/2026-11-19__16-35-02`)
  - Cheat 2: `0.1667` (Job: `jobs/2026-11-19__16-37-52`)
  - Cheat 3: `0.0000` (Job: `jobs/2026-11-19__16-40-24`)
  All attacker cheats score strictly below `0.20`.
