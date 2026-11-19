#!/bin/bash
# Builds every broken variant of the port and runs it on the hidden, the visible and the large random titles.
# Mounts: /task = the task folder (read only), /fuzz = the scratch folder that holds mut/ and fuzz_inputs.txt.
cd /fuzz/mut || exit 1
while read -r name; do
  [ -z "$name" ] && continue
  if (cd "/fuzz/mut/$name" && go build -o "/tmp/bin_$name" . 2>"/fuzz/mut/$name.build.log"); then
    "/tmp/bin_$name" < /task/tests/data/hidden_inputs.txt > "/fuzz/mut/$name.hidden.out" 2>/dev/null
    "/tmp/bin_$name" < /task/tests/data/inputs.txt > "/fuzz/mut/$name.visible.out" 2>/dev/null
    "/tmp/bin_$name" < /fuzz/fuzz_inputs.txt > "/fuzz/mut/$name.fuzz.out" 2>/dev/null
  fi
done < /fuzz/mut/names.txt
echo "all variants built and run"
