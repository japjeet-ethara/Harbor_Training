# HARDEN.md — Day 5

Task: `training-3/YugalLohani/task` (my practice-1 titlecase-go port).
Attacker report hardened against: `training-3/AkulMalviya/attack/ATTACK.md`.
Harbor 0.26.0, Docker 28.3.0, local Docker machine, 2026-11-20. Every "after"
number is from a real Harbor run; its job folder is given in parentheses.

## Holes closed

Akul's three cheats were all half-ports (he left the `.py` files in place), and
his report also raised three findings. I closed every cheat and every finding,
and self-attacked with three more cheats (lookup, python-inside, read-the-exam)
to be sure.

| Cheat / finding | Before | After | Job folder (after) |
|---|---|---|---|
| Akul cheat1 — capitalize word starts | 0.339 | **0.1805** | `jobs/2026-11-20__12-48-27` |
| Akul cheat2 — normalize word casing | 0.3557 | **0.1469** | `jobs/2026-11-20__12-49-11` |
| Akul cheat3 — small-word list | 0.355 | **0.1584** | `jobs/2026-11-20__12-49-55` |
| finding #1 — read the hidden answers at run time | **1.000** | **0.1547** | `jobs/2026-11-20__12-47-25` |
| my probe — python-inside (run the original via python3) | 0.988 | **0.1540** | `jobs/2026-11-20__12-52-22` |
| my probe — half-port | 0.638 | **0.1547** | `jobs/2026-11-20__12-51-33` |
| my probe — lookup / echo | 0.179 | **0.1547** | `jobs/2026-11-20__12-50-44` |

Fixes (in `task/`, all addressing Akul's report):

1. **Finding #1 — no execution isolation (the worst hole).** The grader ran the
   candidate as root in a temp dir, so a Go program could `os.ReadFile(
   "/tests/data/hidden_expected.txt")` and print the answer sheet — a real 1.0.
   Fix: the candidate now runs as an unprivileged user `runner` (created in
   `tests/Dockerfile`) that cannot read `/tests`, and the hidden files are mode
   `0600 root`. `tests/lib/grading.py` drops privileges with `subprocess.run(
   user=..., group=...)` and fails closed if it cannot. Read-exam: 1.0 → 0.155.
2. **Python-inside.** The verifier image shipped `python3`, so a Go wrapper could
   shell out to the original. Fix: `tests/Dockerfile` removes every system
   interpreter (Reward Kit keeps uv's managed Python), and the candidate runs
   with `PATH=/usr/local/go/bin:/usr/bin:/bin`. python-inside: 0.988 → 0.154.
3. **Finding #2 — loose stdout contract.** Behaviour only counted matching
   positions. Fix: `grading.py` now requires exact record count and a final
   newline before scoring, so truncated/over-long output scores 0.
4. **Finding #3 — weak `no_python`.** It paid for one correct changed line. Fix:
   `no_python` now needs the build to pass, no `.py`, **and** behaviour ≥ 0.99,
   so deleting files or a partial port earns nothing there.
5. **Weak exam.** See below.
6. **Reward weight.** behaviour weight 4 → 6 (`(build + no_python + 6·behaviour)/8`)
   so a program that only builds and deletes `.py` cannot drift toward the pass
   mark. A non-solving cheat now needs > 10% correct to reach 0.2.

Controls on the hardened task: oracle **1.0** (`jobs/2026-11-20__12-45-54`),
nop **0.0** (`jobs/2026-11-20__12-46-52`).

## Exam: before and after

Old exam: 2,000 inputs. New exam: **100,000 inputs**, mode: **regex** (CPython
3.12, Unicode 15.0.0, `regex` 2024.11.6 — `REGEX_AVAILABLE` True), stated in
`instruction.md`. Built with the kit (`kit/make_pool.py` enriched with rule-
breaking word families per guide section 5.3; answers frozen twice by
`kit/answers.py`, 0 dropped — see `kit/report.txt`).

| Port | Wrong on new 100k | Wrong on old 2k | Old exam caught it? | Chance a 2K random exam misses all |
|---|---|---|---|---|
| my oracle | 0 | 0 | n/a (correct) | n/a |
| Charitra's port (`re` mode) | 10,902 | 36 | yes, but only 1.8% | 0% |
| Akul's port | 17,475 | 176 | yes, 8.8% | 0% |

(Full `compare.py` output in `measure/`.) The classmates' ports are wrong even
on the old exam, largely because they target the `re` fallback mode while my
exam is `regex` mode — the brief's Lesson 3. The new exam catches their errors
at 6× and 2× the old rate, with certainty.

## What I learned (3 lines)

- The dangerous cheat was not a half-port but infrastructure: a root candidate
  reading the answer file, and an interpreter left in the grading image.
- A bigger exam is not enough; it has to be *weird* — enriching the pool with
  rule-breaking inputs dropped a naive port from 46% correct to under 4%.
- Stating the exact mode (`regex` vs `re`) matters: a correct-looking port in the
  wrong mode fails thousands of lines.
