# Day 6 Defence Notes — Aaditya Markande

## 1. Strongest cheat and its score
Rudransh's cheat 2 (read `/tests/data/hidden_expected.txt` at run time).
Before: **1.000** (job `2026-11-20__11-26-02`). After: **0.000** (job `2026-11-20__11-14-26`).
Why: the old `test.sh` ran the solution's binary while `/tests` was mounted. Now the binary runs in an
empty chroot jail as an unprivileged user, so it cannot open any answer file.
The other two cheats: cheat 1 0.406 -> 0.079, cheat 3 0.667 -> 0.000.

## 2. Before and after exam table
| Port | Wrong on 100K | Old 2K exam caught it? |
|---|---:|---|
| my oracle | 0 | n/a |
| NehaGaur | 488 | no |
| AahanTrikha | 889 | no |

Proofs on the hardened task (`proof/`): oracle 1.0 (job `2026-11-20__11-12-15`), nop 0.0
(job `2026-11-20__11-13-31`). All three of Rudransh's cheats are below 0.2.

## 3. What surprised me
- Rudransh's report said cheat 2 got 0.333. My own re-run gave 1.000. The isolated run hid the hole.
- Five of the 14 ports I scanned were wrong on exactly 3,053 titles. They match titlecase WITHOUT
  `regex`, and my exam is WITH `regex`. This is why the mode must be written in `instruction.md`.
- My Go port is wrong on 0 of 100,000 titles, so the new exam found no bug in my own port.

## 4. What did not work first time (honest)
My first size rule counted every file in `/workspace/repo`. `go build` leaves a 2.3 MB binary there, so my
own oracle scored 0 (`no_python` 0). I found it with `bash -x` and changed the rule to count only `.go` and
`go.mod` files. Early runs also failed because I pasted `test.sh` wrongly. `bash -x` showed the real cause.

## 5. Limits I know about
- `answers.txt` is in the public class repo. Someone could embed answers in Go source, but the 400 KB
  source limit and the 8 MB binary limit stop that.
- The jail uses `chroot` as root inside the container. It is not a full sandbox against kernel escapes.
- Python comes from the task image: the `regex` module is installed only so the original can run.

## 6. Every change, in my own words
- `tests/test.sh`: gated reward, "clean" checks, chroot jail, new data files.
- `tests/data/`: 100,000 inputs and answers. Old visible and hidden files removed.
- `instruction.md`: states the mode (WITH regex), says input is UTF-8, lists the new rules.
- `kit/`: the three scripts and `report.txt`. `measure/`: wrong-answer counts for three ports.
