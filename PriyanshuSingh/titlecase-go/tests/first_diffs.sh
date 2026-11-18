#!/bin/bash
# Author tool, not part of grading. Runs solution/solve.sh in the task image,
# feeds it the visible inputs, and prints the first 10 lines that differ.
# Usage (from the task folder): bash tests/first_diffs.sh [inputs expected]
set -euo pipefail
INPUTS=${1:-inputs.txt}
EXPECTED=${2:-expected.txt}
HOST=$(pwd -W 2>/dev/null || pwd)

docker build -q -t titlecase-go-env environment > /dev/null
MSYS_NO_PATHCONV=1 docker run --rm -v "$HOST:/task:ro" titlecase-go-env bash -c "
  set -e
  bash /task/solution/solve.sh
  go build -o /tmp/titlecase .
  /tmp/titlecase < /task/tests/data/$INPUTS > /tmp/actual.txt
  cp /task/tests/data/$INPUTS /tmp/in.txt
  cp /task/tests/data/$EXPECTED /tmp/want.txt
  paste -d '\n' /tmp/in.txt /tmp/want.txt /tmp/actual.txt | awk '
    NR % 3 == 1 { input = \$0 }
    NR % 3 == 2 { want = \$0 }
    NR % 3 == 0 {
      total++
      if (want != \$0) {
        bad++
        if (bad <= 10) {
          print \"input:    [\" input \"]\"
          print \"expected: [\" want \"]\"
          print \"actual:   [\" \$0 \"]\"
          print \"\"
        }
      }
    }
    END { print bad + 0 \" of \" total \" lines differ\" }'
"
