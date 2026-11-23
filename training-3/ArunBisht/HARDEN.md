# HARDEN.md - Arun Bisht

Date: 2026-11-21
Target: Arun Bisht, commit `c020318f325e9b4220a87ce63e8419f505139523`
Task: `training-3/ArunBisht/task`
Scope of this pass: only this report was rewritten. No task files, configs, data, jobs, or git history were changed.

## 1. Attack summary

Only Priya Kumari's attack report was considered for this task (`training-3/Priya Kumari/attack/ATTACK.md`). The port measurements below are separate comparisons, not attacker submissions.

| Case | Priya reported | Baseline replay | Hardened replay | Result |
|---|---:|---:|---:|---|
| Cheat 1 | 0.3977 | 0.3953 | 0.0000 | Blocked |
| Cheat 2 | 0.4347 | 0.4297 | 0.0000 | Blocked |
| Cheat 3 | 0.5177 | 0.5201 | 0.0000 | Blocked |
| Nop | - | - | 0.0000 | Expected |
| Oracle | - | - | 1.0000 | Expected |

Baseline behaviour components were `0.093` (raw `0.09300`), `0.1445` (raw `0.14453`), and `0.2802` (raw `0.28016`). In every case `build = 1.0` and `no_python = 1.0`; the old reward came entirely from behaviour. The gate below turns those into zero total reward.

## 2. Defences that close the attacks

| Defence | Where | Effect |
|---|---|---|
| Behaviour gate at 0.8 | `tests/score_utils.py`, `tests/build.py`, `tests/no_python.py` | Full credit is given only when deterministic behaviour score is at least 0.8. Below that, `build`, `no_python`, and `behaviour` all score 0, so partial cheat scores cannot leak into reward. |
| Reward weights | `tests/reward.toml` | `build = 1.0`, `no_python = 1.0`, `behaviour = 4.0`. A correct solution earns 1.0 overall; a gated failure earns 0.0 overall. |
| 100K deterministic exam | `kit/`, `key/`, `tests/data/` | Inputs are seeded-random and frozen; key and task copies are byte-identical by SHA-256. Old 2K tables and public-only shortcuts fail on the larger set. |
| Separate hidden input/expected files | `tests/data/hidden_inputs.txt`, `tests/data/hidden_expected.txt` | Hidden cases are not the same files as the public inputs/answers. Reading or caching only the public data cannot pass. |
| Generator mode recorded as `WITHOUT regex` | `kit/report.txt` | The report records `regex module used  False`; the generator used the standard-library `re`, not the third-party `regex` package. This is the current on-disk truth. |
| Worker isolation | `rewardkit/sandbox.py` | The submission runs under a fresh unprivileged UID with `NoNewPrivs=1`, no capabilities, and private paths `/tests` and `/logs/verifier` inaccessible. |
| `.py` file rejection | `tests/no_python.py` | Any `.py` file anywhere under the shared stage fails the `no_python` criterion. This closes Python-helper layouts that leave a helper file behind. |

Attack-to-defence mapping:

| Attack | Why it worked before | Why it fails now |
|---|---|---|
| Cheat 1 | Partial output reuse earned partial behaviour credit. | Behaviour below 0.8 triggers the global gate; total reward is 0.0. |
| Cheat 2 | Regex-heavy or cached shortcuts could score on a smaller public set. | 100K public plus hidden cases, `WITHOUT regex` generator truth, and the 0.8 gate remove partial credit. |
| Cheat 3 | A Python helper could produce answers while the Go program looked valid. | Hidden golden data, the behaviour gate, and `.py` rejection block the submitted form. The interpreter itself is still present; see residual risks. |

## 3. Exam evidence

All files below have exactly `100000` lines. Key and task copies match by SHA-256.

| File | SHA-256 | Bytes | Lines |
|---|---|---:|---:|
| `key/inputs.txt` | `C8E41793D8CAFBCA5C6108C06E475DAB681CE6748FD48E8AC59E219A760F4B82` | 4433328 | 100000 |
| `tests/data/inputs.txt` | `C8E41793D8CAFBCA5C6108C06E475DAB681CE6748FD48E8AC59E219A760F4B82` | 4433328 | 100000 |
| `key/answers.txt` | `B5114890D71ABD7C792FA362BE048CD74F21D9E3EA9A98D0B7C8E3C555D55438` | 4433328 | 100000 |
| `tests/data/expected.txt` | `B5114890D71ABD7C792FA362BE048CD74F21D9E3EA9A98D0B7C8E3C555D55438` | 4433328 | 100000 |
| `key/hidden_inputs.txt` | `72D62EB205BC0C468A51ECF91C83010F50526943C7E26C5A2530EA8C3A1834A3` | 4441767 | 100000 |
| `tests/data/hidden_inputs.txt` | `72D62EB205BC0C468A51ECF91C83010F50526943C7E26C5A2530EA8C3A1834A3` | 4441767 | 100000 |
| `key/hidden_answers.txt` | `3FDC9C931A802072824A0BB80B8415C39368B89BB52C78F70F52755C54410DBD` | 4441767 | 100000 |
| `tests/data/hidden_expected.txt` | `3FDC9C931A802072824A0BB80B8415C39368B89BB52C78F70F52755C54410DBD` | 4441767 | 100000 |

`kit/report.txt` hash: `F66D3F0EC7E6C0D32115562162841A0F44513BB1B36372AB9196898015EC7CA7`. Contents:

```text
pool inputs 100000
kept (stable) 100000
dropped (unstable) 0
regex module used  False
```

## 4. Harbor verification evidence

The following rewards are from existing jobs. Versions used: Harbor `0.25.0`, Docker server `29.9.3`, `harbor-rewardkit==0.2.4`.

| Job | Reward | components |
|---|---:|---|
| `hardened-oracle/task__ohtjHNY` | 1.0000 | `build 1.0`, `no_python 1.0`, `behaviour 1.0` |
| `hardened-nop/task__AJzChfR` | 0.0000 | all 0.0 |
| `hardened-cheat1/hardened-cheat1__ZQpLFEM` | 0.0000 | all 0.0 |
| `hardened-cheat2/hardened-cheat2__V5YWQCj` | 0.0000 | all 0.0 |
| `hardened-cheat3/hardened-cheat3__kvnExPR` | 0.0000 | all 0.0 |

Path prefix for these five jobs: `C:\Users\ARUNBI~1\AppData\Local\Temp\opencode\day5-work\jobs-hardened\`.

Additional local oracle proof in the repo: `jobs/2026-11-20__14-40-32/test-oracle__G7aeGo3/verifier/reward.json` is `1.0`; that job config pointed at the `scratch/test-oracle` copy.

Baseline replay path prefix: `C:\Users\ARUNBI~1\AppData\Local\Temp\opencode\day5-work\jobs\day5-baseline-*`.

A `--print-config --yes` dry run completed without a Harbor config error. No new Harbor run was created during this write-only pass.

## 5. Port comparison on the 100K exam

| Port | Wrong answers | Chance vs oracle |
|---|---:|---:|
| `my-oracle` | 0 / 100000 | 100% |
| `neha-gaur` | 16 / 100000 | 72% |
| `alok-kumar-jaiswal` | 9219 / 100000 | 0% |

Evidence: `training-3/ArunBisht/measure/my-oracle.txt`, `measure/neha-gaur.txt`, and `measure/alok-kumar-jaiswal.txt`.

## 6. Residual risks and next checks

- The current working-tree `tests/test.sh` has a CRLF shebang: first bytes are `23 21 2F 62 69 6E 2F 62 61 73 68 0D 0A`. A fresh oracle attempt from the checked-in working tree failed before scoring with `bash: line 1: /tests/test.sh: cannot execute: required file not found` and `RewardFileNotFoundError`. The committed blob has LF, but the checkout is CRLF. This was not fixed because the scope allows changes only to this report.
- `git ls-files -s` reports `tests/test.sh` as mode `100644`, and `tests/Dockerfile` does not run `chmod +x /tests/test.sh`. Normalize line endings and add an executable bit before relying on a fresh local run.
- `task.toml` has no verifier `no-network` setting or agent `allowlist`. Current isolation relies on Harbor defaults and the Worker sandbox, not an explicit config policy.
- The verifier image is `python:3.12-slim` and `WORKER_ENV` includes `/usr/local/bin:/usr/bin:/bin`. The interpreter is still reachable; `no_python` rejects `.py` files, not interpreter use from another language.
- `instruction.md` says the Go solution must use only the standard library, but there is no separate dependency-download check. Build success alone does not prove this rule.
- No fresh successful Harbor score exists for the current reverted working tree. The 1.0/0.0 results above come from earlier hardened copies and should be described that way.

## 7. Final verdict

The hardening is effective against the three submitted cheats: each falls from roughly 0.40-0.52 to 0.0, while the oracle remains 1.0 and a nop submission remains 0.0. The decisive control is the hard behaviour gate at 0.8 combined with hidden 100K golden data.

Do not claim a fresh post-revert verification from the current checkout until the CRLF/executable-bit launcher issue is fixed and Oracle/Nop/Cheat1/Cheat2/Cheat3 are rerun.
