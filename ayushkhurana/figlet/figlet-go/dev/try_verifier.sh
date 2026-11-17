#!/bin/bash
# Practice range for the grader: put a pretend "agent result" into a fresh room, run the REAL tests/test.sh, print the reward.
#
#   bash dev/try_verifier.sh dev/extra-cheats/peek      # a folder of files that is copied over /workspace/repo
#   bash dev/try_verifier.sh none                       # the agent did nothing (same as the nop agent)
#
# Needs Docker. Builds the room image (environment/), then runs one container as root:
# files copied in, every .py deleted, owner set to "player", then tests/test.sh exactly like the verifier does.
set -euo pipefail
cd "$(dirname "$0")/.."
what=${1:?usage: try_verifier.sh <folder|none>}
docker build -q -t figlet-room environment/ >/dev/null
ws=$(mktemp -d)
[ "$what" = none ] || cp -r "$what"/. "$ws"/
docker run --rm -u root -v "$PWD/tests:/tests-src:ro" -v "$ws:/ws:ro" figlet-room bash -c '
  cp -r /ws/. /workspace/repo/
  find /workspace/repo -type f -name "*.py" -delete
  chown -R player:player /workspace/repo
  mkdir -p /tests /logs/verifier && cp -r /tests-src/. /tests/ && rm -rf /tests/gen.py /tests/data/visible.jsonl
  bash /tests/test.sh 2>&1 | head -${LINES_SHOWN:-12}
  echo "reward.json: $(cat /logs/verifier/reward.json)"'
rm -rf "$ws"
