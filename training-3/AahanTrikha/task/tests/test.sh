#!/usr/bin/env bash
set -uo pipefail

REPO=/workspace/repo
LOGS=/logs/verifier
mkdir -p "$LOGS"

export HOME="${HOME:-/tmp}"
export GOCACHE="${GOCACHE:-/tmp/gocache}"
export GOPATH="${GOPATH:-/tmp/gopath}"
export GOTOOLCHAIN=local
export GOFLAGS=-mod=mod
mkdir -p "$GOCACHE" "$GOPATH" 2>/dev/null

{
  echo "user=$(whoami) pwd=$(pwd) HOME=$HOME"
  go version 2>&1
  go env GOCACHE GOPATH GOFLAGS GOTOOLCHAIN 2>&1
  echo "--- /workspace ---"; ls -la /workspace 2>&1
  echo "--- repo ---"; ls -la "$REPO" 2>&1
  echo "--- /tests ---"; ls -la /tests 2>&1
  echo "--- /tests/data ---"; ls -la /tests/data 2>&1
  echo "--- py files ---"; find "$REPO" -name '*.py' 2>&1 | head -20
} > "$LOGS/env.log" 2>&1

build=0; nopy=0; beh=0.0

if cd "$REPO" 2>/dev/null; then
  go build ./... > "$LOGS/build.log" 2>&1; rc1=$?
  go build -o /tmp/tc . >> "$LOGS/build.log" 2>&1; rc2=$?
  echo "rc_all=$rc1 rc_main=$rc2" >> "$LOGS/build.log"
  if [ "$rc1" -eq 0 ] && [ "$rc2" -eq 0 ]; then build=1; fi
  if [ "$build" -eq 1 ] && [ -z "$(find "$REPO" -name '*.py' -print -quit)" ]; then nopy=1; fi
  if [ "$build" -eq 1 ]; then
    /tmp/tc < /tests/data/hidden_inputs.txt > /tmp/out.txt 2>>"$LOGS/build.log" || true
    beh=$(python3 -c '
w=open("/tests/data/hidden_expected.txt",encoding="utf-8").read().split("\n")
g=open("/tmp/out.txt",encoding="utf-8",errors="replace").read().split("\n")
if w and w[-1]=="": w.pop()
if g and g[-1]=="": g.pop()
n=len(w); m=sum(1 for i in range(n) if i<len(g) and g[i]==w[i])
print("%.4f" % (m/n if n else 0.0))
' 2>>"$LOGS/build.log")
    beh="${beh:-0.0}"
  fi
else
  echo "cd $REPO failed" >> "$LOGS/build.log"
fi

reward=$(python3 -c "print('%.4f' % ((1*$build + 1*$nopy + 4*$beh)/6))")
printf '{"build": %s, "no_python": %s, "behaviour": %s, "reward": %s}\n' \
  "$build" "$nopy" "$beh" "$reward" > "$LOGS/reward.json"
cat "$LOGS/reward.json"