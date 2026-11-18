#!/bin/bash
# Step 7: swap the cheat in as solution/solve.sh, run the oracle, always restore the real one.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/make_cheat.py
cp solution/solve.sh /tmp/solve.sh.real
trap 'cp /tmp/solve.sh.real solution/solve.sh; echo "restored real solve.sh"' EXIT
cp cheat/solve.sh solution/solve.sh
harbor run -p . -a oracle
