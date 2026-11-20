#!/bin/bash
# Grade /workspace/repo. Always exit 0 after writing /logs/verifier/reward.json.

mkdir -p /logs/verifier

write_reward() {
  printf '{"reward": %s}\n' "$1" > /logs/verifier/reward.json
}

REPO=/workspace/repo
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
INPUTS="$SCRIPT_DIR/data/hidden_inputs.txt"
EXPECTED="$SCRIPT_DIR/data/hidden_expected.txt"

if [[ ! -d "$REPO" ]]; then
  write_reward 0.0
  exit 0
fi

# Any remaining Python file scores zero, including when the build would pass.
if find "$REPO" -type f -name '*.py' -print -quit | grep -q .; then
  write_reward 0.0
  exit 0
fi

if ! (cd "$REPO" && go build -buildvcs=false ./...); then
  write_reward 0.0
  exit 0
fi

BIN=$(mktemp)
if ! (cd "$REPO" && go build -buildvcs=false -o "$BIN" .); then
  write_reward 0.0
  exit 0
fi

if [[ ! -f "$INPUTS" || ! -f "$EXPECTED" ]]; then
  write_reward 0.0
  exit 0
fi

ACTUAL=$(mktemp)
"$BIN" < "$INPUTS" > "$ACTUAL" || true

# Whole-stream identity is 1.0. Otherwise each expected or extra line is one trial.
if cmp -s "$EXPECTED" "$ACTUAL"; then
  write_reward 1.0
  exit 0
fi

score=$(awk '
FNR == NR { expected[NR] = $0; nexp = NR; next }
{ actual[FNR] = $0; nact = FNR }
END {
  if (nexp > nact) {
    total = nexp
  } else {
    total = nact
  }
  correct = 0
  limit = nexp
  if (nact < limit) {
    limit = nact
  }
  for (i = 1; i <= limit; i++) {
    if (actual[i] == expected[i]) {
      correct++
    }
  }
  if (total == 0 || correct == 0) {
    printf "0.0"
  } else if (correct == total) {
    printf "1.0"
  } else {
    printf "%.6f", correct / total
  }
}
' "$EXPECTED" "$ACTUAL")

# Identical lines with a different final newline must not score as perfect.
if [[ "$score" == "1.0" ]]; then
  score=0.999500
fi

write_reward "$score"
exit 0
