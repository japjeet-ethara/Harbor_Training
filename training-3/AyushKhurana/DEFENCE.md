# DEFENCE — Ayush Khurana (notes for the 5-minute talk)

My task: `ayushkhurana/titlecase-go`. Attacker on Day 4: Aman Tiwari. All rewards below are from
Harbor 0.25.0 runs (job folders in `proof/`); the before-hardening numbers are Aman's own.

## 1. The strongest cheat against my task
Aman's **Cheat 2 (hidden Python)** and **Cheat 3 (download the answers)** both scored **1.0** before.
- Cheat 2 hid `os/exec` in a nested Go module (`replace tc/run => ./run`) and ran the original Python,
  kept as `orig.txt`, through the image's `python3`. My old `no_exec` gate ran `go list ./...`, which
  never enters a nested module, so the forbidden import was invisible; and `.py` was checked by file
  name only, so Python under another name passed.
- Cheat 3 downloaded my hidden answers from the public repo at solve time — the agent room had
  `network_mode = "public"` and the answers were committed.
- His **Cheat 1 (half port)** scored 0.144: a weak port still earned partial credit.

**Fixes, and what they score now:**
- The `no_exec` gate now reads the **whole build** (`go list -deps -json ./...`): any nested `go.mod`,
  `go.work`, non-main module, `os/exec` anywhere in the closure, `syscall`/`unsafe`, or cgo/assembly
  fails it. Cheat 2 → **0.0**.
- The grader image locks `python3` and `/opt/uv` to root; the program runs as `nobody` with
  `PATH=/nonexistent`. Even past a gate, no Python runs.
- The agent network is an **allowlist** (model host only), and the score is the **lower of a fixed
  100,000-line exam and a fresh 20,000-line exam made at grading time**. Cheat 3 (download) → **0.0**;
  a lookup of all 100,000 public answers → **~0.05** (1.0 on the frozen set, ~0.05 on the fresh one).
- Cheat 1 (half port) stays ~**0.137** on purpose — below 0.2, and a gradient is what makes the score
  useful.

Targets met: oracle 1.0, nop 0.0, every cheat below 0.2.

## 2. My exam, before and after
Old: 2,000 hidden titles from my own generator. New: a fixed **100,000-line** exam from the kit
(`make_pool.py`, seed 20261119) plus a **20,000-line fresh** exam generated inside the grader at
scoring time, answers frozen from the original Python in **`re` mode** (no `regex`). The kit froze
twice (PYTHONHASHSEED 1 and 2) and dropped 0 of 100,000. Score = min(frozen share, fresh share).

The point of the fresh exam: it does not exist until grading, so even a program that embeds every
public answer cannot know it — the memorisation cheat collapses to its honest share (~0.05).

## 3. What surprised me
Two holes I found myself while closing Aman's, neither of which he tried:
- `net/http/cgi` pulls in `os/exec` **through the standard library**, so a program importing it would
  have passed my old gate while gaining an exec path. The deps-closure gate now catches it.
- A Go **assembly** file can make raw system calls with **no import at all**. The gate now fails on any
  assembly/C/cgo file in the module.
Both passed the old `go list ./...` check and fail the new one (`extra-cheat-tests/day5/gate_cgi.sh`,
`gate_asm.sh`).

## Honest limits
- The allowlist depends on Docker's egress control. If the engine can't enforce it, Harbor refuses the
  run rather than opening the network silently — so it fails loud, not silent.
- A half port still earns ~0.14. That is deliberate partial credit, not a miss.
- The fresh exam uses the same generator as the fixed one, so it stops **memorisation**, not a genuine
  rules port. That is the right line: a correct port still scores 1.0.

## Questions I expect
- Why `go list -deps -json` instead of `go list ./...`? Because `./...` never descends into a nested
  module, which is exactly where Cheat 2 hid `os/exec`. The deps closure sees the whole build.
- Why lock Python *and* add the fresh exam, isn't one enough? They cover different attacks — the lock
  stops running Python, the fresh exam stops memorising public answers. Neither closes the other.
- Why `nobody` with no PATH? So the program can't reach any interpreter even if a gate were ever beaten.
