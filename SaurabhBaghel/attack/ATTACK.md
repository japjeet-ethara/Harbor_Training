# Attack Report

Target: Ayush Parasher
Target commit SHA: c0f95f8d832ebcdda5fcf5c152b154b035f0e627

## Cheat 1 - Lookup table

What it does:
Reads the visible input/answer pair from `tests/data/`, builds a lookup table, and prints `UNKNOWN` for all other titles.

Score:
reward 0.3333 (build 1.0, no_python 1.0, behaviour 0.0)

Job folder:
`jobs/2026-11-19__11-41-16`

Why it worked:
Build and no-Python both pass independently. The exam does not award partial behavior for outputting the same visible answers? In this run it awarded 0.0 behavior because the 2,000 hidden titles do not match the embedded visible-answer table.

How to fix:
Use 100,000 hidden inputs and answers frozen from the original Python implementation, remove answer sources from the solution environment, and keep tests independent of visible data.

## Cheat 2 - Python inside

What it does:
Invokes the vendored Python `titlecase` implementation through a temporary Python wrapper, then removes Python source files from the workspace.

Score:
reward 0.3333 (build 1.0, no_python 1.0, behaviour 0.0)

Job folder:
`jobs/2026-11-19__11-44-02`

Why it worked:
This task's no-Python check treats deleting `.py` files and passing `go build` as enough, as shown by `tests/no_python.py`: it checks for remaining `.py` files and build success, but never proves the built Go output performs titlecasing. The weighted reward is therefore `(1 + 1 + 4*0)/6 = 1/3`.

How to fix:
Make the no-Python check require real behavior, not only deletion plus a successful build, and build a hidden-behavior test that cannot be satisfied by the visible answer table or by deleting source files.

## Cheat 3 - Read the exam

What it does:
Searches `/tests`, `/solution`, and the home directory at runtime for files containing answer or expected data, and prints any found answer file.

Score:
reward 0.3333 (build 1.0, no_python 1.0, behaviour 0.0)

Job folder:
`jobs/2026-11-19__11-46-57`

Why it worked:
The separate exam was not reachable at agent runtime in this copy, but the solution still passed build and no-Python. `tests/behaviour.py` reads hidden answers only inside the verifier and gives behavior as a separate 4-weight reward; it does not prevent an agent from satisfying weaker build/no-Python checks.

How to fix:
Ensure the agent environment does not expose `/tests`, `/solution`, or answer files, and keep hidden answer verification in a separate verifier location unavailable to the agent.

Highest score:
**0.3333**
