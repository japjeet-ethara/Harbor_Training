#!/bin/bash
mkdir -p /logs/verifier

cd /workspace/repo || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

if find /workspace/repo -type f -name '*.py' | grep -q .; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

export GOPROXY=off
export GOSUMDB=off

mkdir -p /tmp/gobin
if ! go build -o /tmp/gobin/ ./...; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

score_pair() {
  in_file=$1
  exp_file=$2
  got_file=$(mktemp)
  if ! /tmp/gobin/titlecase < "$in_file" > "$got_file"; then
    echo 0 0
    rm -f "$got_file"
    return
  fi
  awk '
    NR == FNR { want[NR] = $0; nexp = NR; next }
    { ngot++; if ($0 == want[FNR]) matched++ }
    END {
      total = nexp
      if (ngot > total) total = ngot
      print matched + 0, total + 0
    }
  ' "$exp_file" "$got_file"
  rm -f "$got_file"
}

read -r ok total < <(score_pair /tests/data/hidden_inputs.txt /tests/data/hidden_expected.txt)
if [ "$total" -eq 0 ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi
if [ "$ok" -eq "$total" ]; then
  echo 1 > /logs/verifier/reward.txt
else
  awk -v ok="$ok" -v total="$total" 'BEGIN { printf "%.6f\n", ok / total }' > /logs/verifier/reward.txt
fi
