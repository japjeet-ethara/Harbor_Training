import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runs = sorted(p for p in (ROOT / 'evidence/harbor').iterdir() if (p / 'summary.json').is_file())
assert runs, 'No successful complete Harbor baseline run exists'
run = runs[-1]
summary = json.loads((run / 'summary.json').read_text())
assert summary['oracle']['reward'] == 1.0
assert summary['nop']['reward'] == 0.0
assert summary['replay-cheat']['reward'] < .2
rel = run.relative_to(ROOT).as_posix()
reruns = ROOT / 'evidence/reruns'


def latest(label):
    choices = sorted(p for p in reruns.iterdir() if p.name.endswith('-' + label))
    assert choices, label
    path = choices[-1]
    command = json.loads((path / 'command.json').read_text())
    assert command['exit_code'] == 0, (label, command)
    return path.relative_to(ROOT).as_posix() + '/terminal.log'


verification = latest('final-reference-and-go-validation')
grader = latest('grader-integration')
unit = latest('grader-unit-tests')
standalone = latest('shipped-standalone-oracle')
notes = latest('checked-notes')
lint = rel + '/lint.json'
assert json.loads((ROOT / lint).read_text()) == []
oracle = rel + '/' + summary['oracle']['reward_file']
nop = rel + '/' + summary['nop']['reward_file']
cheat = rel + '/' + summary['replay-cheat']['reward_file']

text = f'''# Validation results

Author: Komal. Validation date: 18 November 2026 (Asia/Kolkata). Evidence directories use UTC timestamps.

| Measurement | Actual result | Raw evidence |
| --- | --- | --- |
| Genuine Harbor oracle | 1.0; checks 1/1/1; 2000/2000 hidden matches | [{oracle}]({oracle}) |
| Genuine Harbor nop | 0.0; checks 0/0/0 | [{nop}]({nop}) |
| Genuine Harbor visible replay | {summary['replay-cheat']['reward']}; checks 1/0/0 | [{cheat}]({cheat}) |
| Harbor lint, all available rules | zero findings | [{lint}]({lint}) |
| Dataset regeneration twice | six generated files identical to each other and frozen copies | [{verification}]({verification}) |
| Frozen answers re-executed against original | 4000/4000 exact | same verification log |
| Go visible / hidden byte comparison | 2000/2000 and 2000/2000 | same verification log |
| Independent differential stress | 110000 distinct records, zero mismatches | same verification log |
| Direct pattern results vs Python | 61416 match/search fixtures passed | same verification log |
| Rule examples and line protocol | 36 original-generated examples; protocol unit tests passed | same verification log |
| Unicode regeneration | exact table SHA-256 f204de0275892f9c3af515a6fa3506ae539a19112316c0e8e3a1085365c82ea7 | same verification log |
| Go build, tests, vet | passed in Go 1.23.12 Linux container | same verification log |
| Scoring byte/framing unit tests | 3 tests passed | [{unit}]({unit}) |
| Real grader gating, bounds and isolation | 5 integration assertions passed | [{grader}]({grader}) |
| Standalone shipped agent image and oracle | built and ran; all Go tests passed | [{standalone}]({standalone}) |
| Checked NOTES examples | 36 re-executed | [{notes}]({notes}) |

All baseline job configurations, locks, trial logs, per-check diagnostics, and verifier stdout/stderr are under `{rel}`. `summary.json` was produced by reading actual Harbor reward files and asserting the three measured thresholds. RewardKit serializes rewards to four decimal places: the unchanged weighted mean 1/6 is written as 0.1667. The summary assertion was corrected to compare this documented serialization precision. The real solution installer hashes before and after replay match. Replay ran in a temporary task copy; its program embeds only the frozen visible output and retains original Python source. Its hidden behaviour score is zero. No additional hidden-hit gate modifies build credit.

The original snapshot is byte-identical to the pinned Git blobs; see `evidence/upstream-identity.json`. Windows Git initially converted checkout newlines; the shipped snapshot was restored from exact Git blob bytes, then all frozen answers and differential checks were rerun. The reference loader now enforces the source hash as well as runtime and optional-package state.

Runtime: Go 1.23.12 linux/amd64; CPython 3.12.8; Unicode 15.0.0; optional regex absent in the reference. Harbor 0.26.0 runs under Ubuntu WSL 2 using Docker Desktop 4.99.0 / Engine 29.9.3 and Compose 5.7.0. Agent and verifier images derive from the shipped digest-pinned `golang:1.23` and `python:3.12.8-slim` stages. Full verifier dependency versions are in `tests/requirements.lock`; actual image-build logs are in the dated reruns. The verifier's dependency graph includes regex, but it never runs the reference source.

The shipped Dockerfiles were actually built. The standalone agent image and its oracle were tested separately from Harbor. No alternative runtime profile, memory override, or shared-verifier fallback was used. The host Windows Go 1.26.6 installation failed to find its linker in initial exploration; it was not used as the validation toolchain.

Screenshots in `evidence/screenshots/` are genuine browser captures of a local Linux PTY served by ttyd 1.7.7. The PTY executes `tools/show_terminal.py`, which reads the saved Harbor rewards and check values from a read-only evidence mount. Windows Terminal was not exposed by the native capture inventory, so this capture-only fallback was used. It does not change the task runtime profile. These are post-run terminal views, not synthesized terminal images or claims to capture the whole development session. Their source files remain in the raw Harbor evidence; the Dockerfile, display script, capture manifest and server logs are retained.

## Failures retained

Dated failed runs remain alongside successful reruns. Initial issues were a missing uv-tools PATH, a hosted-only CLI flag, generator path initialization during RewardKit discovery, an overly small build-file bound, and a CRLF shebang in the generated replay installer. After all three final Harbor trials succeeded, an overly strict summary assertion failed on RewardKit's four-decimal serialization; the assertion was corrected and rerun against the unchanged genuine rewards. The underlying causes were corrected. These attempts are not counted as passes. Each rerun has its own commands and logs; no reward file was edited to change a result.

The ZIP packaging report records integrity, executable modes, included-file hashes, and excluded generated artifacts. Candidate artifact trees collected by Harbor are redundant with shipped source and are omitted from the distribution; their collection manifests remain. Compiled replay programs, caches, virtual environments, and credentials are not included.

## Limits and unverified scope

Finite differential testing is not a proof for every possible string. The restricted VM intentionally excludes unused regex features and empty-match substitution. The supported record protocol is well-formed UTF-8 scalar text with LF or CRLF delimiters; malformed UTF-8 and surrogate-containing Python strings are outside that protocol. Default function behaviour is implemented; callbacks, custom small-word lists, CLI home-directory wordlists and non-default options are outside the task. Deeply adversarial patterns or enormous recursive compounds are not performance benchmarks.

No optional fresh model-agent attempt, human teammate review, publication, or GitHub push was performed. No external publication destination was authorized. All requested local validation categories are measured above; there is no claim of exhaustive correctness or kernel-level sandbox hardening.
'''
(ROOT / 'VALIDATION.md').write_text(text, encoding='utf-8')

rows = [
('Task 1, section 18; do not apply FIGlet rules', 'instruction.md, GRADING.md', 'Section 18 was read before implementation; weights and baselines below have no hidden-hit gate'),
('Author Komal; no invented surname/email/GitHub; disclose AI', 'README.md, ATTRIBUTION.md, task.toml', 'Only name Komal is assigned; upstream identities remain attributed separately'),
('Fresh submission; no previous code, graders, data, docs or tables', 'ATTRIBUTION.md and new source/tool files', 'Original implementations authored in this session; only four necessary upstream files copied'),
('Pinned original source read; retain license/attribution; disclose overlap', 'environment/repo, solution/LICENSE.txt, NOTICE, licenses/', 'evidence/upstream-identity.json; exact Git blob byte comparison'),
('Small internal pattern representation; restricted engine', 'internal/pattern/pattern.go, PATTERN_ENGINE.md', verification),
('Generic character classes, sequence, ordered alternatives, repetition', 'Node data, compiler and consume/split/jump interpreter', '61416 direct Python fixtures plus generic ordered/greedy/lazy/backtracking tests'),
('Captures, anchors and boundary assertions', 'save and assertion instructions; value-copied capture positions', 'Python fixture spans/groups; rollback, dollar/strict-end and Unicode-boundary tests'),
('Original patterns represented as data', 'internal/format/patterns.go', 'Direct fixtures for every named titlecase pattern and consonants'),
('Pattern execution separate from transformations', 'pattern and format packages', 'VM only recognizes spans; formatter performs casing/substitution callbacks; tests passed'),
('Original transformation order; no direct rune pipeline/Go regex/format stack', 'internal/format/titlecase.go', '36 reference examples, 4000 frozen records and 110000 independent cases passed; source inspection'),
('Separate record handling, Unicode, matching and formatting', 'internal/records, pyunicode, pattern, format', 'Separate packages compile/test; protocol unit tests'),
('Ordered alternatives, greediness, capture bounds, positions, non-overlap', 'VM branch order, save, Match/Search/Replace', 'Direct Python ambiguous fixtures plus generic non-overlap and capture rollback tests'),
('Validate ambiguous patterns directly with Python before integration', 'tools/gen_patterns.py and patterns_test.go', 'evidence/pattern-tests-initial.log precedes recorded integration runs'),
('Go standard library only; go build ./... passes', 'go.mod and Go imports; no third-party modules', verification + '; genuine oracle build_result returncode=0'),
('Pin reference runtime, Unicode and optional regex state', 'tools/reference.py; digest-pinned Docker stages', verification + '; source hash, CPython 3.12.8, Unicode 15.0.0, regex absent asserted'),
('Do not assume Go Unicode casing/folding/boundaries', 'fresh JSON tables and pyunicode package', 'All scalar properties/mappings generated by Python; no Go unicode/regexp package used'),
('Reproducible compatibility-data generation', 'tools/gen_unicode.py', verification + '; fresh table hash matched'),
('Original public-service, sports, community, everyday corpus', 'tests/gen.py SEEDS', 'coverage.json domain counts; 24 original templates; DATASET.md'),
('Documented rule matrix and original seeds', 'DATASET.md; tests/gen.py', 'Full seed inventory in code; matrix linked to tags and checked examples'),
('Deterministic punctuation/casing/separator/name/boundary/compound mutations', 'tests/gen.py', 'coverage.json and records.json; regeneration hash equality'),
('Deliberate multi-rule interactions', 'paired topics, subphrases, casing, named compounds', '851 visible and 829 hidden tagged interaction records'),
('Use random.seed(1)', 'tests/gen.py build()', 'Explicit seed call and twice-identical generation'),
('Exactly 2000 visible and 2000 different hidden inputs', 'tests/data/inputs.txt, hidden_inputs.txt', verification + '; byte-LF counts 2000 each; input overlap 0'),
('Required frozen expected filenames and counts', 'tests/data/expected.txt, hidden_expected.txt', verification + '; 2000 each and original execution exact'),
('Apostrophe/Mc names, honorifics, dotted initials, internal caps, consonants', 'NAMES, TOPICS, DIRECTED and checked examples', 'coverage matrix and actual per-split counts in coverage.json'),
('Small words, slash/hyphen compounds and subphrases', 'TOPICS plus mutations', 'small/slash/hyphen/nested/subphrase counts; direct reference checks'),
('Unicode expansions, context, combining marks and unusual whitespace', 'Unicode/combining/context/boundary topics; 14 separator choices', 'Frozen/direct examples and independent Unicode stress; whitespace preserved bytewise'),
('Every frozen answer executed by original; never manual/Go answer key', 'tests/gen.py add() calls ref.titlecase', verification + '; all 4000 answers independently re-executed'),
('Input disjointness; measure/avoid output overlap; no meaningless IDs', 'global duplicate input/output rejection before split', 'coverage.json input_overlap=0/output_overlap=0; meaningful seed slots only'),
('Check any metamorphic property against reference before use', 'DATASET.md', 'No metamorphic property used; every expected answer executes original'),
('Candidate path /workspace/repo; pinned golang:1.23 and original source', 'environment/Dockerfile and artifact declaration', standalone + '; Harbor artifact transfer and oracle build passed'),
('No .py in completed candidate; removal conditioned on build', 'solution/solve.sh and independent _grader.py', 'Oracle checks build=1/no_python=1; deletion-only integration probe scores 0'),
('Exact default titlecase for each record', 'format.Titlecase, records.Run', verification + '; exact bytes on both frozen corpora and stress'),
('Separate agent/verifier; protect hidden inputs and answers', 'task.toml; distinct Dockerfiles; root-only /tests', grader + '; runner cannot read hidden answers; agent image only original source'),
('RewardKit weighted mean build 1/no_python 1/behaviour 4', 'tests/checks.py and reward.toml', 'Raw reward-details.json and checks.json; actual baseline scores'),
('Behaviour uses hidden corpus; reward.json at required path', 'tests/_grader.py, tests/test.sh', oracle),
('No FIGlet at-least-one-hidden-answer gate', 'Independent checks with unchanged weighted mean', cheat + '; build=1, no_python=0, behaviour=0, reward=1/6'),
('Independent grader; explicit outcomes/exact bytes/diagnostics/bounds', 'tests/_grader.py and GRADING.md', unit + '; ' + grader + '; raw mismatches and return codes in baseline logs'),
('Preinstall verifier dependencies', 'tests/Dockerfile and requirements.lock', 'Actual image-build logs; offline runtime; no runtime install; lint []'),
('Precise instruction.md covering graded contract; hide answer material', 'instruction.md and environment build context', 'No corpus examples or answer files in instruction/agent image; artifact contract declared'),
('solve.sh installs Go and removes original Python', 'solution/solve.sh', standalone + '; oracle 1.0'),
('Visible-answer replay without implementing titlecase; retain Python', 'cheat/solve.sh and visible-output.txt', cheat + '; retained titlecase/__init__.py, build-only reward'),
('Cheat uses temporary task copy; preserve real solution', 'tools/harbor_runs.sh', rel + '/commands.log and equal real-solution-before/after.sha256'),
('Regenerate twice with matching hashes', 'tools/verify.py', verification),
('Check every frozen answer against original', 'tools/verify.py', verification),
('Exact visible/hidden corpus agreement', 'tools/verify.py', verification),
('At least 100000 independently generated stress cases', 'separate stress grammar in tools/verify.py', verification + '; 110000 distinct; zero mismatches; hashes logged'),
('Meaningful interpreter, precedence, protocol and scoring tests', 'Go tests, test_grader.py, grader_integration.py', verification + '; ' + unit + '; ' + grader),
('Genuine Harbor oracle/nop/replay runs', 'tools/harbor_runs.sh; Harbor 0.26.0', rel + '/summary.json and raw job/trial files'),
('Applicable Harbor lint checks', 'harbor lint --select ALL --json', lint + '; []'),
('Oracle 1.0; nop 0.0; replay below .2', 'RewardKit unchanged weighted-mean checks', rel + '/summary.json: 1.0 / 0.0 / 0.1667 (RewardKit serializes 1/6 to four decimals)'),
('Fix underlying failures and rerun; do not fabricate passes', 'VALIDATION.md; separate dated failure/rerun logs', 'Actual PATH/CLI/discovery/file-limit/shebang failures retained; successful run has no exceptions'),
('Actual commands, versions, configs, raw logs and rewards', 'evidence/reruns and evidence/harbor', 'command.json, terminal.log, Harbor config/lock/result files, checks/reward/details'),
('Genuine terminal screenshots; no synthesized images/history', 'tools/Dockerfile.terminal, show_terminal.py; evidence/screenshots', 'Browser screenshots of a real local Linux PTY showing read-only saved rewards; raw source files and capture manifest retained'),
('Actually build/test shipped Docker environment; disclose alternatives', 'Digest-pinned agent/verifier Dockerfiles', standalone + '; actual standalone and Harbor builds; no alternative profile'),
('README, checked NOTES, engine design, coverage/repro reports', 'README.md, NOTES.md, PATTERN_ENGINE.md, DATASET.md, VALIDATION.md', notes + '; documentation references actual raw evidence'),
('Licenses/attribution and beginner Windows/WSL instructions', 'LICENSE, ATTRIBUTION.md, licenses/, WINDOWS_WSL.md', 'Full upstream/CPython/Unicode notices retained; executable setup commands documented'),
('Known limitations; no unfinished check called passed', 'VALIDATION.md and PATTERN_ENGINE.md', 'Finite-test/default-option/UTF-8/optional-model scope stated explicitly'),
('Readable idiomatic code; no explanatory comments', 'gofmt-formatted Go; explanations in Markdown', 'go vet/tests passed; only required go:embed directives and preserved upstream comments/notices remain'),
('ZIP includes source/tests/frozen data/docs/licenses/evidence', 'tools/package.py and ZIP inventory', 'Packaging report and SHA256SUMS.json'),
('Preserve script modes; archive integrity; exclude secrets/caches/venvs/binaries', 'tools/package.py', 'ZIP CRC, extraction/hash/mode checks; excluded collected artifact trees listed'),
('Validation reruns saved separately', 'Timestamped evidence/reruns and evidence/harbor directories', 'Earlier failed attempts and final success have distinct directories'),
('Do not publish/push without destination; never force-push', 'Local-only delivery', 'No publication or push command executed; section 18 GitHub hand-in superseded by explicit user instruction'),
]
acceptance = '# Acceptance mapping\n\nAuthor: Komal. Evidence is from actual execution, not planned checks. Paths are relative to this authoring bundle. Packaging and screenshot artifacts are included and independently listed in the final packaging report.\n\n| Mandatory requirement | Implementation | Actual verification evidence |\n| --- | --- | --- |\n'
for row in rows:
    acceptance += '| ' + ' | '.join(part.replace('|', '\\|') for part in row) + ' |\n'
(ROOT / 'ACCEPTANCE.md').write_text(acceptance, encoding='utf-8')
print(f'Wrote VALIDATION.md and ACCEPTANCE.md from {rel}; {len(rows)} requirement mappings')
