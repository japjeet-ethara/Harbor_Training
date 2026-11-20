# Attack on Lavesh Dongre's titlecase-go

Target: `Lavesh/titlecase-go` at commit `7effb379807a9ae0ab8c285907598e51872a99b6` (see `TARGET.txt`).

Each cheat is a `solution/solve.sh` placed in a scratch copy of the target and run with `harbor run -p <scratch copy> -a oracle` (Harbor 0.25.0, one trial each). The target's `tests/`, `task.toml` and `environment/` were not changed. Job folders are in `C:\Users\MohdRafey\harbor-jobs\`. File:line references are to the target's files.

The reward is (build + no_python + 4 × behaviour) / 6 (`tests/reward.toml:4`).

## Cheat 1 — Delete trick + build trick

```
What it does:   Deletes every .py file and the titlecase/ folder, then writes go.mod and an
                empty main.go (func main() {}) that reads nothing and prints nothing.
Score:          reward 0.3333  (build 1, no_python 1, behaviour 0.0; matched=0 expected=2001)
Job folder:     2026-11-19__10-58-22  (trial lavesh-cheat1__b6oeF77)
Why it worked:  build and no_python are scored on their own and give 2/6 for no real work:
                build only runs `go build ./...` (tests/build.py:3); no_python only checks that
                no file name ends in .py and that the build passes (tests/no_python.py:10-29).
How to fix:     Give build and no_python points only when behaviour also passes a threshold,
                or score behaviour alone. Then an empty program scores 0.
```

## Cheat 2 — Half port

```
What it does:   Deletes the Python, then writes a small Go program that only capitalises the
                first letter of each word and keeps the small words lowercase (except first/last).
Score:          reward 0.5932  (build 1, no_python 1, behaviour 0.3898; matched=780 expected=2001)
Job folder:     2026-11-19__11-19-53  (trial lavesh-cheat2__DHCrx2n)
Why it worked:  behaviour gives credit line by line (tests/behaviour.py:98-111), so a port that
                skips most rules still gets 780 lines right. Added to the free 2/6 from build and
                no_python (tests/reward.toml:4), a clearly wrong port scores above 0.5.
How to fix:     Make behaviour all-or-nothing, or give 0 below a high pass rate, and gate build
                and no_python on it. Add inputs that hit the skipped rules (all caps, Mc, o'/d',
                hyphens, acronyms, sub-phrases) so a weak port matches far fewer lines.
```

## Cheat 3 — Python inside

```
What it does:   Copies the original titlecase/__init__.py to titlecase_src.txt (not .py), deletes
                every .py file, and builds a Go wrapper that embeds that source and runs it with a
                Python interpreter. If no interpreter is found it exits with an error.
Score:          reward 0.3333  (build 1, no_python 1, behaviour 0.0; verifier log: program_exit=1)
Job folder:     2026-11-19__11-37-31  (trial lavesh-cheat3__cFE2jR4)
Why it worked:  no_python passed although the full Python source was still in the repo, because it
                only checks file names (tests/no_python.py:11). Python 3.11.2 was present in the
                agent image (agent log: /usr/bin/python3).
Why it failed:  behaviour was 0 because the program exited with code 1, which scores 0 before any
                line is compared (tests/behaviour.py:94-96). The wrapper exits 1 only if it finds
                no Python or Python fails. Its error text is not in the logs, so the exact cause
                is not confirmed. It fits the grading setup: the program runs under chroot in a
                folder holding only the binary and its libraries (tests/behaviour.py:12-53, 81-87).
How to fix:     Check file contents, not only names (for example, reject the original source or
                any Python code). Keep the chroot jail: it stopped this cheat. Optionally remove
                Python from the agent image, which golang:1.23 includes (environment/Dockerfile:1).
```

## Summary

| Cheat | Reward | build | no_python | behaviour | Job folder |
|---|---|---|---|---|---|
| 1. Delete + build | 0.3333 | 1 | 1 | 0.0 | 2026-11-19__10-58-22 |
| 2. Half port | 0.5932 | 1 | 1 | 0.3898 | 2026-11-19__11-19-53 |
| 3. Python inside | 0.3333 | 1 | 1 | 0.0 | 2026-11-19__11-37-31 |

Strong parts: the chroot jail kept the Python cheat from scoring, and the agent's image does not contain the tests (only `python-titlecase` is copied in, `environment/Dockerfile:2`; `tests/` is copied only into the verifier image, `tests/Dockerfile:9`). No cheat tried to read the answers. Weak parts: free points for build and no_python, partial credit per line, and a name-only Python check.

**Highest score any cheat got: 0.5932 (Cheat 2, Half port).**
