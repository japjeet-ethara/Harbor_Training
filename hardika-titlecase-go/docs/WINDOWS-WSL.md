# Run the task on Windows with WSL 2

1. In Windows, open PowerShell. If WSL is missing, run `wsl --install -d Ubuntu`. Follow the Windows prompts and restart if requested. Launch Ubuntu and complete its first-run setup.
2. Open Docker Desktop, enable its WSL 2 engine and enable integration for your Ubuntu distribution. In Ubuntu, run `docker version` and `docker compose version`. The Docker version output should include both Client and Server.
3. Extract the ZIP, then copy the extracted folder to your Linux home directory. For example, use the actual extraction path in place of the one below. Working under your Linux home keeps the tools on the same filesystem.

   ```bash
   cp -r "/mnt/c/Users/YOURNAME/Downloads/hardika-titlecase-go" ~/hardika-titlecase-go
   cd ~/hardika-titlecase-go
   ```

4. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) in Ubuntu. Set up Harbor in a virtual environment.

   ```bash
   uv python install 3.12.14
   uv venv --python 3.12.14
   source .venv/bin/activate
   uv pip install 'harbor==0.26.0' 'regex==2026.11.15'
   harbor --version
   ```

5. Run `bash tools/run_harbor.sh`. The builds need network access to fetch the pinned images and wheels. The jobs run offline. Inspect each job’s `result.json` and its trial’s `verifier/reward.json`. Capture the reward in a screenshot if recording a new run.
6. To run the independent reference checks, also install Go 1.23.12 from the [Go downloads archive](https://go.dev/dl/) and put it on your shell’s PATH. Then run `bash tools/validate.sh`.

If Docker reports permission denied, first verify Ubuntu integration from Docker Desktop and check whether `docker version` shows a server from the Ubuntu terminal. A managed shell may have different engine access from your interactive Ubuntu terminal. Harbor logs build or environment setup failures in the corresponding job directory.
