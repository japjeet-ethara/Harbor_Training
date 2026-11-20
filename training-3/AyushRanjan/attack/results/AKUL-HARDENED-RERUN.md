# Akul hardened-task rerun evidence

Latest hardened task available locally: commit `2fbaa108203388562841f9d52faf7b45a39d8827`.

Akul's Slack message links directly to this task at commit `2fbaa108203388562841f9d52faf7b45a39d8827`; the Harbor scratch copies were extracted from that exact commit. The separate label `f5929f6` in the message does not match the linked commit SHA.

| Cheat | Score | Job ID | Trial ID |
|---|---:|---|---|
| Build-only | 0.0 | `efbc086c-42e8-4022-9e27-f9d55f8ccc3f` | `scratch-akul-2fbaa10-cheat1__QrDU92v` |
| Answer-file lookup | 0.0 | `6a311515-1c17-4ee2-8f2d-e6c945c84a04` | `scratch-akul-2fbaa10-cheat2__wUiRsRE` |
| Python wrapper | 0.0 | `ba467c0a-7870-4252-a4be-8eea88d19271` | `scratch-akul-2fbaa10-cheat3__x7GDnb8` |

The reward files are saved alongside this report. These are direct copies of Harbor's verifier reward outputs. All successful trials completed without exceptions. The initial build-only attempt failed only because the temporary Windows scratch copy's `tests/test.sh` had CRLF line endings; the successful retry used LF in that scratch file only.
