#!/bin/bash
# Check 3 (the only scored check): byte-exact output on 100,000 hidden titles.
#
# Prints one number on stdout.
#
# Scoring. A whole-stream byte-for-byte match is 1.0. Otherwise the per-line
# match rate is mapped through a floor: below 0.90 the score is 0.0, and from
# 0.90 to 1.00 it ramps linearly to just under 1.0. The old exam gave straight
# per-line credit, which handed cheat 3 (a 40-line half port with no hyphen,
# slash, Mc, apostrophe or acronym handling) 837/2000 = 0.4185. A near-correct
# port still earns partial credit: 0.95 of the lines is worth 0.50.
set -u

TESTS=${TESTS:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
REPO=${REPO:-/workspace/repo}
INPUTS="$TESTS/data/inputs.txt"
ANSWERS="$TESTS/data/answers.txt"

# uid/gid 65534 is nobody/nogroup on Debian.
GRADER_UID=65534
GRADER_GID=65534
WORK=/var/grader

fail() { echo "0.0"; exit 0; }

[[ -f "$INPUTS" && -f "$ANSWERS" ]] || fail

HOME_TMP=$(mktemp -d /tmp/go-home-XXXXXX) || fail
trap 'rm -rf "$HOME_TMP" "$WORK/titlecase" "$WORK/got.txt"' EXIT

if ! (cd "$REPO" && env HOME="$HOME_TMP" \
        GOCACHE="$HOME_TMP/cache" GOMODCACHE="$HOME_TMP/mod" \
        GOPATH="$HOME_TMP/path" GOTOOLCHAIN=local GOFLAGS= \
        go build -buildvcs=false -o "$HOME_TMP/titlecase" .); then
  echo "behaviour: go build . failed" >&2
  fail
fi
[[ -f "$HOME_TMP/titlecase" ]] || fail

# The compiled binary is the only thing the grading user may touch. Everything
# the agent shipped stays root-only, so a Python interpreter (or any other
# helper) copied into the submission cannot be executed even if one were found.
install -m 0755 -o 0 -g 0 "$HOME_TMP/titlecase" "$WORK/titlecase" || fail
chmod -R go-rwx "$REPO" 2>/dev/null

: > "$WORK/got.txt"
chmod 0666 "$WORK/got.txt"

DROP=""
if command -v setpriv >/dev/null 2>&1; then
  DROP="setpriv --reuid=$GRADER_UID --regid=$GRADER_GID --clear-groups"
elif command -v runuser >/dev/null 2>&1; then
  DROP="runuser -u nobody --"
fi
if [[ -z "$DROP" ]]; then
  echo "behaviour: no way to drop privileges; refusing to grade as root" >&2
  fail
fi

# stdin and stdout are opened here, by root, and only the already-open file
# descriptors are handed to the unprivileged process.
( cd "$WORK" && $DROP "$WORK/titlecase" ) < "$INPUTS" > "$WORK/got.txt" 2>/dev/null
status=$?
if [[ $status -ne 0 ]]; then
  echo "behaviour: the program exited $status" >&2
fi

if cmp -s "$ANSWERS" "$WORK/got.txt"; then
  echo "behaviour: byte-identical on the whole stream" >&2
  echo "1.0"
  exit 0
fi

# awk prints "<score> <matched> <total> <rate>". Only the score goes to stdout.
# The rest is diagnostics for the task author; it lands in the verifier log,
# which the agent never sees.
report=$(awk '
FNR == NR { want[FNR] = $0; nwant = FNR; next }
{ got[FNR] = $0; ngot = FNR }
END {
  total = nwant
  if (ngot > total) { total = ngot }
  limit = (ngot < nwant) ? ngot : nwant
  correct = 0
  for (i = 1; i <= limit; i++) {
    if (got[i] == want[i]) { correct++ }
  }
  if (total == 0) { printf "0.000000 0 0 0.000000\n"; exit }
  rate = correct / total
  score = (rate - 0.90) / 0.10
  if (rate < 0.90) { score = 0 }
  # The stream was not byte-identical (cmp above failed), so a perfect line
  # count must still not read as a perfect score; a stray trailing newline is
  # a real difference.
  if (score > 0.99) { score = 0.99 }
  printf "%.6f %d %d %.6f\n", score, correct, total, rate
}
' "$ANSWERS" "$WORK/got.txt")

set -- $report
echo "behaviour: matched $2 of $3 lines (rate $4) -> score $1" >&2
echo "$1"
