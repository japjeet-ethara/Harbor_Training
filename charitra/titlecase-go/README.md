# Titlecase Go — Harbor Day 3

This repository implements the practice assignment in **Day 3 — Harbor: Tasks,
Trajectories & Hardening**: port the original Python titlecase function to Go,
freeze reference answers, grade in an isolated verifier, and test a genuine
solution plus two negative controls.

## Current status

- Complete task files, original source snapshot, Go oracle, replay cheat,
  deterministic fixtures, and validation scripts are included.
- All 2,000 public and 2,000 hidden records matched the Go solution locally.
- A broader differential suite matched 1,265,238 records against the original.
- Fixture regeneration and reference-answer checks passed.
- **Real Harbor/Docker trials passed on 2026-11-11:** oracle **1.0**,
  nop **0.0**, and replay cheat **0.1673** (below 0.2), with no exceptions.
  Actual rewards and trial results are saved in `evidence/submission/`.
  All three reward screenshots are saved in `screeshot/`.
  GitHub publication and the reflection remain pending.

See `evidence/submission/RESULTS.md` for the actual Harbor scores and
`evidence/terminal-validation/harbor-run.txt` for the terminal transcript.
The latest local checks are in `evidence/terminal-validation/`;
`solution/PARITY.txt` records the earlier broader comparison.

## What completion means

| Deliverable | Required result |
| --- | --- |
| `NOTES.md` | Source URL, commit/date, MIT license, at least eight verified rules |
| `environment/Dockerfile` | Original Python source at `/workspace/repo`; Go 1.23 |
| `instruction.md` | Exact behavior, stdlib-only Go, build and no-Python requirements |
| Four fixture files | 2,000 public and 2,000 disjoint hidden input/answer pairs |
| Separate verifier | RewardKit component scores and weighted aggregate |
| Real oracle trial | All component scores and aggregate equal 1 |
| Real nop trial | All component scores and aggregate equal 0 |
| Real replay-cheat trial | Aggregate below 0.2 |
| Hand-in | GitHub URL, three real reward screenshots, two-line reflection |

The PDF asks you to direct Cursor one stage at a time. `CURSOR_PROMPTS.md`
contains that workflow. The included implementation was generated and checked
with AI assistance here; it is not a claim that a Cursor session took place.

## 1. Install the prerequisites

The commands below target **Ubuntu 24.04 with Bash**, including Ubuntu under
WSL2 when Docker Desktop integration is enabled. On Windows, run Linux commands
inside Ubuntu, not PowerShell. On macOS use Docker Desktop and a matching Go
installer; the task and run commands remain the same.

Install basic tools on Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git unzip gh
```

### Docker

If Docker Desktop already supplies a working Docker/Compose connection, skip
the Engine installation and run the verification commands below. Otherwise,
on a fresh native Ubuntu machine:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

The Docker group grants administrator-level control of Docker. Log out and
back in after adding your user, or open a new group shell with `newgrp docker`.
Do not install a second daemon inside WSL if Docker Desktop is the chosen
daemon. For an existing Docker installation with conflicting packages, follow
Docker's official upgrade/install instructions rather than replacing it blindly.

Verify as your ordinary user:

```bash
docker version
docker compose version
docker info
docker run --rm hello-world
```

Do not continue to Harbor until these commands work.

### uv, Python, Harbor and RewardKit

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

mkdir -p "$HOME/harbor-day3"
cd "$HOME/harbor-day3"
uv python install 3.12.14
uv venv --python 3.12.14 .venv
source .venv/bin/activate
uv pip install 'harbor==0.25.0' 'harbor-rewardkit==0.2.4'

python3 --version
harbor --version
```

Expected versions are Python 3.12.14 and Harbor 0.25.0. These pins reproduce
this project; they are not a claim to be the newest releases. The `oracle` and
`nop` agents need no paid model or model API key. RewardKit is installed during
the verifier image build, so the actual verifier can run without network access.

### Host Go compiler for the local parity check

The task containers already include Go. Install a matching host compiler to
use `scripts/validate_local.py`. These download checksums are from go.dev:

```bash
case "$(uname -m)" in
  x86_64)
    TASK_GO_ARCH=amd64
    TASK_GO_SHA=d3847fef834e9db11bf64e3fb34db9c04db14e068eeb064f49af747010454f90
    ;;
  aarch64|arm64)
    TASK_GO_ARCH=arm64
    TASK_GO_SHA=52ce172f96e21da53b1ae9079808560d49b02ac86cecfa457217597f9bc28ab3
    ;;
  *) echo 'Use the matching Go 1.23.12 download for your architecture.'; exit 1 ;;
esac

TASK_GO_ARCHIVE="/tmp/go1.23.12.linux-${TASK_GO_ARCH}.tar.gz"
curl -fL "https://go.dev/dl/go1.23.12.linux-${TASK_GO_ARCH}.tar.gz" \
  -o "$TASK_GO_ARCHIVE"
printf '%s  %s\n' "$TASK_GO_SHA" "$TASK_GO_ARCHIVE" | sha256sum --check
mkdir -p "$HOME/.local/opt/go1.23.12"
tar -xzf "$TASK_GO_ARCHIVE" -C "$HOME/.local/opt/go1.23.12" --strip-components=1
export PATH="$HOME/.local/opt/go1.23.12/bin:$PATH"
go version
```

These archive names are for Linux. Do not use them on macOS.

## 2. Get the prepared task

Download `titlecase-go-deliverables.zip` and place it in your Downloads folder.
Adjust that one path if your browser downloads elsewhere. Extract into the
working directory created above:

```bash
cd "$HOME/harbor-day3"
unzip "$HOME/Downloads/titlecase-go-deliverables.zip"
cd titlecase-go
chmod +x solution/solve.sh cheat/solve.sh tests/test.sh scripts/run_harbor.sh
```

The archive contains the `titlecase-go/` directory. Keep this directory as the
task root. Do not run `harbor task init` over the completed package.

If you want to rebuild the files through Cursor instead, create a separate
fresh task after installing Harbor:

```bash
cd "$HOME/harbor-day3"
mkdir -p rebuild
cd rebuild
harbor task init training/titlecase-go --no-pytest --author 'Your Name'
cd titlecase-go
```

Complete section 3 first, then use `CURSOR_PROMPTS.md` from the prepared package,
one stage at a time.
The remaining instructions assume you are in the task directory you chose.

## 3. Inspect and pin the original reference

The prepared task already contains an upstream snapshot without `.git` in
`environment/repo`. Its source is:

- URL: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: `2024-04-05T22:03:59-07:00`
- License: MIT, file `LICENSE.txt`
- Answer runtime: CPython 3.12.14, Unicode 15.0.0, stdlib `re`

For independent source inspection or a fresh reconstruction:

```bash
git clone https://github.com/ppannuto/python-titlecase.git ../python-titlecase
git -C ../python-titlecase checkout --detach 42f43e2de55bf003b286c6f8e8d8b2d26676a167
git -C ../python-titlecase log -1 --format='%H %cI'
mkdir -p environment/repo
git -C ../python-titlecase archive HEAD | tar -x -C environment/repo
```

Do not clone again if that sibling checkout already exists; inspect and use
the existing pinned checkout. `git archive` preserves the upstream files while
excluding its Git metadata. Docker cannot `COPY ../python-titlecase` from an
`environment/` build context; staging the snapshot solves that problem.

Check original examples without installing the package or optional `regex`:

```bash
PYTHONPATH=environment/repo python3 -S - <<'PY'
from titlecase import titlecase
for text in ['the lord of the rings', 'NASA AND THE MOON', "d'artagnan l'amour o'brien"]:
    print(repr(text), '->', repr(titlecase(text)))
PY
```

Read `NOTES.md` for 18 executed examples. The selected source's main patterns
do not actually use lookaround or backreferences. The hard parts include
ordering, recursion, exact spacing and Python-compatible Unicode behavior.

## 4. Check the instruction and task configuration

Read `instruction.md`. A candidate must write a root Go executable, use only
standard-library dependencies, match the reference, keep the LF record
protocol, pass `go build ./...`, and remove all `.py` files under the candidate
`/workspace/repo`. Authoring tools under `tests/` and `solution/tools/` stay
outside that candidate tree and may remain Python.

`task.toml` includes these essential settings:

```toml
schema_version = "1.4"
artifacts = ["/workspace/repo"]

[verifier]
environment_mode = "separate"
```

Keep the complete supplied config, including `[verifier.environment]`.
`tests/Dockerfile` creates a clean verifier image; it does not reinstall the
original Python repository over the candidate's solved artifact. The entire
candidate repository is passed to the verifier through `artifacts`.

Set the author before publishing (replace the value below):

```bash
export TASK_AUTHOR='Your Name'
python3 - <<'PY'
import json, os, pathlib, re
p = pathlib.Path('task.toml')
s = p.read_text()
s, n = re.subn(r'(\[\[task\.authors\]\]\s*\nname\s*=\s*)[^\n]+',
               lambda m: m.group(1) + json.dumps(os.environ['TASK_AUTHOR']), s, count=1)
assert n == 1
p.write_text(s)
PY
```

## 5. Generate and verify the fixtures

```bash
python3 -S tests/gen.py
python3 -S scripts/check_fixtures.py --report evidence/fixture-validation.json
wc -l tests/data/*.txt
mkdir -p environment/visible
cp tests/data/inputs.txt tests/data/expected.txt environment/visible/
```

Each file must contain exactly 2,000 LF records. The check recomputes every
answer with the original function, checks source/fixture hashes, verifies
unique and disjoint inputs, and compares two fresh generations byte for byte.
Expected answers must never be edited by hand. Only the public pair is copied
into the agent image. Hidden fixtures and grader code are baked into the
separate verifier image.

Some titles contain tabs, NUL or Unicode line-separator characters. Treat LF
bytes as the record separator; `str.splitlines()` would split too broadly.
The fixture sets also contain lines longer than Go Scanner's default buffer.

## 6. Inspect the rubric and validate locally

The weight sum is six:

```text
reward = (build + no_python + 4 * behaviour) / 6
```

| Case | build | no_python | behaviour | Reward |
| --- | ---: | ---: | ---: | ---: |
| Unchanged Python source | 0 | 0 | 0 | 0 |
| Delete Python, but no successful Go build | 0 | 0 | 0 | 0 |
| Builds; Python remains; all hidden answers wrong | 1 | 0 | 0 | 1/6 |
| Builds; Python removed; all hidden answers wrong | 1 | 1 | 0 | 1/3 |
| Perfect solution | 1 | 1 | 1 | 1 |

The build gate also enforces the declared stdlib-only dependency restriction.
All three criteria use a shared observation. The candidate is built and run
inside `rewardkit.Worker`, which uses a fresh unprivileged UID and keeps the
grader and answer files private. Do not execute the Worker grader as host root.

Run the safe local checks:

```bash
harbor lint . --json > evidence/harbor-lint.json
python3 scripts/test_verifier.py
python3 scripts/validate_local.py --report evidence/local-validation.json
```

The verifier helper tests trusted scoring and metadata functions; it does not
claim to exercise Docker isolation. The solution validator builds an isolated
copy of the Go files and must report 2,000/2,000 public and 2,000/2,000 hidden
matches. It also checks omitted final input LF and empty stdin. None of these
local commands substitutes for the real Harbor trials below.

For the larger, optional differential suite:

```bash
TASK_BINARY_DIR="$(mktemp -d /tmp/titlecase-check.XXXXXXXX)"
TASK_BINARY="$TASK_BINARY_DIR/titlecase"
(cd solution && GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off CGO_ENABLED=0 \
  go build -buildvcs=false -o "$TASK_BINARY" .)
python3 -S solution/tools/check_parity.py \
  --source environment/repo --binary "$TASK_BINARY" --full-unicode
rm -f "$TASK_BINARY"
rmdir "$TASK_BINARY_DIR"
```

`-buildvcs=false` is only for the host-side build, which may be nested in an
unrelated Git working tree. The actual task still checks ordinary `go build ./...`.

## 7. Build both Docker images

The supplied Dockerfiles pin these official multi-platform image indexes.
Resolution metadata is also recorded in `evidence/image-pins.json`:

| Image | SHA-256 digest |
| --- | --- |
| `golang:1.23` | `60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0` |
| `python:3.12-slim-bookworm` | `935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df` |

```bash
docker build -t titlecase-go-agent:check ./environment
docker run --rm titlecase-go-agent:check \
  sh -c 'pwd; ls /workspace/repo; go version'
docker build -t titlecase-go-verifier:check ./tests
```

The agent image must initially contain the original Python source and the
public fixtures. The verifier image installs RewardKit at build time. Both
task runtimes are configured with `network_mode = "no-network"`.

Harbor builds its own image tags for trials; these explicit builds are the
PDF's environment sanity check and may duplicate part of that work.

## 8. Run the oracle, nop and replay cheat in Harbor

From the task root:

```bash
bash scripts/run_harbor.sh --output "$PWD/evidence/harbor/final"
```

Choose a fresh output directory for each attempt. For a retry, use a new name
such as `final-02`; the script refuses to overwrite previous evidence.

The runner checks Docker, Compose and Harbor versions, creates a separate
copy for the replay control, and performs these three real trials:

```bash
harbor run -p . -a oracle -e docker -n 1 -k 1 \
  -o evidence/harbor/final/jobs --job-name oracle --ek auto_mounting=false
harbor run -p . -a nop -e docker -n 1 -k 1 \
  -o evidence/harbor/final/jobs --job-name nop --ek auto_mounting=false
harbor run -p evidence/harbor/final/task-copies/titlecase-go-replay \
  -a oracle -e docker -n 1 -k 1 \
  -o evidence/harbor/final/jobs --job-name cheat --ek auto_mounting=false
```

Those commands explain what the runner does. **Use the runner once**, not both
the runner and these manual commands in the same output directory. It creates
the replay task and run manifest that the evidence checker needs. The
canonical `solution/solve.sh` is never replaced.

The replay control in `cheat/solve.sh` embeds the public expected answers in a
tiny Go executable. It ignores stdin and deliberately retains the original
Python files. This makes `no_python = 0`. Removing Python in this control
would give it a 1/3 structural score, contradicting the requested `<0.2`.

For the included corpus, the replay outputs matched two hidden positions in
the completed Docker trial: behaviour **0.001**, aggregate **0.1673**.
See `evidence/submission/cheat/reward.json` for the actual reward file.

The runner finishes by checking actual completed trial artifacts. Required:

- Oracle: build, no_python, behaviour and reward are all exactly 1.
- Nop: all four scores are exactly 0.
- Cheat: build is 1, no_python is 0 and reward is below 0.2.
- All trials completed without infrastructure exceptions and used a separate
  Docker verifier with automatic host mounting disabled.

## 9. Inspect real results and create submission evidence

```bash
python3 scripts/verify_evidence.py "$PWD/evidence/harbor/final"
cat evidence/harbor/final/evidence-summary.json
python3 scripts/collect_submission.py "$PWD/evidence/harbor/final"
harbor view "$PWD/evidence/harbor/final/jobs" --port 8080
```

Open the local viewer URL printed by Harbor, normally http://localhost:8080.
Inspect each trial, including its verifier output and reward. Save three
actual screenshots as:

- `evidence/submission/screenshots/oracle.png`
- `evidence/submission/screenshots/nop.png`
- `evidence/submission/screenshots/cheat.png`

The collector copies the verified actual rewards, details, trial results and
run manifest, and writes `evidence/submission/RESULTS.md`. It refuses to
overwrite an existing submission directory. If you rerun, pass a new `--output`
directory and submit the evidence corresponding to the final passing task.

Add two truthful lines to `evidence/submission/REFLECTION.md`: first, which
rules actually caused mismatches during your implementation; second, one
fair way to harden the test corpus. If no mismatch history was recorded, say
that and identify the rules requiring special handling. Do not invent a
history of failed runs. `NOTES.md` contains useful, explicitly qualified text.

## 10. Publish the complete task to GitHub

Use a new repository, not an unrelated existing project. The following makes
a private repository; give your trainer access, or choose `--public` if that
is the required submission visibility and the files are ready for publication.
Keep the hidden answers private until evaluation participants have finished.

```bash
git init -b main
git config user.name 'Your Name'
git config user.email 'Your GitHub commit email'
git add .
git status --short
git commit -m "Add titlecase Go Harbor task and validated controls"

gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
gh repo create titlecase-go-harbor --private --source=. --remote=origin --push
gh repo view --web
```

The `.gitignore` omits temporary full jobs and task copies but keeps the curated
submission evidence. Add the actual GitHub URL to your hand-in. The archive
itself does not imply that a GitHub repository has already been created.

If the task is already a Git repository, skip `git init`. If the remote
repository already exists, use `git remote -v` to inspect it and push to the
correct existing remote instead of creating it again.

## Troubleshooting

| Symptom | Next action |
| --- | --- |
| Docker connection or permission error | Start the chosen daemon; verify `docker info` as the same user running Harbor |
| `docker compose` unavailable | Install/enable the Compose plugin; legacy `docker-compose` is not the checked command |
| `COPY ... not found` | Stage upstream under `environment/repo`; stage public files under `environment/visible`; build with `./environment` as context |
| Fixture Python/Unicode mismatch | Activate the pinned Python 3.12.14 environment and regenerate with `-S` |
| Missing `regex` or changed reference answers | Do not install `regex`; this benchmark intentionally fixes stdlib `re` |
| Oracle below 1 | Read grade-details/build status; reproduce local differences; repair source, then rerun all controls in a new directory |
| Nop above 0 | Inspect build gating; `no_python` must never pay when the Go build fails |
| Replay at least 1/3 | Verify the negative control retains original `.py` files |
| Replay unexpectedly high | Confirm grading reads the hidden pair, not public answers, and public/hidden input sets are disjoint |
| Missing reward file or Worker setup error | Treat it as infrastructure failure, not a score; inspect verifier logs and use the supplied dedicated Docker verifier |
| Container source still contains Python after oracle | Check clean verifier image and top-level artifact transfer; do not bake original source into the verifier |
| Windows changed fixture bytes | Preserve `.gitattributes`; regenerate with pinned Python and compare hashes |

## Final checklist

- [ ] Source/license and rule examples inspected.
- [ ] Instruction matches the grader.
- [x] Both Docker images build.
- [x] Four fixture files have 2,000 records and deterministic hashes.
- [x] Public and hidden input sets are disjoint.
- [x] Local Go comparison passes both complete corpora.
- [x] Real Harbor oracle = 1.0.
- [x] Real Harbor nop = 0.0.
- [x] Real Harbor replay cheat < 0.2.
- [x] Actual trial artifacts included.
- [x] Three reward screenshots included in `screeshot/`.
- [ ] Two-line reflection describes real work.
- [ ] GitHub repository accessible to the reviewer.

## Primary references

- [Upstream source at the frozen commit](https://github.com/ppannuto/python-titlecase/tree/42f43e2de55bf003b286c6f8e8d8b2d26676a167)
- [Harbor installation](https://docs.harborframework.com/getting-started/installation)
- [Separate verifier](https://docs.harborframework.com/tasks/separate-verifier)
- [Artifact transfer](https://docs.harborframework.com/tasks/artifacts)
- [RewardKit](https://docs.harborframework.com/rewardkit/quick-start)
- [Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [uv installation](https://docs.astral.sh/uv/getting-started/installation/)
- [Official Go downloads and checksums](https://go.dev/dl/)
- [GitHub CLI repository creation](https://cli.github.com/manual/gh_repo_create)
