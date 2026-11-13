**Windows guide: understand, check, and upload the submissions**

Each ZIP is a complete Harbor task. Harbor gives another coding agent a Python repository and asks it to reproduce the behavior in Go. The package includes the instructions, grading system, and a known working solution. Kushal and Hardika have separate implementations and datasets. You should understand the work before submitting it under your name.

**1. What the files do**

| File or folder | Purpose |
|---|---|
| `README.md` | Overview, commands, recorded results, and limitations. Start here. |
| `instruction.md` | The assignment another coding agent receives. |
| `task.toml` | Harbor settings: task name, author, time limits, and container isolation. |
| `environment/` | Builds the starting workspace and contains the pinned original Python source. |
| `solution/solve.sh` | Installs the working Go solution into that workspace. |
| `solution/src/main.go` | The main Go implementation. |
| `solution/src/unicode_data.go` | Generated character and casing tables needed to reproduce Python behavior. |
| `tests/` | Builds and runs the separate grader. Checks compilation, removal of Python, and exact output. |
| `tests/data/` | Frozen visible and hidden inputs and original-Python expected outputs. Do not edit answers manually. |
| `cheat/solve.sh` | Deliberately replays visible answers to confirm hidden tests catch that approach. |
| `tools/` | Utilities for validation, data verification, stress testing, and network isolation. |
| `requirements-dev.txt` | Lists the exact Python tools needed for checking the task. |
| `evidence/` | Recorded Harbor logs, score reports, screenshots, and comparison evidence. New checks go in `evidence/reruns/`. |
| `NOTES.md` | Original behavior, tricky rules, examples, and development observations. |
| `COMPARISON.md`, `SUBMISSION_TYPES.md` | Candidate comparison, implementation approaches, and limitations of that comparison. |
| `LICENSE`, `NOTICE.md`, `licenses/` | Attribution and licensing. Keep these. |
| `SHA256SUMS.json` | File fingerprints for the delivered package. New validation files are added after delivery and are not covered by this original manifest. |
| `.gitignore` | Keeps local virtual environments, caches, and collected artifact folders out of Git. |

**2. Install Ubuntu on Windows**

Open Start, search for PowerShell, right-click it, and choose Run as administrator. Run:

```powershell
wsl --install -d Ubuntu
```

Restart Windows if requested. Open Ubuntu from Start and create its Linux username and password. The password is not displayed while typing; that is normal. If Ubuntu is already installed, use the existing installation.

Use the Ubuntu terminal for all remaining command blocks, not PowerShell.

**3. Install Docker Desktop**

Download Docker Desktop for Windows from https://docs.docker.com/desktop/setup/install/windows-install/ and install it. Start Docker Desktop and finish its setup.

In Docker Desktop settings, enable the WSL 2 engine and enable Ubuntu under Resources → WSL Integration. Apply/restart if requested. Keep Docker Desktop running.

In Ubuntu, run:

```bash
docker version
```

Both Client and Server information should appear. If only the client appears or there is a connection error, resolve Docker setup before continuing.

**4. Put the ZIPs into Ubuntu**

Download the two current ZIPs from the chat. In Ubuntu, run:

```bash
mkdir -p ~/harbor-submissions
cd ~/harbor-submissions
explorer.exe .
```

A Windows File Explorer window opens at this Ubuntu folder. Copy both downloaded ZIPs into that window. Keep their names `kushal-titlecase-go.zip` and `hardika-titlecase-go.zip`.

Back in Ubuntu:

```bash
sudo apt update
sudo apt install -y unzip curl git gh
unzip kushal-titlecase-go.zip
unzip hardika-titlecase-go.zip
```

This extracts the files on Linux and retains the script permissions.

**5. Install the Python environment manager**

Use the official uv installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv --version
```

The `source` command makes uv available in this terminal. If you open a new terminal, the installer normally arranges for uv to be available there too.

**6. Check Kushal's package**

```bash
cd ~/harbor-submissions/kushal-titlecase-go
uv venv --python 3.12.14
source .venv/bin/activate
uv pip install -r requirements-dev.txt
python tools/validate.py .
```

The first run downloads Python tools and Docker images and can take some time. You do not need to install Go separately; the containers include it.

The command performs three checks:

| Check | Meaning | Required result |
|---|---|---|
| Oracle | Runs the working solution | Reward 1.0 |
| Nop | Does no work | Reward 0.0 |
| Cheat | Replays visible answers | Reward below 0.2; expected 0.1667 |

A low cheat score is the desired result. It shows that copying visible answers does not solve the hidden cases.

The final output prints the new results directory under `evidence/reruns/`. Its `baselines.json` should contain `"passed": true`. The bundled evidence is preserved.

If a command fails, stop at that step and share the error text in the chat. Do not edit the frozen answers or the score files.

**7. Check Hardika's package**

```bash
deactivate
cd ~/harbor-submissions/hardika-titlecase-go
uv venv --python 3.12.14
source .venv/bin/activate
uv pip install -r requirements-dev.txt
python tools/validate.py .
```

Expect the same three rewards and `"passed": true` in its new results. Then run:

```bash
deactivate
```

The supplied screenshots describe the recorded cloud validation profile. Your rerun creates fresh logs for your own Docker host; it does not automatically replace those screenshots. If your trainer requires screenshots from your own run, capture the actual new score output with Windows+Shift+S and save those separately in `evidence/`.

**8. Sign into GitHub**

Create a GitHub account at https://github.com if needed. Use the account that should own the submission. In Ubuntu:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

Follow the displayed browser/device-code instructions. These commands connect Git on this computer to your GitHub account.

**9. Upload Kushal's repository**

Run the following, replacing `YOUR_EMAIL` with the email you want associated with Git commits. You may use the private commit email shown in GitHub Settings → Emails.

```bash
cd ~/harbor-submissions/kushal-titlecase-go
git init
git branch -M main
git config user.name "Kushal"
git config user.email "YOUR_EMAIL"
git add .
git status --short
```

Check that `.venv/` is not in the staged list. Then:

```bash
git commit -m "Add titlecase Harbor task and validation evidence"
gh repo create kushal-titlecase-go --private --source=. --remote=origin --push
gh repo view --web
```

This creates a private repository and opens it in the browser. If the trainer explicitly requires a public repository, use `--public` instead of `--private` in the create command. For a private repository, grant the trainer access through repository Settings → Collaborators.

At the repository's top level you should see `task.toml`, `instruction.md`, `solution/`, `tests/`, and `evidence/`. The repository should contain the extracted files, not just a ZIP.

**10. Upload Hardika's repository**

If Hardika should own the repository in a different GitHub account, repeat step 8 using that account first. Otherwise continue with the same account.

Replace `YOUR_EMAIL` again:

```bash
cd ~/harbor-submissions/hardika-titlecase-go
git init
git branch -M main
git config user.name "Hardika"
git config user.email "YOUR_EMAIL"
git add .
git status --short
git commit -m "Add titlecase Harbor task and validation evidence"
gh repo create hardika-titlecase-go --private --source=. --remote=origin --push
gh repo view --web
```

Use `--public` instead if required by the trainer. Set the GitHub owner's account through login; the Git commit name alone does not change repository ownership.

**11. Submit the two links**

Copy each repository URL from the browser and submit the corresponding link. Confirm that the trainer can open them. Read `README.md` and `NOTES.md` before presenting the work so you can explain what it does.

The two submissions tied the best observed functional result in the diagnostic audit. The audit does not prove that they outperform every candidate under every possible grading setup. Full standalone validation on your Docker host is the remaining check described above.
