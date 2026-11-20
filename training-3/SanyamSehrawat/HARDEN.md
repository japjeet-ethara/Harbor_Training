# Day 5 — Harden Sanyam Sehrawat's Titlecase Task

## Attacker and target

- Attacker: Sonu Kumar
- Original target commit: `9c8b84d4d7da90ea8feceb9f5e9a39720a672b53`
- Sonu's strongest cheat: Python Inside, reward `0.9897`
- Job folder: `Harbor_Day4_Workspace/Sonu Kumar/jobs/2026-11-18__23-51-32`

## Changes

1. Replaced the Python verifier with a compiled-Go verifier. The verifier image and agent
   image no longer install Python or the `regex` package.
2. Added a forbidden-import check for `os/exec`, `syscall`, `plugin`, `unsafe`, `C`, `net`,
   and `net/*`. This rejects subprocess and network-wrapper solutions during build.
3. Made `no_python` conditional on both no remaining `.py` files and behaviour of at least
   `0.5`. A delete trick or half port can no longer receive independent free credit.
4. Behaviour now runs the submitted binary once as uid/gid `65534` from `/tmp`, with `/tests`
   restricted to root. The hidden answer sheet is therefore unreachable at runtime.
5. Replaced the 2,000-line graded set with a frozen 100,000-line set generated from pool seed
   `1`. The freeze report kept all 100,000 answers; 0 were dropped.
6. Stated in `instruction.md` that answers use titlecase WITH the optional `regex` package.

## Holes closed

| Sonu cheat | Before | Fix |
|---|---:|---|
| Delete trick | 0.3333 | Build is still 1, but behaviour and gated `no_python` are 0, giving at most 0.1667 reward. |
| Half port | 0.4697 | Behaviour is capped below the 95% threshold and `no_python` remains 0. |
| Python Inside | 0.9897 | Forbidden `os/exec` build check and removal of Python reject the wrapper. |

These are hardening properties based on the verifier logic; they still require real Harbor
re-runs before they can be claimed as measured Day 6 proofs.

## 100K exam measurement

The kit was run with `python -I`. `report.txt` records `kept (stable) 100000`, `dropped
(unstable) 0`, and `regex module used True`.

| Port | Wrong on 100K | Old 2K missed it? | Chance 2K misses all wrong lines |
|---|---:|---|---:|
| Sanyam oracle | 21,649 | n/a | 0% |
| Alok Kumar Jaiswal oracle | 99,999 | no | 0% |
| Lokesh Deshwal port | 16 | no | 72% |

The Sanyam oracle failed the new 100K exam, so it needs a real algorithm fix before Day 6.
The result is not addressed by deleting inputs or weakening the grader.
