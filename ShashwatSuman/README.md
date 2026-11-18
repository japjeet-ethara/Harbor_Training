# Harbor Day 3 practice task: titlecase-go (Windows guide)

This folder contains the finished practice task from the Day 3 PDF (section 18),
plus everything needed to run it on this Windows PC.

```
harbor-practice\
├── README.md            ← this guide
├── NOTES.md             ← Step 1: SHA, licence, 14 rules with checked examples
├── python-titlecase\    ← the original repo (git clone)
├── titlecase-go\        ← the full Go port Harbor task (Section 18 practice task)
│   ├── instruction.md   task.toml   README.md
│   ├── environment\     Dockerfile, copy of the repo, visible examples
│   ├── solution\        solve.sh + main.go  (the oracle: Go port)
│   ├── tests\           Dockerfile, test.sh, build.py, no_python.py, behaviour.py, reward.toml, data\
│   ├── tools\           gen.py (makes answer sheets), compare.py (shows wrong lines)
│   └── cheat\           solve.sh (the cheat for Step 7)
└── sample-task\         ← sample log-analyzer task (compact, hardened, instant local verifier)
    ├── instruction.md   task.toml   README.md
    ├── environment\     Dockerfile, sample.log
    ├── solution\        solve.sh + log_analyzer.py (Oracle = 1.0)
    ├── cheat\           solve.sh (Cheat <= 0.20)
    ├── tests\           test.sh, Dockerfile, reward.toml, test_cli.py, test_std_lib.py, test_behaviour.py, data\
    └── verify_local.py  ← offline benchmark (tests Oracle=1.0, Nop=0.0, Cheat<=0.20 on Windows)
```

---

## Part 1: Software

### Already installed on this PC

| Tool | Version | Why |
|---|---|---|
| Git | 2.56 | clone / push |
| uv | 0.13.9 | runs Python and Python tools |
| Python 3.12 (via uv) | 3.12.16 | Harbor and the original titlecase code |
| Harbor | 0.26.0 | runs the task (`harbor` command) |
| Go | 1.27.4 | build and test the Go port on Windows |
| GitHub CLI | 2.104.0 | `gh` for the final push |

Open a **new** PowerShell window so it picks up the new PATH, then check:

```bash
git --version; uv --version; go version; gh --version; harbor --version
```

> Harbor was installed with `uv tool install --python 3.12 harbor`. The plain
> `uv tool install harbor` fails on this PC because the default Python is 3.15,
> which has no prebuilt packages yet (`pyyaml` tries to compile and needs Visual C++).

### You still need to do these yourself

These need administrator rights, a restart or a sign-up, so I did not do them for you.

**1. Turn on UTF-8 for Python (one command).** Without it, `harbor lint` and
other commands crash on Windows with `UnicodeDecodeError`:

```bash
setx PYTHONUTF8 1
```

Then close PowerShell and open it again.

**2. Install WSL 2 (Docker Desktop needs it).** Right-click Start, open
**Terminal (Admin)**, run the command below, then restart the PC:

```bash
wsl --install
```

**3. Install Docker Desktop.** Download it from
https://docs.docker.com/desktop/setup/install/windows-install/ , run the installer
and keep "Use WSL 2" ticked. Start Docker Desktop and wait until it says
**Engine running**. Check:

```bash
docker run hello-world
```

It should print "Hello from Docker!". **Docker Desktop must be open whenever you run `harbor run`.**

**4. Log in to GitHub (for Step 8):**

```bash
gh auth login
```

Choose GitHub.com → HTTPS → Login with a web browser.

**5. Cursor (optional now).** All the code is already written, but the PDF
expects you to direct the Cursor agent. Download it from https://cursor.com, then use
File → Open Folder → `harbor-practice\titlecase-go` and press **Ctrl+L**.

---

## Part 2: The task, step by step

Every command below runs in PowerShell from the `harbor-practice` folder:

```bash
cd $HOME\Desktop\Shashwat_Suman\harbor-practice
```

### Step 1: Understand the repo (done → `NOTES.md`)

`NOTES.md` has the URL, the SHA `42f43e2de55bf003b286c6f8e8d8b2d26676a167`,
the MIT licence and 14 rules, each with an example produced by the real code.
To get the SHA yourself:

```bash
git -C python-titlecase log -1 --format='%H %cI'
```

**Important finding:** the library needs the `regex` package to behave as
designed. Without it, it silently falls back to `re` and gives different
answers. So always run it with `--with regex==2026.11.18`.

### Step 2: Task folder and Dockerfile (done)

It was created with `harbor task init titlecase-go --org my-org --author "Shashwat Suman"`.
`environment/Dockerfile` starts from `golang:1.23` (pinned to an exact digest),
adds `python3` + `python3-regex`, copies the repo to `/workspace/repo` (no `.git`)
and the examples to `/workspace/examples`, and runs the agent as the non-root user `agent`.

Check it once Docker is running:

```bash
docker build -t titlecase-go-env titlecase-go\environment
```

```bash
docker run --rm titlecase-go-env ls /workspace/repo
```

### Step 3: `instruction.md` (done)

It covers the goal (a Go program, stdin → stdout, one line per line), the hard
rules (standard library only, `go build ./...`, no `.py` left), the behaviour
(byte for byte, the input alphabet), what is not checked, and how it is graded.
It never mentions the tests or the hidden answers. Every rule in it is checked by a test.

### Step 4: Inputs and frozen answers (done)

```bash
cd titlecase-go
```

```bash
uv run --no-project --python 3.12 --with regex==2026.11.18 python tools/gen.py
```

This uses `random.seed(1)`, so it gives the same output on every run. It writes 2000 visible and 2000 different hidden
titles, then runs the **original** Python on each one. On this PC: running it twice gave
identical files, and all four files have 2000 lines.

`gen.py` lives in `tools/`, not `tests/`. Reward Kit treats **every** `.py` in
`tests/` as a scoring check, and the agent must never see the generator.

### Step 5: Tests (done)

There are three Reward Kit checks, combined with a weighted mean (`tests/reward.toml`):

| Check | Weight | Score |
|---|---|---|
| `build.py` | 1 | `go build -o <tmp>/ ./...` passes and `go.mod` has no `require` |
| `no_python.py` | 1 | no `.py` files **and** the build passes (so deleting files alone earns nothing) |
| `behaviour.py` | 4 | share of the **hidden** titles that are exactly right |

Expected: nothing done = 0, build only = (1+0+0)/6 ≈ 0.17, perfect = 1.
The verifier runs in its own container (`environment_mode = "separate"`), with
Reward Kit pre-installed and no network.

### Step 6: Solution / oracle (done, verified locally)

`solution/main.go` is a full Go port that uses no regular expressions at all: every
Python pattern is rewritten as plain character checks. Check it on Windows,
without Docker:

```bash
New-Item -ItemType Directory -Force $env:TEMP\tc | Out-Null; Copy-Item solution\main.go $env:TEMP\tc\; Set-Content $env:TEMP\tc\go.mod "module titlecase`n`ngo 1.23" -Encoding ascii; go -C $env:TEMP\tc build -o titlecase.exe .
```

```bash
python tools/compare.py $env:TEMP\tc\titlecase.exe tests/data/hidden_inputs.txt tests/data/hidden_expected.txt
```

This must print `2000/2000 lines match`. Then the real Harbor run (Docker must be open):

```bash
harbor run -p . -a oracle -o ../jobs
```

**Expected reward: 1.0.**

### Step 7: Nop and cheat checks

```bash
harbor run -p . -a nop -o ../jobs
```

**Expected: 0.0.** Now the cheat. Swap it in, run, and put the real solution back:

```bash
Copy-Item solution\solve.sh solution\solve.sh.real; Copy-Item cheat\solve.sh solution\solve.sh
```

```bash
harbor run -p . -a oracle -o ../jobs
```

```bash
Move-Item -Force solution\solve.sh.real solution\solve.sh
```

**Expected: 0.17** (below 0.2). The cheat builds and keeps the `.py` files, but
it has never seen the hidden titles.

Real Harbor runs on this PC (Docker, 18 Nov 2026): oracle 1.0, nop 0.0, cheat 0.1667. Jobs are in the `jobs` folder next to `titlecase-go` (oracle-2, nop, cheat).

See the results in the browser (http://127.0.0.1:8080):

```bash
harbor view ../jobs
```

### Step 8: Hand in

```bash
git init; git add .; git commit -m "titlecase-go Harbor task"
```

```bash
gh repo create titlecase-go --private --source . --push
```

Add screenshots of the three rewards from `harbor view`. Your two lines:

1. *Rules the agent got wrong most:* Python's full Unicode upper-casing (`ß` → `SS`),
   the case-sensitive SUBPHRASE rule with no word boundary (`title: android` → `Title: Android`),
   and the lazy punctuation prefix in UC_ELSEWHERE.
2. *To make it harder:* the cheat scores 0.33 if it also deletes the `.py` files.
   Gate `build`/`no_python` on `behaviour` ≥ 0.5, and add more rare Unicode in the hidden set.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `harbor: command not found` | Open a new PowerShell. If it is still missing, run `uv tool update-shell` and reopen. |
| `UnicodeDecodeError` from harbor | Run `setx PYTHONUTF8 1` and reopen PowerShell. |
| `Docker is not installed or not on PATH` | Install / start Docker Desktop (Part 1, steps 2–3). |
| `failed to connect to the docker API` | Docker Desktop is not running. Open it and wait for "Engine running". |
| Error about the network policy / egress control | Temporarily set `[agent] network_mode = "public"` in `task.toml`, then report it. |
| `bash\r: No such file` in a run | A `.sh` file got Windows line endings. `.gitattributes` forces LF; re-checkout or re-save it as LF. |
| Oracle below 1.0 | Run `tools/compare.py` (Step 6) to see the wrong lines. Below 1.0 means the task is broken, not hard. |
