# Day 5: how to produce the evidence

Run these in WSL from the folder that contains `task/` (for example `.../AyushKhurana`). Every number in
`HARDEN.md` must come from a `jobs/<name>/` folder made by these commands.

## 0. Quick check without Harbor (Docker only)
```
AMAN=~/path/to/Harbor_Training/training-3/AmanTiwari/attack bash task/extra-cheat-tests/try_verifier5.sh
```
It prints the Permission-denied line for the Python lock, then nop, oracle, the control, the two gate tests,
the lookup cheat and (with AMAN set) his three cheats.

## 1. The two basic runs
```
harbor run -p ./task -a oracle --job-name d5-oracle -o jobs     # must be 1.0
harbor run -p ./task -a nop    --job-name d5-nop    -o jobs     # must be 0.0
```

## 2. The cheats (each is a throw-away copy of the task whose solve.sh is the cheat)
```
AMAN=~/path/to/Harbor_Training/training-3/AmanTiwari/attack
cheat() {   # cheat <name> <solve script> [with-data]
  rm -rf /tmp/ct-$1 && cp -r task /tmp/ct-$1 && cp "$2" /tmp/ct-$1/solution/solve.sh
  [ "${3:-}" = with-data ] && cp task/tests/data/inputs.txt /tmp/ct-$1/solution/q.txt && cp task/tests/data/answers.txt /tmp/ct-$1/solution/a.txt
  harbor run -p /tmp/ct-$1 -a oracle --job-name d5-$1 -o jobs
}
cheat aman1  $AMAN/cheat1/solve.sh      # below 0.2
cheat aman2  $AMAN/cheat2/solve.sh      # 0.0 (no_exec fails)
cheat aman3  $AMAN/cheat3/solve.sh      # download blocked, so nothing useful is built
cheat hybrid task/extra-cheat-tests/day5/lookup_plus_halfport.sh with-data   # below 0.2
```
`cheat3` needs the internet; if the run shows a `curl` failure in `jobs/d5-aman3/*/agent/`, that is the allowlist working.

## 3. Allowlist acceptance test
```
cheat netprobe task/extra-cheat-tests/day5/net_probe.sh
```
Open `jobs/d5-netprobe/*/agent/` and read the three lines. If Harbor refuses to start because the engine cannot
do egress control, the message says so: then report that in HARDEN.md under "Limits"; do not remove the allowlist silently.
