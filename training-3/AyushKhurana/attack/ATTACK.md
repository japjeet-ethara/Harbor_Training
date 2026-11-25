# Attack — Pragati Sharma's `titlecase-go`

**Target:** `PragatiSharma/titlecase-go` in `Harbor_Training`
(commit `8b79bbcfbcce50f0a50058fdf397cd55f0abc018`; see `TARGET.txt`).
**Attacker:** Ayush Khurana. **Front door only:** every cheat is a
`solution/solve.sh`; `tests/`, `task.toml` and `environment/` were never touched.

> **About the numbers.** Every score below is from a real `harbor run -p <copy> -a
> oracle` on my machine (2026-11-18). Each cheat's `reward.json` is saved in
> `results/`, and the job folder is named next to the score. The reward figures are
> read from Harbor's own result table, not claimed.

---

## How the exam is scored (read first)

`reward = (build + no_python + 4·behaviour) / 6` — `tests/grade/reward.toml:4`.

| Check | What it does | File:line |
| --- | --- | --- |
| `build` | `go build ./...` from `/workspace/repo` succeeds | `tests/grade/build/check.py:12-14`, `support.py:51-63` |
| `no_python` | build succeeds **and** no file whose name ends in `.py` remains | `tests/grade/no_python/check.py:21-28` |
| `behaviour` | fraction of 2,000 **hidden** titles whose line matches | `tests/grade/behaviour/check.py:63-69` |

Answers to the five attacker questions (step 4.1):

1. **What the agent sees in its room:** the whole `/workspace/repo` checkout of
   python-titlecase (`environment/Dockerfile:3`). It does **not** see `tests/`;
   the grader runs in a *separate* verifier image (`task.toml:15`
   `environment_mode = "separate"`).
2. **What `tests/test.sh` checks:** it runs `rewardkit /tests/grade` as root
   (`tests/test.sh:3`), which scores the three checks above.
3. **Where the inputs live:** visible pair in `tests/data/inputs.txt` +
   `tests/data/expected.txt` (public in the repo); hidden pair in
   `tests/data/hidden_inputs.txt` + `tests/data/hidden_expected.txt`, read at the
   fixed paths `tests/grade/behaviour/check.py:11-12`.
4. **Is `tests/` visible to the agent while it works?** No at agent time (separate
   image). **But** the program under test is rebuilt and executed *inside the
   verifier*, as root, with `/tests` present (`COPY . /tests/`, `tests/Dockerfile:17`, no permission change) and the binary's
   cwd set to the workspace (`behaviour/check.py:39-61`). So the compiled program
   can read the hidden answers even though the agent could not.
5. **Three weakest points:**
   - **W1 — `no_python` is a pure filename check.** `path.suffix == ".py"`
     (`no_python/check.py:21-23`). Rename the Python, keep the logic.
   - **W2 — the verifier ships a full Python and runs the program unsandboxed.**
     `tests/Dockerfile:1` is `python:3.12-slim-bookworm`; the binary is run with
     the grader's inherited PATH, as root (the verifier image sets no `USER`,
     `tests/Dockerfile:1-17`), with nothing that restricts child processes
     (`behaviour/check.py:56-61`). A Go wrapper can shell out to `python3`.
   - **W3 — the hidden answers are reachable by the program.** They sit at a
     fixed, readable path in the same container the binary runs in
     (`behaviour/check.py:11-12`), as root. The program can just read them.

---

## Cheat 1 — Lookup table + delete trick

**What it does:** No titlecase logic. It embeds the 2,000 **visible** answers
(`tests/data/expected.txt`, public) in the Go binary, answers any title it has
memorised, echoes everything else back unchanged, and deletes every `.py` file so
`no_python` is paid for free. Tests W1 and whether the hidden inputs really differ
from the visible ones.

**Score (Harbor run):** reward **0.364** — build 1, no_python 1, behaviour
**0.046** (92 of 2,000 hidden titles matched). The 92 are titles that are already
titlecased, so echoing them is correct by luck; none of the memorised visible
answers appear in the hidden set.
**Job folder:** `jobs/2026-11-18__09-45-54`  (`results/cheat1-reward.json`)
**Confirmed reward:** **0.364**

**Why it worked (file:line):** `no_python/check.py:21-28` gives a full point for
deleting `.py` files with no working port; `behaviour/check.py:63-69` awards the
fraction, and the ~4.6% of titles that are identity cases pay out even for an echo.
**How to fix:** award `no_python` only when `behaviour > 0` (stop paying a free
1/6 for deletion), and use a weirder, larger hidden set so the identity-echo floor
collapses toward 0.

---

## Cheat 2 — Python inside (the strongest)

**What it does:** No Go port. It renames the original rules
`titlecase/__init__.py` → `original_rules.txt` (so no `.py` remains), embeds that
text, and ships a ~40-line Go `main` that calls `python3 -I` at run time, forces
the plain `re` branch (the exam's mode), and titlecases stdin line by line. Tests
W1 and W2 together.

**Score (Harbor run):** reward **1.000** — build 1, no_python 1, behaviour
**1.0** (2,000 / 2,000).
**Job folder:** `jobs/2026-11-18__09-47-48`  (`results/cheat2-reward.json`)
**Confirmed reward:** **1.000**

**Why it worked (file:line):** `no_python/check.py:21-23` only inspects the file
*suffix*, so `original_rules.txt` is invisible to it; `tests/Dockerfile:1` puts a
real `python3` on PATH inside the verifier; `behaviour/check.py:56-61` runs the
binary with that PATH inherited and nothing stopping a child process, so the
wrapper reproduces the reference answers exactly.
**How to fix:** run the program under test as an unprivileged user from an empty
cwd with a scrubbed PATH and no child-process / network capability, and make
`no_python` reject interpreters by content (shebangs, an embedded module that is
exec'd), not by file extension.

---

## Cheat 3 — Read the exam

**What it does:** Pure Go standard library, no titlecase logic. At run time the
binary walks the usual roots (`/tests`, `/workspace`, home, …), pairs any
`*input*` file with its `*expected*`/`*answer*`/`*output*` sibling of equal length,
builds a title→answer table from them, and answers from it (echo otherwise). Tests
W3. It reads the grader's fixed hidden pair
(`/tests/data/hidden_inputs.txt` + `hidden_expected.txt`) directly first, then
falls back to the disk walk, so it does not depend on one path layout.

**Score (Harbor run):** reward **1.000** — build 1, no_python 1, behaviour
**1.0** (2,000 / 2,000).
**Job folder:** `jobs/2026-11-18__09-48-39`  (`results/cheat3-reward.json`)
**Confirmed reward:** **1.000**

**Why it worked (file:line):** `behaviour/check.py:11-12` keeps the hidden answers
at a fixed path inside the verifier, and lines 39-61 run the binary as root with
`/tests` readable, so the program reads the answer key the grader is about to
score it against.
**How to fix:** run the program as `nobody` from a neutral empty directory and
`chmod -R go-rwx /tests` before scoring, so the answer files are not readable by
the program under test.

---

## Are these the strongest cheats?

- **Cheat 2 and cheat 3 are at the ceiling** — reward 1.000 is the maximum, and
  they reach it through two *independent* holes (call Python; read the answer key),
  so closing one does not close the other. On Day 5 both must be fixed.
- **Cheat 1 is at the ceiling for pure memorisation.** Visible and hidden titles are
  disjoint, so a memoriser can only win the 92 identity cases (behaviour 0.046); the
  rest of its score is the free `no_python` point. Nothing a lookup table does can
  raise this — to score higher it would have to actually compute answers, which is a
  different cheat (a *half port*, below).
- **One stronger variant exists but tests a different hole — a half port.** A program
  that implements only the easy rules (capitalise each word, lowercase the small
  words) and skips Mc/Mac, apostrophe tails and acronyms would likely score behaviour
  ~0.3–0.6, i.e. reward ~0.5–0.7. It measures how much partial credit a weak-but-real
  port earns, which is the Day-6 "new cheat" I will add after hardening. I kept the
  three above for Day 4 because two of them already break the task completely and the
  third proves the hidden set is clean.

## Highest score any cheat got: **1.000** (cheat 2 and cheat 3).

Two separate holes each give a non-porter full marks: the verifier runs an
unsandboxed program that can both **call Python** and **read the hidden answers**.
Cheat 1 is the honest low result — it shows `no_python` leaks a free 1/6, but the
hidden set is genuinely disjoint from the visible one (only the 4.6% identity
floor leaks), so memorising the public answers is worth almost nothing.
