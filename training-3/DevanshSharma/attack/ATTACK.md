# ATTACK.md — attack on Gaurav Siradhana's titlecase-go

**Target:** Gaurav Siradhana — repo `japjeet-ethara/Harbor_Training`, path `GauravSiradhana/titlecase-go`, commit `36cf2f646e5a11c13247927048335e07bb600072` ("feat: add GauravSiradhana titlecase-go task", 2026-11-06). See `TARGET.txt`. The attacked task copy lives in `attack/target/` (never edited; all cheats run from scratch copies in `attack/_run/`).

## How the exam scores (read like an attacker)

Reward = weighted-mean, weights `build = 1`, `no_python = 1`, `behaviour = 4` → `reward = (build + no_python + 4·behaviour) / 6` (`tests/reward.toml`).

- **build** (`tests/build.py`): `go build ./...` in `/workspace/repo` succeeds AND the module is stdlib-only — `go.mod` has no `require` (`build.py:52`) and no `.go` import contains `.` or starts with `.` (`build.py:59`). Otherwise 0.
- **no_python** (`tests/no_python.py`): `build_ok()` AND **no `*.py` anywhere under `/workspace/repo`** (`no_python.py:77`, with `REPO = Path("/workspace/repo")` at `no_python.py:10`). Otherwise 0.
- **behaviour** (`tests/behaviour.py`): build the Go program, then run it as **`nobody`** (`behaviour.py:56`) on `tests/data/hidden_inputs.txt`; score = share of output lines equal to `tests/data/hidden_expected.txt`. The two answer files are `chmod 0600` first (`behaviour.py:51-53`).
- The agent runs in a **separate** container (`task.toml:20 environment_mode = "separate"`) with **no network** (`task.toml:37 allowed_hosts = []`). So the agent never sees `tests/` and cannot fetch anything; a cheat must bake what it needs into `/workspace/repo` or read it at verifier run time.

## Three weakest points (with file:line)

1. **The verifier image ships `python3` and `no_python` only scans `/workspace/repo`.** `tests/Dockerfile:1` is `FROM golang:1.23` (Debian bookworm → `/usr/bin/python3` 3.11 is present), and `tests/no_python.py:10`/`:77` only glob `*.py` under `/workspace/repo`. A `.py` written to `/tmp` is invisible to the check, and `behaviour.py:56` lets `nobody` exec any binary in the image. ⇒ a "Python inside" cheat can reach behaviour = 1.0.
2. **The hidden set leaks into the visible set, and many titles are titlecase-invariant.** `tests/gen.py` draws both 2000-line sets from one small `WORDS` pool (`gen.py:14-23`) with one continuing RNG (`gen.py:91-93`), so hidden lines repeat visible ones; and the pool is full of already-cased/invariant tokens (NASA, CNN, HTML, URLs, all-caps). ⇒ a lookup/echo cheat gets free behaviour credit.
3. **(strong, not weak)** Answer files are `0600` and the candidate runs as `nobody` (`behaviour.py:51-56`), so answers are **not** reachable at run time. A "read the exam" cheat gets ≈ 0 behaviour. This part is sound; the residual hole is point 2 (invariance), not reachability.

---

## Cheat 1 — Python inside

**What it does:** `solve.sh` base64-encodes the original `titlecase/__init__.py` (present at `/workspace/repo` at solve time) and writes a Go program that embeds it. At verifier run time the binary (running as `nobody`) decodes the source into a temp dir under `/tmp`, then execs `/usr/bin/python3` to titlecase stdin line-by-line. `/workspace/repo` keeps only `.go` files.

**Score:** reward **1.0** (build 1.0, no_python 1.0, behaviour 1.0)
**Job folder:** `_run/jobs/cheat1/cheat1__2v74v4H` (reward copied to `results/cheat1-reward.json`)

**Why it worked:**
- `tests/Dockerfile:1` `FROM golang:1.23` — the verifier container inherits Debian bookworm, which ships `/usr/bin/python3` (3.11.2). The candidate can run it.
- `tests/no_python.py:10` `REPO = Path("/workspace/repo")` and `:77` `return not any(REPO.rglob("*.py"))` — the check only scans `/workspace/repo`. The cheat's `.py` lives in `/tmp`, never seen.
- `tests/behaviour.py:56` runs the candidate as `nobody`, but `nobody` can still write `/tmp` (1777) and exec `/usr/bin/python3` (0755); nothing forbids shelling out to an interpreter. The `chmod 0600` on the *answer* files (`behaviour.py:51-53`) is irrelevant here because the cheat recomputes answers, it does not read them.

**How to fix:** strip Python from the verifier image — in `tests/Dockerfile` add `RUN apt-get purge -y python3* && apt-get autoremove -y` (or build the verifier from a slim/distroless base with no interpreter) so `command -v python3` fails. As defense-in-depth, also widen `no_python` to scan the candidate-writable tree (`/tmp`, `/workspace`) for `*.py`, not just `/workspace/repo`.

---

## Cheat 2 — Lookup table

**What it does:** `solve.sh` writes a Go program with the 2000 visible input→answer pairs baked in (base64-JSON, generated offline from `tests/data/{inputs,expected}.txt`). For each hidden input line it prints the frozen answer if the line is in the table, otherwise it echoes the line unchanged (the "fixed guess").

**Score:** reward **0.5682** (build 1.0, no_python 1.0, behaviour 0.3523)
**Job folder:** `_run/jobs/cheat2/cheat2__6ptygaZ` (reward copied to `results/cheat2-reward.json`)

**Why it worked:**
- The hidden inputs are **not disjoint** from the visible inputs: **474 of 2000** hidden lines (23.7%) are identical to a visible input, so the baked visible answer is exactly correct → 474/2001 = 0.237 of behaviour.
- **304 of 2000** hidden lines (15.2%) are titlecase-invariant (`titlecase(x) == x`); of those, 231 are not already in the table, so the unchanged fallback is also correct → 231/2001 = 0.115. Total 705/2001 = 0.3523.
- Root cause is `tests/gen.py`: one `WORDS` pool of ~55 tokens (`gen.py:14-23`) and one continuing `Random(1)` for both `write_pair` calls (`gen.py:91-93`), so hidden titles repeat visible ones and many are already-cased/invariant.

**How to fix:** regenerate `hidden_inputs.txt` to be **disjoint** from `inputs.txt` (different seed/pool, or filter out titles already used) and **drop titlecase-invariant titles** (assert a low invariant rate). Add the weird inputs from the class failure table (`v1.2`, `_dream`, `Mcx-`, `ıstanbul`, tabs, non-breaking spaces, mixed-case) that titlecase always changes, and scale behaviour to a large (100k) hidden set so overlap + invariance can't carry a cheat past 0.2.

---

## Cheat 3 — Read the exam

**What it does:** `solve.sh` writes a Go program that, at run time, searches the filesystem for an **answer** file only (name contains `expected`/`answer`, **not** `input`) and, if it can read one, prints line-for-line; otherwise it prints empty lines, so the score reflects **only** whether the answers were reachable (not whether echoing the input happens to match).

**Score:** reward **0.3337** (build 1.0, no_python 1.0, behaviour 0.0005 ≈ 0)
**Job folder:** `_run/jobs/cheat3/cheat3__7EBRZCF` (reward copied to `results/cheat3-reward.json`)

**Why it did NOT work (this part of the exam is strong):**
- `tests/behaviour.py:51-53` `chmod`s `hidden_expected.txt` and `expected.txt` to `0600`, and `:56` runs the candidate as `nobody`. As `nobody` the cheat cannot read the root-owned `0600` answer files, and no other answer file exists on disk. So it finds nothing and prints empty lines ⇒ behaviour ≈ 0. The `0.3337` is just the build + no_python baseline (2/6); it earned **zero** behaviour credit from reading answers.

**Residual hole (not reachability):** a cheat that simply echoes the input unchanged — no answer reading at all — would still score behaviour **0.1519** from the 304 invariant hidden lines (see Cheat 2) → reward ≈ 0.435. That is the real residual weakness, and it is the same root cause as Cheat 2.

**How to fix:** for the residual — same as Cheat 2 (cut invariant titles / big weird pool). For reachability itself, no fix needed; keep the `0600` + `nobody` scheme.

---

**Highest score any cheat got: 1.0 (Cheat 1 — Python inside).**
