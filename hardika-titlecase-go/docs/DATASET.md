# Dataset and scoring

`tests/gen.py` seeds Python’s random generator with 1. Each of the two splits has 400 titles from each of five families covering bibliographies, exhibitions, publication catalogues, music programs and historical material. The title patterns combine subjects, names and places with varied casing, competing punctuation rules, recursively processed compounds and Unicode characters. The generator rejects a candidate if its exact input or its upstream-computed output has already appeared in either split. It adds no record identifiers.

| Split | Inputs | Answers |
| --- | --- | --- |
| Visible | `tests/data/inputs.txt` | `tests/data/expected.txt` |
| Hidden | `tests/data/hidden_inputs.txt` | `tests/data/hidden_expected.txt` |

All four files contain 2,000 UTF-8 records, with LF as the byte delimiter. A Unicode line separator or an ASCII vertical tab can occur within a record. Standard Python `splitlines()` would treat those as record delimiters. The verifier parses LF bytes and checks casing, tabs and punctuation without normalization. Both frozen splits and their regeneration hashes are recorded in `evidence/`. The stress generator uses a different seed, grammar and character pools from the frozen dataset.

## Reward

Reward Kit writes `/logs/verifier/reward.json`, including three components and the aggregate `(build + no_python + 4 × behaviour) / 6`. The build check executes `go build ./...`. Python removal pays only when the build succeeds. The behavior check compiles the root command, pipes the hidden input bytes to it, and compares output record bytes at the same indexes. A partial final record without LF earns no point for that record. Extra output or unsuccessful execution earns zero behavior credit.

The separate verifier image admits the candidate workspace artifact. Only the verifier image contains hidden data. The verifier opens the input as standard input for the candidate process, keeps expected bytes private, and invokes Go and the resulting command as UID/GID 65534 with cleared supplementary groups and no new privileges. Network access is disabled for both Harbor environments. The launcher limits candidate execution and output so a stalled or noisy command cannot stall grading indefinitely.

## Scoring limitations

The visible-answer replay fixture leaves the starter Python files and earns only the build component. A replay that also deletes the Python files earns 2/6 under the required weights even with zero behavior credit. The below-0.2 threshold applies to the bundled fixture. The frozen splits share the same template families and cannot establish correctness on arbitrary titles. The standard-library rule is stated in the instruction and the environment disables module downloads. An offline build alone cannot detect all forms of vendored dependencies.
