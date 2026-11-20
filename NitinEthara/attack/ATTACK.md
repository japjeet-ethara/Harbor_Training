# Attack on Ayush Ranjan's task (titlecase-go)

Target: Ayush Ranjan, commit 60bd919b260d75a90a7c2b380a4cf297b2503d0c (training-3/AyushRanjan/task).
All numbers below must be replaced by the Harbor run results before pushing.

## Cheat 1 — Lookup table from leaked answer files
What it does:   Reads /workspace/repo/tests/data/{inputs,hidden_inputs,expected,hidden_expected}.txt (copied into the agent image),
                embeds them in a Go binary with go:embed and prints the remembered answer. Unknown line -> echoed unchanged.
Score:          reward <FILL FROM HARBOR>   (build <_>, no_python <_>, behaviour <_>)   [local simulation: 0.9973, behaviour 1991/2000]
Job folder:     <FILL: jobs/...>
Why it worked:  environment/Dockerfile:5 copies the whole python-titlecase tree, including environment/python-titlecase/tests/data/*.txt,
                into /workspace/repo. The seeded generator (tests/gen.py:36 random.seed(1)) makes that older set overlap the real hidden set:
                1,991 of 2,000 hidden inputs are already present with identical answers. Real hidden files: tests/data/hidden_*.txt.
How to fix:     Do not ship tests/ or gen.py in the agent image; regenerate the exam with a new seed/pool and keep it only in the verifier.

## Cheat 2 — Python inside (Go wrapper around python3)
What it does:   Copies titlecase/__init__.py to pysrc/tc.txt, deletes all *.py, and ships a Go program that embeds the source and
                runs it with `python3 -c` at run time.
Score:          reward <FILL FROM HARBOR>   [local simulation: 1.0]
Job folder:     <FILL: jobs/...>
Why it worked:  tests/criteria/no_python.py:21 only checks for files named *.py; tests/Dockerfile:1 (python:3.12-slim) and :10
                provide python3 and titlecase in the verifier, so the wrapper runs there.
How to fix:     Run the binary where python is absent, or scan sources/binary for python3/exec use; award no_python only with real behaviour.

## Cheat 3 — Build/Delete trick (no work)
What it does:   Deletes *.py and ships an empty `func main() {}`.
Score:          reward <FILL FROM HARBOR>   (expected build 1, no_python 1, behaviour 0)   [local simulation: 0.3333]
Job folder:     <FILL: jobs/...>
Why it worked:  tests/criteria/reward.toml:4 weights build 1 + no_python 1 out of 6, and build.py:35 / no_python.py:40 need only a successful build.
How to fix:     Gate build and no_python on behaviour (e.g. zero them if behaviour < 0.5).

Other notes: instruction.md does not state the regex/no-regex mode; tests/test_outputs.py is not used by the verifier (tests/Dockerfile:14 copies only criteria/).

**Highest score any cheat got: <FILL FROM HARBOR>**
