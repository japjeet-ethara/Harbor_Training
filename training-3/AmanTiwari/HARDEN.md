# HARDEN.md — Day 5

Task: `training-3/AmanTiwari/task` (my practice-1 titlecase-go, hardened).
Attacker: **Ayush Singh** — report at `training-3/AyushSingh/attack/ATTACK.md`.

Every "after" number below is from a real Harbor run on the hardened task
(local Docker, 2026-11-19); the job folder is given and the `reward.json` is in
`../AmanTiwari/proof/`. The "before" numbers are Ayush Singh's own Harbor runs on
the old task (`../AyushSingh/attack/results/`).

Proof runs on the hardened task:

| Run | reward | job folder |
|---|---|---|
| oracle | **1.000** | jobs/2026-11-19__18-31-01 |
| nop | **0.000** | jobs/2026-11-19__18-35-59 |

## Holes closed

Ayush Singh's three cheats all scored above 0.2 on the old task; each is now
below 0.2, re-run on the hardened task:

| Cheat | How it beat the old exam | before | after | job folder | fix |
|---|---|---|---|---|---|
| 1 — build trick (empty Go program) | build + no_python paid 2/6 points for a program that printed nothing | **0.333** | **0.000** | jobs/2026-11-19__18-38-16 | gates, not points |
| 2 — half port (cap words + small-word list) | proportional behaviour paid for the few lines a naive port gets right, on top of the free 2/6 | **0.438** | **0.140** | jobs/2026-11-19__18-40-41 | gates + bigger/weirder exam |
| 3 — Python inside (os/exec to run the original) | no check looked at imports; the verifier image has python3 | **1.000** | **0.000** | jobs/2026-11-19__18-44-02 | new `no_exec` gate (no_exec=0) |

### Fix 1 — hard rules are gates, not points (`tests/reward.toml`, `tests/behaviour/behaviour.py`)
`reward = behaviour` only (build, no_python, no_exec have weight 0), and
`behaviour` returns 0 unless all three gates pass. So a program that builds but
does no titlecasing scores 0, and deleting the Python is necessary but no longer
worth anything by itself. This alone takes cheat 1 to 0 and drops cheat 2 to its
true match share.

### Fix 2 — a real `no_exec` gate (`tests/no_exec/no_exec.py`, `tests/_shared.py`)
The program must be a single Go module whose own packages import none of
`os/exec`, `syscall`, `unsafe`, `plugin`, `runtime/cgo`, with no second `go.mod`
and no `StartProcess` / `go:linkname` in the source. Imports are read from the
author's own packages (`go list ./...`), not the whole stdlib closure (every
honest port pulls in `syscall`/`unsafe` transitively through `os`). A nested
`go.mod` is rejected outright, so `os/exec` cannot be smuggled behind a
`replace` — the exact trick I used to beat my own target on Day 4. Cheat 3 → 0.

### Fix 3 — bigger, weirder exam (`kit/`, `tests/data/`)
Replaced the 2,000-title hidden set with **100,000** titles from
`kit/make_pool.py` (seed 1), answers frozen twice by `kit/answers.py` (see
`kit/report.txt`: 0 dropped, mode `re`). The weirder pool pushes the half port
from 0.157 down to 0.140.

## Exam: before and after

Old exam: 2,000 hidden titles.  New exam: **100,000** titles, mode **`re`**
(plain Python, `regex` package not installed — stated in `instruction.md`).

Wrong-answer counts from `kit/compare.py` (outputs in `measure/`):

| Port | wrong on new exam (of 100,000) | note |
|---|---|---|
| my oracle (`solution/solve.sh`) | **0** | the hardened oracle is byte-exact |
| Ayush Khurana's oracle | **0** | correct port; my exam has no false positives |
| Ayush Singh's oracle | **0** | correct port; my exam has no false positives |
| *(reference)* the half port (cheat 2) | **86,041** | a weak port is caught everywhere |

The two real classmate ports are correct oracles, so there was nothing subtle to
catch — an honest result, not a failure of the exam: the 100k set never rejects a
correct port. Where it earns its keep is the lessons the kit is built around:

- **Weird inputs beat many inputs.** The half port is wrong on 86% of the pool
  because the pool is full of the cases it ignores (Mc-names, `//`, apostrophe
  names, no-break spaces, Greek/Cyrillic, all-consonant acronyms). A 2,000-title
  exam that happened to miss those word families could have scored it much higher.
- **Mode matters.** `titlecase` gives different answers with vs without the
  optional `regex` package (the class measured 3,053 of 100,000 differ). A port
  that matched the wrong mode would fail only on those rare lines — invisible to a
  small exam. My exam fixes the mode to plain `re` and says so in `instruction.md`.

## What I learned (3 lines)

1. Free points are the real hole: 2/6 for "it compiles and the .py are gone" let a
   do-nothing program clear a third of the bar. Gating behaviour closed cheats 1–3 more than the bigger exam did.
2. Checking imports needs the author's own packages, not the transitive closure —
   stdlib uses `syscall`/`unsafe` everywhere, so a naive ban fails every real port.
3. A correct port scoring 0 wrong on 100k is a *good* sign (no false positives); the
   exam's value shows up on weak or wrong-mode ports, which a small random exam can miss.
