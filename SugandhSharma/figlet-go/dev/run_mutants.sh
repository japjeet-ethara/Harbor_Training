#!/bin/bash
# Builds every broken variant of the port in the room image and counts the cases it gets wrong
# on the hidden cases and on a larger random set. Several variants run at the same time.
# Mounts: /task = the task folder (read only), /scratch = the folder that holds mut/ and fuzz_small.jsonl.
# Usage: bash /task/dev/run_mutants.sh [WORKERS]      (default 4)
# Writes /scratch/mutation_counts.txt with lines:  name hidden_wrong fuzz_wrong   (or "name BUILD_FAILED").
workers="${1:-4}"
cd /tmp && cp /task/dev/compare.go /tmp/compare.go && go build -o /tmp/compare /tmp/compare.go || exit 1
: > /scratch/mutation_counts.txt

one() {
  name="$1"
  dir="/tmp/m_$name"
  rm -rf "$dir" && mkdir -p "$dir/fonts"
  cp "/scratch/mut/$name"/* "$dir/" && cp /workspace/repo/pyfiglet/fonts/*.flf "$dir/fonts/"
  if (cd "$dir" && go build -o "/tmp/mutant_$name" . 2>"/tmp/build_$name.log"); then
    h=$(/tmp/compare /task/tests/data/hidden.jsonl "/tmp/mutant_$name" | tail -1 | sed -E 's/.*; ([0-9]+) differ/\1/')
    f=$(/tmp/compare /scratch/fuzz_small.jsonl "/tmp/mutant_$name" | tail -1 | sed -E 's/.*; ([0-9]+) differ/\1/')
    echo "$name $h $f" >> /scratch/mutation_counts.txt
  else
    echo "$name BUILD_FAILED" >> /scratch/mutation_counts.txt
  fi
  rm -rf "$dir" "/tmp/mutant_$name"
}

while read -r name; do
  [ -z "$name" ] && continue
  while [ "$(jobs -rp | wc -l)" -ge "$workers" ]; do
    wait -n
  done
  one "$name" &
done < /scratch/mut/names.txt
wait
echo "all variants built and run"
