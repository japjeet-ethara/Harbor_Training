# Attack Report — Prashant Kumar

Target: Prashant Kumar fe970011a7693e9344be4e3e2b03bea40494a475

## Cheat 1 — Read hidden answers from disk
What it does:   At runtime, cats /tests/data/hidden_expected.txt directly as output instead of running the Go binary.
Score:          reward 1.000 (build 1.0, no_python 1.0, behaviour 1.0)
Job folder:     jobs/2026-11-18__16-37-53
Why it worked:  tests/behaviour/check.py line 7 defines EXPECTED = Path("/tests/data/hidden_expected.txt"). The file is readable by the agent at runtime because tests/ is mounted into the container with no access restrictions.
How to fix:     Move hidden answer files outside the agent-visible container, or compare output against answers computed at check time rather than stored in a readable file.

## Cheat 2 — Build trick and delete Python files
What it does:   Writes a minimal Go echo program into /workspace/repo, deletes all .py files, and builds. Produces no correct titlecase output.
Score:          reward 0.394 (build 1.0, no_python 1.0, behaviour 0.091)
Job folder:     jobs/2026-11-18__16-45-49
Why it worked:  tests/no_python/check.py line 7-16 gives full no_python credit just for go build passing and no .py files present, with no check that answers are correct. tests/build/check.py line 7 only checks return code == 0.
How to fix:     Gate no_python credit on behaviour also being above a minimum threshold, so deleting .py files alone gives no reward.

## Cheat 3 — Half port
What it does:   Implements only simple titlecase (capitalize first letter, lowercase small words) with no edge case handling — no Unicode, no punctuation, no McX, no apostrophes.
Score:          reward 0.338 (build 1.0, no_python 1.0, behaviour 0.006)
Job folder:     jobs/2026-11-18__16-48-07
Why it worked:  tests/behaviour/check.py line 10-17 gives partial credit proportional to correct answers, so even a weak port earns build and no_python points freely.
How to fix:     Require a minimum behaviour score (e.g. 0.5) before build and no_python contribute to reward, so a half port cannot score above 0.2 overall.

## Highest score achieved
Cheat 1: reward 1.000