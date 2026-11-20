# DEFENCE — Ayush Parasher (5-minute talk notes)

## 1. Strongest cheat against my task
**Saurabh's cheat 1, "direct hidden-answer read"**: `main.go` just prints `/tests/data/hidden_expected.txt`.
- Before: **1.0** (Saurabh's job `2026-11-19__13-06-28`, my re-run `jobs/2026-11-20__05-22-23`).
- After: **0.0** (`jobs/2026-11-20__05-19-10`).
- Why it worked: the grader ran the agent's binary **as root in the verifier container**, next to the
  answers. Nothing was wrong with the data; the problem was who could read it.
- Fix: `test.sh` makes `/tests` root-only. `_grade.py` reads the exam into memory, then runs the binary
  as `nobody` (`setpriv --no-new-privs`) with an empty env in an empty temp dir. Cheats 2 and 3 (lookup
  map, recursive search incl. `/proc/1/root`) die for the same reason.
- I also closed a hole he did not use: the golang verifier image ships `python3`, so "Python inside a Go
  wrapper" (my cheat that got 1.0 on Sonu's task) would have worked. The verifier Dockerfile now deletes
  it, and that cheat scores 0.0 (`jobs/2026-11-20__05-21-36`).
- And: `build` + `no_python` used to pay 0.33 for an empty program. They are now multiplied by the
  behaviour score.

## 2. Exam before / after
Old: 2,000 hidden titles. New: 100,000 titles (`make_pool.py 100000 1` + my `EXTRA` word bank),
answers frozen twice, 0 dropped, **re mode (WITHOUT regex)**, written in `instruction.md`.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---|---|---|
| my oracle | 0 | n/a | n/a |
| Sonu Kumar | 4,963 | no (0/2,000 wrong) | 0% |
| Saurabh Baghel | 5,445 | no (0/2,000 wrong) | 0% |

Proof on the hardened task: oracle **1.0** (`jobs/2026-11-20__05-17-42`), nop **0.0**
(`jobs/2026-11-20__05-18-32`), every cheat **0.0**.

## 3. What surprised me
- Both classmates' ports were **perfect on my old exam** and wrong on about 5% of the new one. A random 2K
  sample of the new pool would catch them every time, so the old exam failed on *content*, not size:
  it never had `ß`, `_a/b/c`, `v1.2`, `ıstanbul` and similar words.
- The mode matters: 3,737 of the 100,000 titles differ between `re` and `regex`. My port matches `re`
  exactly. Saurabh's is closer to `regex`.
- My own practice-1 hand-in had the cheat committed as `solution/`. I fixed it on Day 4 before the attack
  (commit `53baf42`). I now verify from a clean `git` export, never from my Windows working copy
  (that copy has CRLF line endings, which break bash scripts and the data files).

## What did not work / honest notes
- Harbor's Windows launcher is blocked on my laptop, so every run is Harbor 0.25.0 inside Ubuntu WSL.
- My own port did **not** fail any of the 100,000 titles, so no port bug was found this time.
- Grading 100k lines builds and runs the port 3 times (once per check file, if rewardkit uses separate
  processes). It is still well under the timeout, and the reward is the same.

## Likely questions
- *Why `nobody` and not just delete the answers?* The grader needs them. Reading them into memory first and
  then dropping privileges for the untrusted binary keeps both.
- *Could the binary read rewardkit's memory?* No: `/proc/<pid>/mem` needs ptrace rights over a root
  process, and `nobody` has none (`--no-new-privs`).
- *Why multiply build/no_python by behaviour?* So "compile something and delete files" earns nothing.
  The guide says `no_python` should pay only if real answers are right.
