# Akul hardened-task rerun evidence

Latest hardened task available locally: commit `2fbaa108203388562841f9d52faf7b45a39d8827`.

Akul's Slack message links directly to this task at commit `2fbaa108203388562841f9d52faf7b45a39d8827`; the Harbor scratch copies were extracted from that exact commit. The separate label `f5929f6` in the message does not match the linked commit SHA.

| Cheat | Score | Job ID | Trial ID |
|---|---:|---|---|
| Build-only | 0.0 | `efbc086c-42e8-4022-9e27-f9d55f8ccc3f` | `scratch-akul-2fbaa10-cheat1__QrDU92v` |
| Answer-file lookup | 0.0 | `6a311515-1c17-4ee2-8f2d-e6c945c84a04` | `scratch-akul-2fbaa10-cheat2__wUiRsRE` |
| Python wrapper | 0.0 | `ba467c0a-7870-4252-a4be-8eea88d19271` | `scratch-akul-2fbaa10-cheat3__x7GDnb8` |

The reward files are saved alongside this report. These are direct copies of Harbor's verifier reward outputs. All successful trials completed without exceptions. The initial build-only attempt failed only because the temporary Windows scratch copy's `tests/test.sh` had CRLF line endings; the successful retry used LF in that scratch file only.

## Two additional probes

These extra probes target the scoring behavior, not the answer-file isolation or Python runtime boundary. Both used the same linked Akul task revision above.

| Probe | Shortcut | Score | Evidence from grader | Harbor job ID | Trial ID | Reward file |
|---|---|---:|---|---|---|---|
| Cheat 4 | Basic whitespace-token title casing with a small-word list; omits most edge rules and collapses whitespace | 0.06136 | 6,136 / 100,000 lines matched | `1ed4629d-ca27-44e9-b8b4-4e6aca8c0a34` | `scratch-akul-2fbaa10-cheat4__big4B8M` | `day6-akul-cheat4-reward.txt` |
| Cheat 5 | Reuses Ayush's original practice-1 Go port, which is an incomplete solution for Akul's expanded exam | 0.82558 | 82,558 / 100,000 lines matched; 17,442 wrong | `635c97f8-d57b-4f3c-9559-196f43cef4e5` | `scratch-akul-2fbaa10-cheat5__SvpbY7s` | `day6-akul-cheat5-reward.txt` |

### Finding

The verifier enforces exact output count and final newline (lines 67-71), but then gives proportional behavior reward for each matching line (`task/tests/test.sh:74-81`). The deliberately basic cheat received only 0.06136, but the known incomplete practice port received 0.82558 while producing 17,442 wrong answers. This is a scoring weakness if the goal is to ensure an incomplete solution stays below 0.2. To close it, make behavior reward binary for full exact output, or explicitly cap partial behavior credit below the required cheat threshold. No files in Akul's folder were changed.
