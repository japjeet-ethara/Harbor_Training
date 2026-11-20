#!/bin/bash
# Re-run the 3 cheats with REAL Harbor and copy each reward.json to results/.
# Run from <YourName>/attack/ after:  cd Harbor_Training && git pull
# Needs: Docker running, harbor on PATH. Uses a scratch copy; never edits the original.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HERE/target"                       # your copy of ShashwatSuman/titlecase-go
for n in 1 2 3; do
  S="$(mktemp -d)/titlecase-go"
  cp -r "$TARGET" "$S"
  rm -rf "$S/cheat" "$S/solution"/*         # only the cheat may be in solution/
  cp "$HERE/cheat$n/solve.sh" "$S/solution/solve.sh"
  ( cd "$S" && harbor run -p . -a oracle )
  R="$(ls -dt "$S"/jobs/*/*/verifier/reward.json | head -1)"
  echo "cheat$n job folder: $(dirname "$(dirname "$(dirname "$R")")")"
  cp "$R" "$HERE/results/cheat$n-reward.json"
  cat "$HERE/results/cheat$n-reward.json"; echo
done
