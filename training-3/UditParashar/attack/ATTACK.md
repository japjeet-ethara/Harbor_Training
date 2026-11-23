# Day 4 Attack Report

## 1. Target Information

- Attacker: Udit Parashar
- Target: Saket Kukatkar
- Target task path: `SaketKukatkar/titlecase-go`
- Target commit SHA: `edfead0283987cece7d7fad04848356b4034a8ad`
- Repository: `Harbor_Training`
- Date: 2026-11-20

## 2. Target Task Analysis

The task asks for a Go port of python-titlecase 2.4.1 that reads one title per
line from stdin and writes one title-cased line to stdout
([instruction.md](../../../SaketKukatkar/titlecase-go/instruction.md),
lines 3-7). The solution must be a root `main` package with `go.mod`, use only
the Go standard library, remove every `.py` file, and build with
`go build ./...` ([instruction.md](../../../SaketKukatkar/titlecase-go/instruction.md),
lines 9-15).

The reward is weighted by `reward.toml`: build weight 1, no-python weight 1,
and hidden behaviour weight 4 ([reward.toml](../../../SaketKukatkar/titlecase-go/tests/reward.toml),
lines 1-6). The behaviour check executes the built binary on 2000 hidden inputs
and compares its stdout with frozen answers
([behaviour.py](../../../SaketKukatkar/titlecase-go/tests/behaviour.py),
lines 18-42). The no-python check requires no `.py` files and a successful build
([no_python.py](../../../SaketKukatkar/titlecase-go/tests/no_python.py),
lines 20-29).

A key weakness is that visible and hidden data are separate: the visible
`tests/data/inputs.txt` and `expected.txt` are only 2000 examples, while scoring
uses `hidden_inputs.txt` and `hidden_expected.txt`. Another weakness is that
the structural checks award 1/3 of the final reward combined, even when
behaviour is zero. This made a lookup-only or cleanup-only attack potentially
worth investigating.

The original target is protected. The attack copy was created from commit
`edfead0283987cece7d7fad04848356b4034a8ad` and its `tests/`, `task.toml`, and
`environment/` directories were not modified.

## 3. Cheat 1 — Lookup Table / Memorization Attack

- Attack idea: Embed 10 legitimate examples from the visible `inputs.txt` /
  `expected.txt` pair, then use a simple capitalisation fallback for every other
  input.
- Files created: `training-3/UditParashar/attack/cheat1/solve.sh`
- How it works: The script deletes Python files, writes a Go program, embeds
  selected visible input/output pairs, and returns a basic fallback for unseen
  titles.
- Why it might succeed: It can earn exact answers for overlapping visible
  examples and any structural credit that the verifier may award.
- Why it might fail: The hidden set is distinct and is 2000 lines.
- Failed Harbor command:
  `harbor run -p C:\Users\UditParashar\Harbor_Training\uditparashar\attack\scratch-cheat1 -a oracle`
- Original Harbor job folder: `jobs/2026-11-20__15-55-11`
- Original Harbor result: `RewardFileNotFoundError` because `/tests/test.sh`
  could not launch with CRLF line endings.
- Direct Reward Kit result (not a Harbor-managed job): `0.3333`
- Reward file:
  `training-3/UditParashar/attack/results/cheat1-reward.json`
- Direct-run commands (with `<workspace>`, `<logs>`, and `<cheat-script>` set
  to the corresponding cheat's paths):
  `docker run --rm -v <workspace>:/workspace/repo -v <cheat-script>:/solution/solve.sh:ro golang:1.23.4-bookworm bash -c "tr -d '\r' < /solution/solve.sh | bash"`
  `docker run --rm -v <workspace>:/workspace/repo -v <tests>:/tests:ro -v <logs>:/logs saket-verifier-local bash -c "tr -d '\r' < /tests/test.sh | bash"`
- Result: The real target verifier checks ran after line-ending normalization
  in the execution stream only; no target file was modified. Because this was
  a direct Reward Kit run and not a Harbor-managed run, the score has no
  corresponding Harbor job folder and does not satisfy the assignment's
  Harbor-job evidence requirement.
- Recommended fix: Use a larger/disjoint hidden exam and keep structural checks
  gated on meaningful behaviour.

## 4. Cheat 2 — Partial Implementation Attack

- Attack idea: Implement only basic first-letter capitalization and middle
  small-word lowercasing, deliberately omitting hyphen, slash, apostrophe,
  acronym, Mc-name, and Unicode edge handling.
- Files created: `training-3/UditParashar/attack/cheat2/solve.sh`
- How it works: The script deletes Python files and builds a root-package Go
  binary that processes stdin line-by-line.
- Why it might succeed: Common visible-style lines may receive partial credit,
  and it may receive partial structural credit.
- Why it might fail: Most rare and mixed-case hidden lines require special
  titlecase rules.
- Failed Harbor command:
  `harbor run -p C:\Users\UditParashar\Harbor_Training\uditparashar\attack\scratch-cheat2 -a oracle`
- Original Harbor job folder: `jobs/2026-11-20__16-00-45`
- Original Harbor result: `RewardFileNotFoundError` because `/tests/test.sh`
  could not launch with CRLF line endings.
- Direct Reward Kit result (not a Harbor-managed job): `0.3333`
- Reward file:
  `training-3/UditParashar/attack/results/cheat2-reward.json`
- Direct-run commands: same Docker commands as Cheat 1, using Cheat 2's
  workspace and script.
- Result: The real target verifier checks ran after line-ending normalization
  in the execution stream only. This score has no corresponding Harbor job
  folder and does not satisfy the assignment's Harbor-job evidence requirement.
- Recommended fix: Add explicit edge-case families and use a nonzero behaviour
  floor or behaviour-gated structural checks.

## 5. Cheat 3 — Build / Restriction / Evaluation Weakness Attack

- Attack idea: Attempt a read-the-exam solution that searches for hidden answers
  at several standard container paths, with no real titlecase implementation.
- Files created: `training-3/UditParashar/attack/cheat3/solve.sh`
- How it works: It deletes Python files, builds a Go binary, and tries to read
  hidden answer files from `/tests`, `/workspace/repo/tests`, or
  `/workspace/tests`.
- Why it might succeed: If Harbor exposed hidden verifier data to the solution
  container, it could reproduce answers.
- Why it might fail: Harbor normally keeps the verifier in a separate container;
  the solution should not receive `/tests/data/hidden_expected.txt`.
- Failed Harbor command:
  `harbor run -p C:\Users\UditParashar\Harbor_Training\uditparashar\attack\scratch-cheat3 -a oracle`
- Original Harbor job folder: `jobs/2026-11-20__16-03-51`
- Original Harbor result: `RewardFileNotFoundError` because `/tests/test.sh`
  could not launch with CRLF line endings.
- Direct Reward Kit result (not a Harbor-managed job): `0.3333`
- Reward file:
  `training-3/UditParashar/attack/results/cheat3-reward.json`
- Direct-run commands: same Docker commands as Cheat 1, using Cheat 3's
  workspace and script.
- Result: The real target verifier checks ran after line-ending normalization
  in the execution stream only. This score has no corresponding Harbor job
  folder and does not satisfy the assignment's Harbor-job evidence requirement.
- Recommended fix: Keep verifier data separate and run verifier tests in a
  container; add a runtime filesystem restriction if `/tests` or other answer
  locations must be inaccessible.

## 6. Results Comparison

| Cheat | Attack Type | Direct Reward Kit Score (not Harbor-managed) | Harbor Job Folder | Result |
|---|---|---|---|---|
| Cheat 1 | Lookup Table | `0.3333` | `jobs/2026-11-20__15-55-11` (failed before scoring) | Direct verifier produced JSON; no Harbor score |
| Cheat 2 | Partial Implementation | `0.3333` | `jobs/2026-11-20__16-00-45` (failed before scoring) | Direct verifier produced JSON; no Harbor score |
| Cheat 3 | Read-the-exam | `0.3333` | `jobs/2026-11-20__16-03-51` (failed before scoring) | Direct verifier produced JSON; no Harbor score |

## 7. Strongest Cheat

All three cheats tie at `0.3333` in the direct Reward Kit runs against the real
target checks. None has a qualifying Harbor reward: all three Harbor jobs
failed to start the verifier. These direct scores must not be presented as
Harbor job scores.

## 8. Recommended Fixes

- Fix `tests/test.sh` line endings to LF so `/tests/test.sh` launches under Linux.
- Separate hidden answers from any task files the solution container can mount.
- Widen the hidden set and include the targeted rare families documented in
  `NOTES.md`.
- Consider behaviour-gating build and no-python scores so structural-only
  shortcuts cannot contribute most of a successful reward.
- The direct verifier reward files are preserved under `attack/results/`.

## 9. Conclusion

Three distinct solutions were created and each was attempted through the normal
Harbor `-a oracle` interface against a fresh scratch copy. Harbor produced no
reward for those runs because the verifier entrypoint was not executable under
Linux with CRLF line endings. The real target checks were then run directly
with Reward Kit in a verifier container, producing JSON with `0.3333` for each
cheat; these are not Harbor-managed job results and do not fulfill the
assignment's Harbor-job evidence requirement. The clean target copy was not
modified, and no Harbor score or job identifier was fabricated.
