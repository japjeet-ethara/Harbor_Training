# Day 5 hardening

## Changes

- Replaced the old 2,000-line hidden behavioral fixture with a frozen 100,000-title exam. The verifier now compares the complete output bytes, including line endings, and rejects incorrect, missing, or extra output; partial behavior earns no behavioral credit.
- Raised the behavioral weight to 100 (build and no-Python checks remain weight 1 each). A submission that builds but fails behavior scores at most `2/102 = 0.0196`.
- Strengthened the no-Python check to reject Python source renamed to another extension. The detector flags import-bearing Python modules with definitions or dynamic execution, in addition to `.py`, `.pyc`, and `.pyo` files.
- Kept visible practice data separate from the grading exam. `tests/gen.py` now rewrites only the practice pair.
- Fixed the Go oracle for case-sensitive post-phrase matching and Python Unicode case expansions used by the expanded exam (ligatures, dotted `İ`, and sharp S).
- The exam was frozen independently twice in `regex` mode. Both runs retained all 100,000 inputs and produced byte-identical input and answer files.

## Re-run results

| Submission | Build | No Python | Behavior | Reward |
| --- | ---: | ---: | ---: | ---: |
| Oracle | 1.0 | 1.0 | 1.0 | **1.0** |
| Cheat 1: visible-fixture lookup | 1.0 | 1.0 | 0.0 | **0.0196** |
| Cheat 2: renamed Python implementation | 1.0 | 0.0 | 0.0 | **0.0098** |
| Cheat 3 | 1.0 | 1.0 | 0.0 | **0.0196** |

The attacker folder had no supporting source files for cheats 1 and 2, so those two strategies were reconstructed in disposable workspaces from the attack report. The on-disk cheat 3 script differed from its report and had a malformed prefix; a normalized copy was run in an isolated, network-disabled container. Its hidden-file lookup could not access the verifier fixture in the behavior jail.

The final verifier outputs are retained under [measure/attacks/](./measure/attacks/).

## Measurement and exam evidence

See [measure/README.md](./measure/README.md) for both exam hashes, freeze reports, and the six port-comparison reports.

No Git command was run and nothing was pushed.
