#!/bin/bash
# Run from <YourName>/ . Needs attack/target/ (copy of training-3/AyushRanjan/task). Never push attack/target/.
set -euo pipefail
for n in 1 2 3; do
  rm -rf /tmp/scratch$n; cp -r attack/target /tmp/scratch$n
  cp attack/cheat$n/solve.sh /tmp/scratch$n/solution/solve.sh
  harbor run -p /tmp/scratch$n -a oracle
  echo "cheat$n done: copy verifier/reward.json from the new jobs/ folder to attack/results/cheat$n-reward.json"
done
