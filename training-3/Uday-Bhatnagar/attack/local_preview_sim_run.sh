#!/bin/bash
# LOCAL PREVIEW ONLY (not a Harbor run). Mimics: agent runs solve.sh -> verifier builds module + runs pytest.
# usage: sim_run.sh <solution_dir> <label>
W=/home/claude/work
SOL=$(readlink -f "$1"); LABEL=$2
rm -rf /workspace/titlecase; ln -sfn "$SOL" /solution
( cd /workspace && bash /solution/solve.sh ) > $W/sim/$LABEL.solve.log 2>&1 || echo "solve.sh exited non-zero (see log)"
export PATH=$W/vv/bin:/usr/lib/go-1.23/bin:/usr/bin:/bin
export GOFLAGS=-mod=mod GOPATH=/tmp/gopath-sim GOCACHE=/tmp/gocache-sim
cd /tests
python -m pytest /tests/test_outputs.py -q -p no:cacheprovider -x --tb=line 2>&1 | tail -15 > $W/sim/$LABEL.pytest.log
python -m pytest /tests/test_outputs.py -q -p no:cacheprovider --tb=no 2>&1 | tail -3 | tee -a $W/sim/$LABEL.pytest.log
if python -m pytest /tests/test_outputs.py -q -p no:cacheprovider --tb=no >/dev/null 2>&1; then echo "REWARD($LABEL)=1"; else echo "REWARD($LABEL)=0"; fi
