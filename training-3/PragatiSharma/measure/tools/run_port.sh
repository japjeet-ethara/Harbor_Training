#!/bin/bash
# Run one built port over one exam inside a disposable container (network off,
# read-only root, unprivileged user). Mounts: /port (binary, read-only),
# /suite (inputs.txt + answers.txt, read-only), /out (writable).
# Writes got.txt, stderr.txt, exit.txt, time.txt (real user sys, seconds).
set -u
TIMEFORMAT='%3R %3U %3S'
{ time /port/titlecase < /suite/inputs.txt > /out/got.txt 2> /out/stderr.txt; echo $? > /out/exit.txt; } 2> /out/time.txt
