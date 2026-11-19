# HARDEN — Madhur Jain's titlecase-go task

Attacker: Mukul Bhardwaj (Harbor_Training/training-3/MukulBhardwaj/attack/ATTACK.md). Every number below comes from a Harbor run; the job folder is next to it.

## Holes closed
Cheat 1 (FILL his name for it): was FILL (jobs/mukul-cheat1-before), now FILL (jobs/mukul-cheat1-after)   fix: FILL
Cheat 2 (FILL his name for it): was FILL (jobs/mukul-cheat2-before), now FILL (jobs/mukul-cheat2-after)   fix: FILL
Cheat 3 (FILL his name for it): was FILL (jobs/mukul-cheat3-before), now FILL (jobs/mukul-cheat3-after)   fix: FILL

What changed in task/:
- tests/checks/behaviour.py and no_python.py build the port with CGO_ENABLED=0 and run it alone in an empty chroot as user nobody. There is no Python, no /tests and no /solution inside, which closes "read the exam" and "Python inside".
- tests/checks/no_python.py pays only when the program itself earns behaviour (above 90% right), so deleting .py files is worth nothing on its own.
- tests/checks/behaviour.py scores the share right on 100,000 titles: nothing below 90%, then linear to 1.0. An echo program or a half port earns 0.
- tests/checks/build.py now checks the standard-library rule: no require lines in go.mod, no vendor/ folder.
- tests/data: 100,000 titles from the kit (count 100000, seed 1), answers frozen twice, mode re. The old 2,000-title files are gone.
- instruction.md states the mode (titlecase WITHOUT regex, Python 3.14), the jail and the scoring.
- Removed leftovers: tools/ (old generator), cheat/ (old practice cheat), screenshots/ (old numbers) and environment/python-titlecase/titlecase-go (an empty task skeleton).
- solution/go/titlecase.go: a one-line fix in capFirst, found by the new exam (below).

## Exam: before and after
Old exam: 2,000 hidden inputs   New exam: 100,000 inputs, mode: re (titlecase WITHOUT regex)

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---|---|---|
| my oracle, before the fix | FILL | no | FILL |
| my oracle, after the fix | 0 | n/a | n/a |
| Satvik Tandon | FILL | yes | FILL |
| Mukul Bhardwaj | FILL | no | FILL |

From kit/compare.py: measure/my-oracle-before-fix.txt, measure/my-oracle.txt, measure/satvik-tandon.txt, measure/mukul-bhardwaj.txt.

## What I learned (3 lines)
1. Weird beats many: my old 2,000 titles never had a word starting with "_", so a bug on 8,752 of 100,000 weird titles was invisible and my oracle scored 1.0.
2. Partial credit needs a floor: a port that was only 26% right scored 0.51 on my old grader.
3. Hiding the tests from the agent is not enough: the program is graded later, so it must run where it cannot reach Python or the answers.
EOF
