#!/bin/bash
# Hardened verifier for ethara/titlecase-go.
#
# reward = behaviour, but only when the submission builds and is clean.
# build and no_python are gates, not points (Day 4 cheats 1 and 2 got 0.333
# from them alone). The port runs in an empty chroot as nobody, so it cannot
# open /tests/data/answers.txt (Day 4 cheat 3 read it and scored 1.0).
set -u
export LC_ALL=C
export CGO_ENABLED=0 GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local GOWORK=off

REPO=/workspace/repo
INPUTS=/tests/data/inputs.txt
ANSWERS=/tests/data/answers.txt
LOGS=/logs/verifier
mkdir -p "$LOGS"

build=0
no_python=0
behaviour=0

# Gate 1: the module builds (go build ./..., as the instruction says).
if [ -f "$REPO/go.mod" ] && (cd "$REPO" && go build ./...) > "$LOGS/build.log" 2>&1; then
  build=1
fi

# Gate 2: a clean, self-contained Go port.
#   - no .py file anywhere in the repo
#   - standard library only: no require/replace in go.mod, no vendor/
#   - no cgo (it could .incbin files at build time); CGO_ENABLED=0 also blocks it
#   - Go sources under 1 MB, so a pasted answer table cannot hide in the code
if [ "$build" = 1 ]; then
  no_python=1
  if [ -n "$(find "$REPO" -name '*.py' -print -quit)" ]; then
    echo "found .py files" >> "$LOGS/clean.log"; no_python=0
  fi
  if grep -Eq '^[[:space:]]*(require|replace)([[:space:]]|\()' "$REPO/go.mod"; then
    echo "go.mod has require/replace" >> "$LOGS/clean.log"; no_python=0
  fi
  if [ -e "$REPO/vendor" ]; then
    echo "vendor/ present" >> "$LOGS/clean.log"; no_python=0
  fi
  if grep -rlq --include='*.go' -E 'import[[:space:]]+"C"' "$REPO"; then
    echo "cgo import found" >> "$LOGS/clean.log"; no_python=0
  fi
  size=$(find "$REPO" -type f -name '*.go' -printf '%s\n' | awk '{s += $1} END {print s + 0}')
  if [ "$size" -gt 1000000 ]; then
    echo "Go sources are $size bytes" >> "$LOGS/clean.log"; no_python=0
  fi
fi

# Behaviour: run the port alone in an empty jail, as uid/gid 65534.
if [ "$build" = 1 ] && [ "$no_python" = 1 ]; then
  JAIL=$(mktemp -d /tmp/jail.XXXXXX)
  if (cd "$REPO" && go build -o "$JAIL/titlecase" .) >> "$LOGS/build.log" 2>&1; then
    chmod 755 "$JAIL" "$JAIL/titlecase"
    timeout 300 chroot --userspec=65534:65534 "$JAIL" /titlecase \
        < "$INPUTS" 2> "$LOGS/run.err" | head -c 50000000 > /tmp/actual.txt
    expected_n=$(wc -l < "$ANSWERS")
    behaviour=$(awk -v n="$expected_n" '
      NR == FNR { want[FNR] = $0; next }
      { got_n = FNR; if (FNR <= n && $0 == want[FNR]) ok++ }
      END { total = (got_n > n) ? got_n : n; printf "%.6f", (total ? ok / total : 0) }
    ' "$ANSWERS" /tmp/actual.txt)
  fi
  rm -rf "$JAIL"
fi

if [ "$build" = 1 ] && [ "$no_python" = 1 ]; then
  reward=$behaviour
else
  reward=0
fi

printf '{\n  "build": %s,\n  "no_python": %s,\n  "behaviour": %s,\n  "reward": %s\n}\n' \
  "$build" "$no_python" "$behaviour" "$reward" > "$LOGS/reward.json"
cat "$LOGS/reward.json"
