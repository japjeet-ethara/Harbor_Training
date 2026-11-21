#!/bin/bash
# Hardened verifier for titlecase-go.
export LC_ALL=C
export CGO_ENABLED=0 GOFLAGS=-mod=readonly GOPROXY=off GOTOOLCHAIN=local
mkdir -p /logs/verifier

REPO=/workspace/repo
build=0; clean=0; beh=0

# 1. The project must build.
cd "$REPO" 2>/dev/null
if [ "$PWD" = "$REPO" ] && go build ./... > /tmp/build.log 2>&1; then
  build=1
fi

# 2. "clean" = a real, self-contained Go port.
if [ "$build" = 1 ]; then
  clean=1
  # 2a. no .py file anywhere under /workspace
  if [ -n "$(find /workspace -name '*.py' -print -quit 2>/dev/null)" ]; then clean=0; fi
  # 2b. no way to start other programs or hide payloads
  if grep -rEq '"os/exec"|"syscall"|"plugin"|"unsafe"|import "C"|go:embed|go:linkname' --include='*.go' "$REPO"; then clean=0; fi
  # 2c. standard library only
  if grep -Eq '^[[:space:]]*(require|replace)\b' "$REPO/go.mod"; then clean=0; fi
  if [ -e "$REPO/vendor" ]; then clean=0; fi
  # 2d. a real port is small; a pasted answer table is not
  size=$(find "$REPO" -type f \( -name '*.go' -o -name go.mod \) -printf '%s\n' | awk '{s+=$1} END{print s+0}')
  if [ "$size" -gt 400000 ]; then clean=0; fi
fi

# 3. Run the port alone in an empty jail, as an unprivileged user.
if [ "$build" = 1 ] && [ "$clean" = 1 ]; then
  if go build -o /tmp/tc_bin . >> /tmp/build.log 2>&1 && [ "$(stat -c %s /tmp/tc_bin)" -lt 8000000 ]; then
    J=/tmp/jail; rm -rf "$J"; mkdir -p "$J"
    cp /tmp/tc_bin "$J/tc"; chmod 755 "$J" "$J/tc"
    timeout 300 chroot --userspec=65534:65534 "$J" /tc < /tests/data/inputs.txt 2> /tmp/run.err \
      | head -c 20000000 > /tmp/out.txt || true
    total=$(wc -l < /tests/data/answers.txt)
    beh=$(awk -v total="$total" 'NR==FNR{a[FNR]=$0; next} {if (FNR<=total && $0==a[FNR]) c++} END{printf "%.6f", c/total}' \
          /tests/data/answers.txt /tmp/out.txt)
  fi
fi

# 4. Behaviour is the whole score, and only counts for a build that is clean.
if [ "$build" = 1 ] && [ "$clean" = 1 ]; then reward=$beh; else reward=0.000000; fi
printf '{"build": %s, "no_python": %s, "behaviour": %s, "reward": %s}\n' \
  "$build" "$clean" "$beh" "$reward" > /logs/verifier/reward.json
cat /logs/verifier/reward.json
