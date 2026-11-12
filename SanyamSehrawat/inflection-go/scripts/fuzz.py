#!/usr/bin/env python3
"""Compare a Linux build of the Go port with the ORIGINAL inflection on random lines.

    python scripts/fuzz.py <binary-ending-in--linux> [count] [seed]

The binary runs inside the golang:1.23 image (Docker must be running).
Arguments are random printable ASCII, much wilder than the graded data.
"""
import random
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(TASK / "tests"))
import gen  # noqa: E402

functions = gen.load_original()
binary = Path(sys.argv[1]).resolve()
count = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 7)

alphabet = [chr(c) for c in range(0x20, 0x7F)] + list("aeiouysxzhqlfmnt_-' ") * 3
lines = []
for _ in range(count):
    name = rng.choice(list(functions))
    if name == "ordinalize":
        arg = rng.choice(["", "-"]) + "".join(rng.choice("0123456789") for _ in range(rng.randint(1, 25)))
    else:
        r = rng.random()
        if r < 0.5:
            arg = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
        else:
            # Random suffixes on real nouns hit the rule tables much more often.
            arg = rng.choice(gen.NOUNS + gen.CAMEL) + "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 3)))
            arg = gen.rand_case(arg) if rng.random() < 0.5 else arg
    if gen.ok(name, arg):
        lines.append((name, arg))

expected = [functions[n](a) for n, a in lines]
cmd = ["docker", "run", "--rm", "-i", "-v", f"{binary.parent}:/w:ro", "golang:1.23", f"/w/{binary.name}"]
proc = subprocess.run(cmd, input="".join(f"{n}\t{a}\n" for n, a in lines).encode(), capture_output=True)
if proc.returncode != 0:
    sys.exit(f"binary failed: {proc.stderr.decode('utf-8', 'replace')[:500]}")
actual = proc.stdout.decode().split("\n")[:-1]

bad = 0
for (n, a), want, got in zip(lines, expected, actual + ["<missing>"] * len(lines)):
    if got != want:
        bad += 1
        if bad <= 15:
            print(f"DIFF {n}({a!r})\n     want={want!r}\n      got={got!r}")
print(f"mismatches: {bad} of {len(lines)} (output lines {len(actual)})")
