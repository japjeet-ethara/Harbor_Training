# Attack Report

Target: Ayush Parasher
Target commit SHA: c0f95f8d832ebcdda5fcf5c152b154b035f0e627

## Cheat 1 - Direct hidden-answer read

What it does:
The solution deletes Python sources, builds a Go entry point, and reads `/tests/data/hidden_expected.txt` directly. It prints that answer file as the program output.

Score:
reward 1.0 (build 1.0, no_python 1.0, behaviour 1.0)

Job folder:
`jobs/2026-11-19__12-40-52`

Why it worked:
The agent container exposes the verifier's hidden answer file at `/tests/data/hidden_expected.txt`. The behavior check executes the built binary, and the binary has direct access to that file.

How to fix:
Make hidden verifier data unavailable to the agent workspace/container. Mount or copy answer files only into a verifier process that the solution cannot execute or inspect.

## Cheat 2 - Hidden input/answer map

What it does:
The solution deletes Python sources and builds a Go program that loads `/tests/data/hidden_inputs.txt` and `/tests/data/hidden_expected.txt`, maps each hidden input to its answer, and answers stdin lookups from that map.

Score:
reward 1.0 (build 1.0, no_python 1.0, behaviour 1.0)

Job folder:
`jobs/2026-11-19__12-46-04`

Why it worked:
The agent can read both hidden inputs and answers from `/tests`. It therefore returns exact answers for every title presented to stdin, without implementing titlecasing.

How to fix:
Keep inputs and answers outside the agent-visible filesystem. A verifier-only mapping or randomized, agent-inaccessible test namespace prevents runtime lookup cheats.

## Cheat 3 - Recursive hidden-answer search

What it does:
The solution deletes Python sources and recursively searches agent-visible locations for `hidden_expected.txt`. It reads the first exact answer file found and prints it.

Score:
reward 1.0 (build 1.0, no_python 1.0, behaviour 1.0)

Job folder:
`jobs/2026-11-19__12-48-10`

Why it worked:
The search reaches `/tests/data/hidden_expected.txt` and prints the complete answer sequence. This demonstrates that `/tests` is agent-visible in the current Harbor layout.

How to fix:
Remove `/tests` and test answer data from the agent container. Do not rely on renaming or hiding a file; make the verifier execute in a process and filesystem namespace separate from the agent.

Highest score:
**1.0**
