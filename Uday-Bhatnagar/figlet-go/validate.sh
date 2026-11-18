#!/bin/bash
# Run from Linux/macOS/WSL with working Docker and Harbor.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p evidence jobs
docker build -t figlet-room environment/ 2>&1 | tee evidence/docker-build.txt
docker run --rm figlet-room sh -c 'whoami; pwd; ls pyfiglet/fonts | wc -l; command -v python3 || echo NO_PYTHON; command -v python || true; command -v bash; touch x && echo CAN_WRITE' | tee evidence/docker-checks.txt
harbor run -p . -a oracle -o ./jobs --job-name figlet-oracle 2>&1 | tee evidence/harbor-oracle.txt
harbor run -p . -a nop -o ./jobs --job-name figlet-nop 2>&1 | tee evidence/harbor-nop.txt
# Separate task copy keeps the real oracle intact even if the cheat run fails.
scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$scratch/figlet-go-cheat"
cp -R environment tests instruction.md task.toml "$scratch/figlet-go-cheat/"
mkdir -p "$scratch/figlet-go-cheat/solution"
cp cheat/solve.sh "$scratch/figlet-go-cheat/solution/solve.sh"
harbor run -p "$scratch/figlet-go-cheat" -a oracle -o ./jobs --job-name figlet-cheat 2>&1 | tee evidence/harbor-cheat.txt
python3 tools/check_rewards.py jobs
echo 'Capture genuine terminal screenshots of these three completed Harbor runs.'
