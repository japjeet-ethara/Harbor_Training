# Rewards

Harbor itself has not been run yet. Windows required a reboot after Virtual Machine Platform was enabled (DISM exit 3010), and the Docker engine cannot start until that reboot.

The same three checks were scored on this machine with `go build` and a line-by-line compare against `tests/data/hidden_expected.txt`. Weights are build 1, no_python 1, behaviour 4.

| Run | build | no_python | behaviour | reward |
| --- | ---: | ---: | ---: | ---: |
| Oracle (Go port, `.py` files removed) | 1 | 1 | 1 | 1.0 |
| Nop (untouched Python tree) | 0 | 0 | 0 | 0.0 |
| Cheat (prints `expected.txt`, leaves `.py` files) | 1 | 0 | 0.002 | 0.168 |

The cheat matches 4 of 2000 hidden lines, so the reward stays under 0.2. Both 2000-line sheets were generated twice with `random.seed(1)` and the copies were identical. The Go port matched all 4000 frozen lines and the single-line cases in `titlecase/tests.py`.

The official suite and the generated sheets matched on the first comparison. The behaviour that is easiest to get wrong, and the fair way to make the task harder, is the interaction of three rules: `Mc`/`MC` prefixes (but not `Mac`), `d`/`o`/`l` apostrophes, and all-caps initials such as `D.C.` that must survive an otherwise lowercased line. A fair hardening step is one more conjunctive check for a single line that contains all three, still graded by the original `titlecase()` output.
