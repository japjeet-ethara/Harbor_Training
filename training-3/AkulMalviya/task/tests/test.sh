#!/bin/bash
set -euo pipefail

reward=/logs/verifier/reward.txt
mkdir -p /logs/verifier
printf '0\n' > "$reward"

reject() {
  printf '%s\n' "$1" >&2
  exit 0
}

# Run the trusted checks in order so any failed gate leaves the default reward.
source /tests/checks/no_python.sh
source /tests/checks/build.sh
source /tests/checks/behaviour.sh
