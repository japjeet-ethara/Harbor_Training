# Five-Minute Defence — Day 5 Hardening

## 1. Introduction — 0:25

This task asks for a Go implementation of Python `titlecase()`: titles arrive
on standard input and the program writes one transformed title per line. The
goal of Day 5 was to harden the existing task, not replace it: reduce reward
for useless solutions, broaden meaningful behavior checks, and make security
claims only where the execution boundary supports them.

## 2. Original weaknesses — 0:35

The supplied attack report records three historical, pre-hardening results:
deleting Python files received 0.0000; a partial Go port received 0.2777; and
runtime answer-file discovery received 0.3333. The partial port omitted
important titlecase rules. The answer-discovery attempt built and passed the
no-Python check, but had zero behavior. These are historical scores, not
current attack measurements.

## 3. Stage A — Reward hardening — 0:30

Overall reward now uses weighted-sum aggregation with behaviour as its only
nonzero contributor. Build and no-Python results remain separate components,
but cannot offset incorrect outputs. This directly addresses the old failure
mode where a program with no useful behavior could still earn reward for
building or satisfying a policy check.

## 4. Stage B — Examination hardening — 0:40

The original hidden set has 2,000 cases. A fixed-seed generator, seed
`20261121`, adds 2,400 strong hidden cases for a combined 4,400. Expected
outputs come from the original Python reference implementation. The verifier
requires the exact output count and compares each output with the expected
line at the same position, so missing, extra, or reordered output cannot earn
full credit.

## 5. Stage C — Security audit — 0:40

The task uses `environment_mode = "separate"` to isolate the candidate
environment from the verifier. The expected-answer fixtures are still copied
into the verifier image by `COPY . /tests/`. The audit confirmed no
candidate-accessible answer-file path under the configured separation, but
image or build-cache access remains a low-severity residual risk. No supported
verifier-only secret or mount mechanism was found, and that risk is not
claimed as fixed.

## 6. Stage D — Attack evaluation — 0:30

Current attack measurements were blocked: Harbor provides no documented
runner for selecting the available `cheat/solve.sh` scripts as candidate
solutions. No attack job was launched, and no attack is claimed defeated.
Historical report scores must therefore remain distinct from current
validation results.

## 7. Validation results — 0:35

The recorded Oracle job, UUID
`b3d68ef9-786a-4995-aee4-07a964e8d186`, scored 1.0 overall, with build,
no-Python, and behaviour each at 1.0. The NOP job, UUID
`921529e9-3e57-4488-9545-e4456b53c7a8`, scored 0.0 on all four. Each had one
trial and zero reported exceptions. Genuine job result, reward, and verifier
output files are included in `proof/`. Those job files do not themselves print
the case count; the task verifier defines the 4,400-case examination.

## 8. Lessons learned — 0:40

First, behavioral correctness should gate reward; build and policy checks are
valuable diagnostics, not substitutes for a working solution. Second, fixed
seeds, reference-generated answers, and exact positional comparison make a
larger exam repeatable and harder to game. Third, environment separation is
meaningful evidence, but it does not erase image-access risks. Finally, a
security claim needs a supported execution path and a real measurement; an
unsupported Harbor configuration change would add risk without proving a fix.

## 9. Conclusion — 0:25

The reward design and hidden examination were hardened, and the reported
Oracle/NOP boundary remains 1.0/0.0. The remaining limitation is explicit:
answer fixtures are present in the verifier image, and current attacks were
not measured. This defence reports those boundaries rather than claiming more
than the evidence establishes.
