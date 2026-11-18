# Optional Cursor authoring workflow

These are prompts for future Cursor sessions. They are not a claim that Cursor was used to create the supplied package, and they are not evidence that any commands below have run successfully.

Use the README for installation, version pins, workspace creation, and submission commands. For a fresh implementation, work in a new `titlecase-go` task folder with a sibling `python-titlecase` clone. Open their parent folder in Cursor so it can read both. Run the command blocks below from `titlecase-go`. The original clone must be pinned to `42f43e2de55bf003b286c6f8e8d8b2d26676a167` and remain unchanged. After Step 2, `environment/repo` is the reproducible source snapshot.

Paste one stage prompt at a time. Run its checks yourself. If a check fails, paste the exact command and complete error into Cursor and ask for the smallest correction; do not proceed on an unverified “done.”

## Step 1 — Understand the original

### Paste into Cursor

```text
Read ../python-titlecase/titlecase/__init__.py and ../python-titlecase/LICENSE.txt.
The source must be commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167.
Use CPython 3.12, Unicode 15.0.0, and the standard-library re fallback;
the optional regex package must be absent. Run Python with -S.

Write titlecase-go/NOTES.md containing the repository URL, full commit SHA,
commit date, MIT license name, and at least eight numbered behavior rules.
For each rule, run the original default titlecase(text) function and record
an actual input/output example. Use repr-style notation to preserve spaces.
Do not guess outputs or change the original source. Explain the difference
between all-uppercase lines and mixed-case lines, recursion, whitespace,
and Unicode casing. Record incorrect predictions honestly if any occur.
Change only NOTES.md.
```

### Check

```bash
git -C ../python-titlecase log -1 --format='%H %cI'
test -f NOTES.md
PYTHONPATH=../python-titlecase python3.12 -S - <<'PY'
import titlecase
assert titlecase.REGEX_AVAILABLE is False
print('Reference:', titlecase.__file__)
for value in ('the lord of the rings', 'NASA AND THE MOON', "d'artagnan l'amour o'brien"):
    print(repr(value), '->', repr(titlecase.titlecase(value)))
PY
```

Compare those actual outputs with the notes. Confirm at least eight rules and examples are present. The real license filename is `LICENSE.txt`.

## Step 2 — Build the starting environment

### Paste into Cursor

```text
Create the Harbor agent environment for this task. Stage the tracked files
from the pinned ../python-titlecase commit under environment/repo using
git archive. Exclude .git, virtual environments, caches, and author notes;
keep LICENSE.txt and the actual Python project files.

Use environment/ as the Docker build context. Start from the official
Go 1.23 image pinned to the verified digest in the README. Copy repo/ into
/workspace/repo and set that directory as WORKDIR. Run the agent as a
non-root user that owns its workspace. Do not copy solution/ or tests/
into the image. For this stage, copy only repo/; public examples will be
added in Step 4. Keep the original source checkout unchanged.
Print the exact build command and explain which files enter the image.
```

### Check

```bash
docker build -t titlecase-go:author ./environment
docker run --rm --network none titlecase-go:author sh -c \
  'test -f /workspace/repo/titlecase/__init__.py && test ! -e /workspace/repo/.git && ls -la /workspace/repo'
```

The build must succeed and the container must contain the original Python files. A sibling path such as `COPY ../python-titlecase ...` is not a valid substitute for staging files inside the build context.

## Step 3 — State the exact task

### Paste into Cursor

```text
Write instruction.md for the candidate agent. Explain the pinned repository
and the default Python function: CPython 3.12, Unicode 15.0.0, stdlib re,
no callback, default options, no modified small-word list.

Require a Go module and root main package in /workspace/repo, with
successful go build ./..., go build -o /tmp/titlecase ., and go run .
The CLI reads one UTF-8 title per LF-delimited record and writes one result
plus LF for each record. A final input record may omit its LF. Empty stdin
means no records; a blank record is an empty title. Preserve exact output
bytes and whitespace. Support lines beyond 64 KiB. Embedded CR/LF are
outside an individual title's input contract.

Require standard-library-only Go, no external transformation interpreter,
no remaining .py files anywhere inside /workspace/repo, and preservation
of the MIT license. The reference's actual behavior is authoritative.
Explain hidden automatic partial grading with weights build=1,
no_python=1, behavior=4; no_python and behavior require a successful build.
State that speed, memory, style, and error wording are not separately scored,
while operational time limits still apply. Do not reveal hidden filenames,
answers, or fixture examples. Avoid vague requirements. Change only this file.
```

### Check

Read the instruction and compare every requirement with the intended verifier. Ask a teammate to explain what completion means using only this file. Do not leave an unstated assumption about where the executable lives or how output records are framed.

## Step 4 — Freeze original answers

### Paste into Cursor

```text
Write import-safe tests/gen.py, using a dedicated random.Random(1).
Generate exactly 2,000 unique public titles and 2,000 unique hidden titles,
with no overlap between sets. Use stable sequence ordering, never set
iteration. Mix upstream input examples, ordinary words, small-word rules,
all/mixed case, apostrophes, punctuation, slash/hyphen recursion, exact
spacing, Unicode expansions, Greek sigma, Turkish letters, combining marks,
and non-Latin text. Include empty/whitespace records and a line over 80 KiB
in each set. Do not put CR/LF inside any individual title.

Load the ORIGINAL function from environment/repo/titlecase/__init__.py.
Require its SHA-256 to equal
a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0.
Require Python 3.12 and REGEX_AVAILABLE=False. Never hand-write expected
answers: compute every expected record by calling that original function.
Write UTF-8 with explicit LF delimiters to tests/data/inputs.txt,
expected.txt, hidden_inputs.txt, and hidden_expected.txt.

Write a provenance/checksum manifest. Add scripts/check_fixtures.py to
validate hashes, record counts, unique/disjoint inputs, original-derived
answers, and two byte-identical regenerations. Parse records on LF only,
not str.splitlines() or strip(). Do not generate files on module import.
Copy only the public inputs/expected pair to environment/visible, and add
that directory to the Dockerfile at /workspace/repo/visible. Hidden data
must remain outside the agent image.
```

### Check

```bash
python3.12 -S tests/gen.py
python3.12 -S scripts/check_fixtures.py
wc -l tests/data/*.txt
mkdir -p environment/visible
cp tests/data/inputs.txt tests/data/expected.txt environment/visible/
docker build -t titlecase-go:author ./environment
```

Spot-check five actual answers independently:

```bash
PYTHONPATH=environment/repo python3.12 -S - <<'PY'
from pathlib import Path
import titlecase
assert titlecase.REGEX_AVAILABLE is False
inputs = Path('tests/data/inputs.txt').read_bytes().split(b'\n')[:-1]
expected = Path('tests/data/expected.txt').read_bytes().split(b'\n')[:-1]
for i in range(5):
    given = inputs[i].decode('utf-8')
    actual = titlecase.titlecase(given).encode('utf-8')
    assert actual == expected[i], i
    print(i + 1, repr(given), '->', repr(actual.decode('utf-8')))
PY
```

Do not edit a frozen answer to accommodate a Go implementation. Fix the implementation or a demonstrated generator defect instead.

## Step 5 — Implement the hidden verifier

### Paste into Cursor

```text
Implement tests/test.sh, the Reward Kit criteria, tests/reward.toml,
tests/Dockerfile, and task.toml for the versions pinned in the README.
Use three component keys: build, no_python, behaviour; aggregate them as
reward=(build+no_python+4*behaviour)/6 with weighted-mean aggregation.

Build=1 requires successful Go compilation, a root main package, and only
stdlib/own-module dependencies. No_python=1 requires build=1 and no .py
files anywhere in the submitted repository. Behavior is the fraction of
2,000 hidden output records whose bytes match the frozen hidden answers.
Build failure gates all components to zero. A failed candidate execution,
wrong output record count, or missing final output LF gives behavior zero.
Preserve spaces, empty records, and Unicode line separators inside records.

Run a separate verifier environment using its own Dockerfile. Transfer
/workspace/repo as the submission artifact. Preinstall pinned dependencies
at image build time so verification itself needs no network. Keep the
hidden fixtures and reward directories inaccessible to candidate code.
Use rewardkit.Worker with fresh unprivileged candidate execution and
private grading paths; do not execute a submitted program as verifier root.
Do not assume a separate container alone hides answers from its child process.

Write /logs/verifier/reward.json with all three components and reward.
Treat infrastructure failures as errors, not fabricated zero scores.
Add host-safe verifier unit checks with Worker execution mocked. Never
run the real privileged Worker boundary directly on the author workstation.
Show the expected totals for unchanged source, build with Python retained,
and a fully correct port: 0, 1/6 with zero behavior, and 1 respectively.
```

### Check

```bash
docker build -t titlecase-go:verifier ./tests
uv run --python 3.12 --with 'harbor-rewardkit==0.2.4' \
  python scripts/test_verifier.py
```

Inspect the behavior criterion to confirm it uses the hidden pair. Check `environment_mode = "separate"` and that the completed workspace is transferred. These local checks do not replace actual Harbor trial results.

## Step 6 — Implement and repair the oracle

### Paste into Cursor

```text
Write the reference Go port under solution/ and an executable
solution/solve.sh. The script must put go.mod and the Go source into
/workspace/repo, remove every .py file there, preserve LICENSE.txt, and
verify go build ./.... Do not modify environment/repo or frozen fixtures.

Implement the pinned Python function's actual branch order, recursive
slash/hyphen and Mc rules, small-word boundaries, exact whitespace,
Python-compatible Unicode classification, multi-character uppercase
expansions, and contextual lowercase sigma. Use only Go standard-library
runtime dependencies. Unicode property/case tables are acceptable; embedding
fixture inputs or expected answers is not. Avoid the default scanner limit.

Add a differential checker that prints input, expected, and actual for the
first ten mismatches against original Python, without trimming whitespace.
Fix mismatches in small batches and record concrete bugs that occurred.
Do not claim a Harbor reward until an actual completed trial provides it.
```

### Check

```bash
oracle_job="oracle-$(date -u +%Y%m%dT%H%M%SZ)"
harbor run -p . -a oracle -e docker -n 1 -k 1 \
  -o ./jobs --job-name "$oracle_job" --ek auto_mounting=false
harbor view ./jobs --port 8080
```

Inspect the trial's verifier reward and errors. The genuine oracle must earn **1.0**. If it does not, run the differential checker, feed its exact mismatches back to Cursor, and fix the Go source. Re-run Harbor after each correction. A local comparison success is not a substitute for the final oracle reward.

## Step 7 — Nop and replay negative control

### Paste into Cursor

```text
Create a literal executable cheat/solve.sh. It must create a tiny Go main
program that replays only the PUBLIC expected answers in their original
order, without implementing titlecase. Embed public answers during authoring
or copy /workspace/repo/visible/expected.txt for Go embedding. Do not read
/tests from the candidate, and do not expose hidden data to make it run.
Deliberately retain the original .py files. A compiling cheat that removes
Python already earns 2/6 and cannot meet the requested reward below 0.2.

Create or adapt scripts/run_harbor.sh to run the genuine oracle, nop, and
a separate copied task whose solution is cheat/solve.sh. Never overwrite
the canonical reference solution. Use Docker, one trial per control,
separate verification, and --ek auto_mounting=false. Preserve actual logs
and a run manifest. Add scripts/verify_evidence.py to require genuine
completed, error-free trials and consistent reward files:
oracle all scores=1; nop all scores=0; cheat build=1, no_python=0, reward<0.2.
Do not convert a crash into a passing negative control or invent evidence.
```

### Check

Choose a fresh output directory each time:

```bash
bash scripts/run_harbor.sh --output "$PWD/evidence/harbor/final"
python3 scripts/verify_evidence.py "$PWD/evidence/harbor/final"
harbor view "$PWD/evidence/harbor/final/jobs" --port 8080
```

The replay result tests one specific shortcut. It does not prove that every possible attack on the grader is prevented. If it fails the threshold, inspect the actual hidden overlap and scoring implementation; do not alter correct hidden answers merely to force a desired score.

## Step 8 — Prepare and submit actual evidence

### Paste into Cursor

```text
Prepare the submission README and final checklist using only the existing
files and genuine completed trial evidence. Include source/license/version
provenance, reproduction commands, links to the three reward files, and
places for actual oracle/nop/cheat screenshots. Exclude virtual environments,
bytecode caches, credentials, and unrelated local files from Git.

Write two short reflection lines: first, which implementation rules caused
observed mistakes; second, one fair way to make the task harder. If there is
no recorded mistake for a rule, label it anticipated difficulty instead of
claiming it occurred. Do not fabricate scores, screenshots, a GitHub URL,
a teammate review, Cursor history, or a model attempt. Leave any missing
real-world evidence explicitly pending. Use the author's chosen name.
```

### Check and hand in

Take screenshots of the **actual** three completed rewards in the viewer and store them with the submission. Confirm the real oracle remains in `solution/solve.sh`, all three required controls pass, and the reflection matches recorded observations. Follow the README's Git/GitHub commands to publish the task repository, then open its URL and confirm the task files and screenshots are visible to the reviewer.

An optional fresh-agent attempt is separate from these mandatory checks: use a fresh conversation with only the instruction and original repository, give no troubleshooting help, then grade its output and report its real score. Paid model calls or a CC Bridge are not required for the mandatory oracle, nop, and replay controls.
