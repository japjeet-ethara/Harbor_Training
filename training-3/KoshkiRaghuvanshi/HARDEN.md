# HARDEN.md - Koshki Raghuwanshi

Attacker: Tanya Shrivastava. Baseline: oracle 1.0 in jobs/2026-11-20__16-45-12.

## Holes closed
Cheat 1 (Python inside): was 1.0, now 0.0 (jobs/2026-11-20__17-24-53)
  fix: no_python.py rejects any file whose name contains ".py" (so .py.txt is caught); the verifier image deletes /usr/bin/python*; go_run.py hides /usr/local/bin from the submitted program.
Cheat 2 (Half port): was 0.2696, now 0.0 (jobs/2026-11-20__17-27-26)
  fix: behaviour is all-or-nothing, an exact byte match on 100,000 titles; reward.toml is all-pass, so partial credit is gone.
Cheat 3 (Build trick + delete trick): was 0.1667, now 0.0 (jobs/2026-11-20__17-29-49)
  fix: all-pass means build and no_python give no points on their own.

## Extra tests I added
Cheat 4 (Tanya's cheat 1 calling /opt/rewardkit/bin/python3): 0.0 (jobs/2026-11-20__17-33-50). This was stopped by the filename check, not by hiding the interpreter, so it does not test the interpreter on its own.
Cheat 4b (same, but the Python source is stored as .dat so no filename contains .py): 0.0 (jobs/2026-11-20__17-43-17). This tests whether the leftover Python in /opt/rewardkit is reachable. Result: the submitted program cannot reach it, so no extra fix was needed.

Also fixed: instruction.md now says a single final newline is a terminator, not an extra empty line (Tanya's "other weak point").

## Exam: before and after
Old exam: 2,000 inputs.   New exam: 100,000 inputs, mode: re (titlecase WITHOUT regex), answers frozen twice, 0 dropped (kit/report.txt).

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|------|-------------------|---------------------|----------------------------|
| my oracle | 0 | n/a | n/a |
| Aahan Trikha | 3900 | no | 0% |
| Tanya Shrivastava | 3053 | no | 0% |

Note: an earlier measurement of my own oracle (before I fixed it) showed 488 wrong. The 100,000-title exam found those bugs, I fixed the port, and the current port is measured above.

## What I learned
1. My old 2,000-title exam gave a perfect score to two classmate ports that are wrong on 3,900 and 3,053 of 100,000 titles, so its inputs were too ordinary; what is in the inputs matters more than how many there are.
2. Partial credit and free points (build, no_python) let a half-port or an empty program score above zero; all-or-nothing closes that.
3. The answer mode (with or without regex) must be written in instruction.md, otherwise a correct port can fail.

The old 2,000-input exam is kept in measure/old-exam/ so the "old exam caught it?" column can be re-run: python kit/old_exam.py measure/old-exam/hidden_expected.txt <port output for measure/old-exam/hidden_inputs.txt>

Made the task self-contained: the original Python source now lives in task/environment/python-titlecase-src/ and docker-compose.yaml points to ./python-titlecase-src. The old path ../../python-titlecase does not exist in the repo layout, so the task could not build from the repo.
