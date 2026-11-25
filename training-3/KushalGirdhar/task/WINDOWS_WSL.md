# Run the submission on Windows with WSL

## 1. Set up WSL and Docker

Check your installed Linux distributions in Windows PowerShell.

```powershell
wsl --list --verbose
```

If you need one, use `wsl --install -d Ubuntu` from an elevated PowerShell and follow Windows' restart and account setup instructions. Open Docker Desktop. Select the Linux engine and enable WSL integration for your distribution under **Settings → Resources → WSL Integration**. Open the Ubuntu terminal and check that the Docker server is reachable.

```bash
docker version
docker compose version
```

The version output must include a **Server** section. Resolve an engine or permission error in your own terminal before running Harbor. See the official [WSL installation guide](https://learn.microsoft.com/windows/wsl/install) and [Docker Desktop WSL setup](https://docs.docker.com/desktop/features/wsl/).

## 2. Extract into the WSL filesystem

Install the setup utilities from Ubuntu if needed.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl unzip python3
```

Copy the ZIP from your Windows Downloads folder to WSL and unpack it. Adjust the source path if you saved it elsewhere.

```bash
mkdir -p ~/harbor-practice
cd ~/harbor-practice
cp /mnt/c/Users/KushalGirdhar/Downloads/kushal-titlecase-go.zip .
unzip kushal-titlecase-go.zip
cd kushal-titlecase-go
python3 tools/package.py verify ../kushal-titlecase-go.zip
```

## 3. Install the pinned Harbor CLI

Install uv from the official instructions, then start a new Ubuntu terminal if needed. [uv installation](https://docs.astral.sh/uv/getting-started/installation/)

```bash
uv tool install --python 3.12.14 'harbor==0.26.0'
uv tool update-shell
```

Open a new Ubuntu terminal if `harbor --version` is still unavailable. Set aside space for Docker images and saved job artifacts. Initial image pulls and installation of hash-locked verifier wheels require network access during setup and image build. Harbor runs and scores the submissions offline.

## 4. Run the three real baselines

```bash
cd ~/harbor-practice/kushal-titlecase-go
mkdir -p ../evidence
bash tools/run_harbor.sh "$(realpath ../evidence)"
```

The script creates a fresh directory for every run. It runs Harbor lint, builds the two images, checks that neither the candidate image nor the verifier's unprivileged process can open grading files, and runs oracle, nop, and visible-answer replay. At completion, it prints the reward files it read and checks oracle = 1.0, nop = 0.0, and replay < 0.2. A stopped script leaves its logs and earlier job artifacts in place.

For real screenshots, open the saved `validation.log` or the job's result view and capture each recorded reward with the Windows Snipping Tool. Name each PNG for the job and record the run directory, corresponding reward JSON path, and capture method next to it. Keep the original job logs.

## 5. Repeat the reference checks

Use CPython 3.12.14 in an environment without the optional `regex` package. Use Go 1.23.12 or the pinned Go image. The native executable checks run independently of Harbor.

```bash
cd ~/harbor-practice/kushal-titlecase-go
out="$(mktemp -d)"
uv run --no-project --python 3.12.14 python -B tests/gen.py --output "$out/first" > "$out/first.json"
uv run --no-project --python 3.12.14 python -B tests/gen.py --output "$out/second" > "$out/second.json"
diff -r "$out/first" "$out/second"
diff "$out/first.json" "$out/second.json"
diff -r "$out/first" tests/data
(cd solution/src && GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=0 go build -o "$out/titlecase" .)
uv run --no-project --python 3.12.14 python -B tools/validate_reference.py "$out/titlecase" --count 120000
```

Keep your original ZIP and validate in a separate directory before creating any new handoff archive.
