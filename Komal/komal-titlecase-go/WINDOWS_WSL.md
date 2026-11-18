# Beginner Windows / WSL instructions

1. Install Docker Desktop with Linux containers and Ubuntu under WSL 2. Open Docker Desktop and enable its Ubuntu WSL integration. Reboot if the installers request it. Open the Ubuntu application from Start. These are setup steps for the user, not changes performed by this bundle.
2. In Ubuntu, run `docker version`. Both Client and Server should appear. Run `docker compose version`. If Docker cannot connect, start Docker Desktop before continuing.
3. Extract `komal-titlecase-go.zip`. Prefer a folder in your Ubuntu home directory, such as `~/komal-titlecase-go`, rather than a Windows mount. Use a Linux unzip tool if possible: `unzip /mnt/c/Users/YOUR_WINDOWS_USER/Downloads/komal-titlecase-go.zip -d ~/`. Replace the Windows path with the actual location. Unix executable permissions are stored in the ZIP.
4. Enter the extracted folder. Run `chmod +x titlecase-go/solution/solve.sh titlecase-go/tests/test.sh titlecase-go/cheat/solve.sh tools/harbor_runs.sh` if your extractor discarded those permissions.
5. Install `uv` using its official installation instructions if it is unavailable, then run `uv tool install harbor==0.26.0`. Add `~/.local/bin` to PATH or open a new Ubuntu terminal. Check `harbor --version`.
6. Run `harbor lint titlecase-go --select ALL --json`. An empty JSON array means no findings. Run `bash tools/harbor_runs.sh`. The first run downloads pinned Docker base images and installs the locked grader dependencies during image build. This needs internet access. The actual candidate and verifier phases run without network access.
7. Read the printed rewards and the new `evidence/harbor/<UTC timestamp>/summary.json`. Individual trial folders contain `verifier/reward.json`, `checks.json`, raw stdout/stderr, and Harbor configuration. Oracle should be 1, nop 0, and replay 1/6, which is below 0.2. A Harbor exception is not a zero or a pass; inspect its `exception.txt` and verifier output.

The replay script copies the task to a temporary directory. It preserves the original installer, and compares the original installer hash before and after the replay run. Do not replace the real solution manually.

For full independent checking, run the two Docker validation commands from README. This avoids needing Go or the reference Python version installed on Windows. A direct Windows Go build is optional and was not the validated toolchain in this submission. The tested toolchain is Go 1.23.12 inside the shipped Linux Docker profile, hosted by Docker Desktop through Ubuntu WSL 2.

Titles are UTF-8. To avoid PowerShell encoding and newline transformations, run protocol checks from Ubuntu or use the supplied byte-preserving verification script. Do not use `Get-Content` to count records containing unusual Unicode line separators; the dataset is delimited by byte LF only.

No GitHub account is needed. Publishing is a separate action requiring an explicit destination and authorization.
