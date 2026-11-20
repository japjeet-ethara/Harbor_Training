# Hardening report

## Changes

The behavior criterion now gives credit only when every hidden output line
matches. Reward weights are `build=1`, `no_python=1`, and `behaviour=9`.
Build and no-Python checks alone can therefore contribute at most `2/11 =
0.1818` of the total reward.

The task is still graded against the original `titlecase()` default behavior
with the optional `regex` package absent, using the standard-library `re`
implementation. The replacement hidden exam contains 100,000 stable inputs.
The kit froze answers from runs with `PYTHONHASHSEED=1` and
`PYTHONHASHSEED=2`; all 100,000 were stable and none were dropped.

## Validation

| Check | Reward |
|---|---:|
| Oracle on the 100,000-input hidden exam | 1.0 |
| Nop | 0.0 |
| Mohd Rafey cheat 1 | 0.1818 |
| Mohd Rafey cheat 2 | 0.1818 |
| Mohd Rafey cheat 3 | 0.1818 |

## Port measurements

The old exam contains 2,000 inputs. The new exam contains 100,000 inputs.
"Miss chance" is the kit's estimated chance that a random 2,000-input suite
would miss all errors in that port.

| Port | Old wrong / 2,000 | Old miss chance | New wrong / 100,000 | New miss chance |
|---|---:|---:|---:|---:|
| Gaurav | 3 | 0% | 19 | 68% |
| SaurabhBaghel | 103 | 0% | 3,546 | 0% |
| LaveshDongre | 0 | 100% | 0 | 100% |

Detailed comparison output:

- Old exam: [Gaurav](./measure/old/Gaurav.txt), [SaurabhBaghel](./measure/old/SaurabhBaghel.txt), [LaveshDongre](./measure/old/LaveshDongre.txt)
- New exam: [Gaurav](./measure/new/Gaurav.txt), [SaurabhBaghel](./measure/new/SaurabhBaghel.txt), [LaveshDongre](./measure/new/LaveshDongre.txt)
