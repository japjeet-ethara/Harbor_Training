# Defence Report — Rucchika Kapoor / titlecase-go

## 1. Defense Summary

The supplied attack report identified two successful bypasses in the original task:
reading the hidden answer file from the solution process and earning structural
credit without implementing titlecasing. The revised verifier closes the shared
filesystem path to the executable and makes behavior the only source of reward.

## 2. Attack-to-Control Mapping

| Reported approach | Original result | Defense | Recheck |
|---|---:|---|---|
| Echo or empty Go program | `0.3333` | Build and no-Python checks are prerequisites. Behavior below `0.20` receives no reward. | Echo replay: behavior `0.01442`, reward `0.0`. |
| Read `/tests/data/hidden_expected.txt` | `1.0000` | Run the executable as an unprivileged user in a chroot containing only the built binary; feed inputs over stdin. | File-read replay: hidden path unavailable, behavior `0.0`, reward `0.0`. |
| Embed or invoke the shipped Python implementation | `0.3333`, behavior `0.0` in the report | The jailed filesystem contains no Python runtime or reference source; the verifier disables network access. | Not replayed separately after the changes. |
| Omit or append output records | Not reported as a successful attack | Require the output record count to equal the fixture count before scoring. | Enforced by the grader. |

## 3. Defense Boundaries

- The hidden input and expected-output files remain verifier assets; the submitted
  executable receives neither file path nor filesystem access to `/tests`.
- The chroot runs with cleared supplementary groups and an empty environment. Only
  standard input/output/error are passed to the process.
- CPU/runtime, process count, open files, core dumps, and output-file size are limited.
- The generated hidden suite contains 100,000 frozen cases; expected results are
  checked against the reference implementation and filtered for stability across two
  hash seeds.

## 4. Validation and Limitations

Harbor lint and Python syntax checks passed. The two successful approaches in the
supplied report were replayed against the local verifier Docker image: the hidden-file
reader scored `0.0`, and the echo program scored `0.0` reward. These are local verifier
tests, not a full Harbor submission or a guarantee against unknown future attacks.
