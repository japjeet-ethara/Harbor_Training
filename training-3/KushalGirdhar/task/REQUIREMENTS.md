# Requirements

## Source and scope

Section 18 of `04-harbor-day3.pdf` is the assignment source. It begins on PDF page 18, with the implementation and hand-in steps on pages 20–24. The user's request supplies the author, pins the source revision, adds technical and validation requirements, permits autonomous AI assistance, and requests a private ZIP handoff.

## Mandatory deliverables from section 18

| Section 18 step | Requirement |
| --- | --- |
| 1 | Record source URL, commit and date, permissive license, and at least eight rules with verified input/output examples in `NOTES.md`. |
| 2 | Build the environment from pinned `golang:1.23`. Copy the Python project without its Git metadata into `/workspace/repo` and set that working directory. |
| 3 | Give the candidate a concise, standalone brief for a standard-library-only Go CLI in `/workspace/repo`. It must build with `go build ./...`, remove all `.py` files, and reproduce the original per-record output byte for byte. Describe partial grading without disclosing test paths, answers, or test inputs. |
| 4 | Use `random.seed(1)` in `tests/gen.py`. Produce exactly 2,000 visible and 2,000 different hidden records in `tests/data/inputs.txt` and `tests/data/hidden_inputs.txt`. Create `expected.txt` and `hidden_expected.txt` solely by calling the original function. Rerun generation and spot-check five answers against upstream. |
| 5 | Use Reward Kit weighted mean. Build is binary with weight 1. Python removal is binary with weight 1 and requires a passing build. Exact per-line hidden behavior has weight 4. Write `/logs/verifier/reward.json`. Run a separate verifier that keeps its tests from candidates. |
| 6 | Ship `solution/solve.sh` to install the standard-library Go implementation and remove Python files. Check the real Harbor oracle for 1.0. |
| 7 | Check real Harbor nop for 0.0 and a replay-only `cheat/solve.sh` for a reward below 0.2. |
| 8 | Retain genuine screenshots of all three rewards, observed difficult rules, and a proposed hardening change. |

## Additional mandatory requirements from the user

- Author Kushal Girdhar, kushal.girdhar@ethara.ai. Fresh implementation and original corpus. Prior submissions and earlier generated packages are excluded as sources. The training repository is at most a conventions reference.
- Reference commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`. Identify the Python runtime, Unicode database, and optional regex backend actually used.
- Implement ordered manual rules over UTF-8 byte spans with explicit token and separator boundaries, no Go regexp, separate stream handling, matching case expansions, properties and contextual casing, and matching recursive precedence.
- Balance rule and interaction coverage across release notes, incidents, networks, and documentation. Minimize output overlap and avoid cosmetic identifiers. Independently exercise empty, CRLF, unterminated, and long records and exact framing.
- Hash two independent dataset generation runs, verify the complete frozen dataset, compare at least 100,000 independent stress records, exercise the grader and protocol, run applicable Harbor lint, and preserve logs, commands, runtime versions, configuration, and actual screenshots with provenance.
- Pin dependencies and image digests where supported. Keep agent execution and grading offline. Use distinct run directories. Clearly label any alternative validation profile.
- Preserve attribution. Keep implementation code readable and free of explanatory comments. Document the implemented system and actual AI and human contributions. Include a Windows/WSL beginner guide. Verify the ZIP, omit environments, caches, credentials and binaries, and name it `kushal-titlecase-go.zip`.

## User-directed changes to the PDF workflow

- The PDF describes a human driving Cursor through individual steps. The user explicitly authorizes Codex to complete those steps autonomously.
- The PDF suggests downloading Reward Kit during grading. The user requires offline grading, so grading dependencies are installed at image build time.
- The PDF's GitHub push and submission link are replaced by a private ZIP. Publication requires separate authorization.
- The replay copies only the visible answers and uses a separate temporary task copy, preserving the shipped oracle.

## Optional improvement

Section 18 explicitly makes a fresh model attempt and model score optional. Speed, memory, and error wording are outside the candidate's scoring criteria. Build and execution guards bound verification infrastructure usage.
