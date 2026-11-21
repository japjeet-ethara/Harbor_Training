# Day 4 grading report

Target revision is recorded in [TARGET.txt](TARGET.txt). File references below are relative to the local `attack/target/` copy.

Harbor 0.26.0 rejected the target's package name and agent network setting at `task.toml:4` and `:13`. Harbor 0.1.10 ran the unmodified tests against all three submissions in its shared verification environment. That release predates the separate verifier setting in `task.toml:17`. Each trial produced a structured verifier reward, then job aggregation exited because this release expects a single reward key. The scores below come directly from the three verifier files. Independent reruns reproduced all three reward files byte for byte.

## Read-only review

1. **Agent workspace.** The image recipe starts with `FROM golang:1.23` and runs `COPY python-titlecase /workspace/repo` and `WORKDIR /workspace/repo`. Inspection of the local image found `titlecase/__init__.py`, `titlecase/tests.py`, `setup.py`, `setup.cfg`, `pyproject.toml`, `tox.ini`, `AUTHORS.rst`, `LICENSE.txt`, `README.rst`, `.gitignore`, and two GitHub workflows. The base image also provides `/usr/bin/python3`. `environment/Dockerfile:1`, `:3`, `:5` and `environment/.dockerignore:1`.
2. **Scoring.** Build is binary and invokes `go build -o /tmp/titlecase_test_bin .`. The Python-file check is binary and runs only after a successful build. Behaviour starts at zero and is calculated from a diff when output is nonempty. The final expression is `($build_score * 1 + $no_py_score * 1 + $behaviour_score * 4) / 6.0`. `tests/test.sh:9`, `:19`, `:37`, `:43`, `:51` and `:58`.
3. **Inputs.** The scored verifier reads `tests/data/hidden_inputs.txt` and compares against `tests/data/hidden_expected.txt`. The separate diagnostic script reads `tests/data/inputs.txt` and `tests/data/expected.txt`. The generator uses seed 1 for the diagnostic set and seed 2 for the scored set. `tests/test.sh:34`, `:35`, `tests/diff_check.sh:5`, `:6`, and `tests/gen.py:141`.
4. **Test visibility.** I confirmed `/tests` was absent in the local starting image. The task declares `environment_mode = "separate"`, and Harbor reserves test files for verification. The Python package's own `titlecase/tests.py` is inside the copied source tree. `environment/Dockerfile:3`, `task.toml:17`, and `environment/python-titlecase/titlecase/tests.py:1`. [Harbor task-creation guide](https://github.com/harbor-framework/harbor/blob/main/skills/create-task/SKILL.md)
5. **Weakest points.**
   - Build and absence of Python files can earn reward independently of useful output. The build command also checks only the root package despite the instruction requiring `go build ./...`. Gate submission acceptance on functional correctness and run the documented build command. `tests/test.sh:10`, `:19`, `:58`, and `instruction.md:11`.
   - The behaviour score uses diff hunks as a proxy for positional matches and ignores the program's exit status. Check process success, output count, and byte-for-byte equality at each position. `tests/test.sh:40`, `:43`, and `:47`.
   - Both datasets use the same generator and finite token lists, and the specification leaves the reference's optional regex mode unstated. Add cases outside the shared generator vocabulary and pin the reference mode. `tests/gen.py:24`, `:126`, `:141`, `instruction.md:15`, and `environment/python-titlecase/titlecase/__init__.py:18`.

## Cheat 1 — Half port

**What it does:** Capitalizes the first rune of each word and keeps common interior small words lowercase. It also removes the starter Python files.

**Score:** reward 0.4240 (build 1, no_python 1, behaviour 0.1360). [Verifier reward](results/cheat1-reward.json)

**Job folder:** `HarshitKumar/jobs/day4-20261118-172730/runs/day4-20261118-172730-legacy-cheat1`, trial `cheat1__zwqDxBE`.

**Why it worked:** The verifier awarded partial behaviour at `tests/test.sh:51` and added both binary checks at `tests/test.sh:58`.

**How to fix:** Expand the suite with independent Unicode, whitespace, compound, and punctuation cases. Require a minimum correctness threshold before awarding the binary checks.

## Cheat 2 — Build-only program

**What it does:** Creates a Go module with an empty main function and removes the starter Python files.

**Score:** reward 0.3333 (build 1, no_python 1, behaviour 0.0). [Verifier reward](results/cheat2-reward.json)

**Job folder:** `HarshitKumar/jobs/day4-20261118-172730/runs/day4-20261118-172730-legacy-cheat2`, trial `cheat2__gZ53Tze`.

**Why it worked:** The empty program passed the build and absence checks at `tests/test.sh:10` and `:19`. The weighted sum at `tests/test.sh:58` credited both checks even with zero behaviour.

**How to fix:** Require valid output with the expected line count before awarding build and Python-file points.

## Cheat 3 — Lookup table

**What it does:** Removes the starter Python files and builds a Go program that looks up exact matches in visible input and answer files when available. It echoes unmatched titles.

**Score:** reward 0.3337 (build 1, no_python 1, behaviour 0.0005). [Verifier reward](results/cheat3-reward.json)

**Job folder:** `HarshitKumar/jobs/day4-20261118-172730/runs/day4-20261118-172730-legacy-cheat3-lookup`, trial `cheat3-lookup__2taPkgr`.

**Why it worked:** The Dockerfile copies only the starter source into `/workspace/repo`, so the script had no visible answer files at the paths it checks and fell back to echoing inputs. Most of its reward came from passing the build and Python-file checks. `environment/Dockerfile:3` and `tests/test.sh:10`, `:19`, `:58`.

**How to fix:** Keep the expected answers out of the agent workspace and gate build and Python-file points on a minimum behaviour score.

**Highest measured score: 0.4240 (Cheat 1, `day4-20261118-172730-legacy-cheat1`).**
