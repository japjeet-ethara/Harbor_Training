#!/usr/bin/env python3
"""Differential fuzz test: random cases NOT in the exam, original (in-process) vs a built program.

    python3 dev/fuzz.py --bin /path/to/figlet [--n 20000] [--seed 12345] [--all-fonts]

Uses the same "run the original main()" helper as tests/gen.py. Cases where the
original itself fails, loops or prints nothing are skipped (they are not part of the exam).
Prints the first differing cases.
"""
import argparse
import os
import random
import signal
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
import gen  # noqa: E402

ASCII = [chr(c) for c in range(32, 127)]
EXTRA = list("éßñÄöüÿç€☃日😀¿£§ \t") + ["\n"]
PUNCT = list("|/\\_[]{}()<>-^~`'\"!?.,:;@#$%&*+=")


def rand_text(rng):
    n = rng.randrange(1, 40)
    pool = rng.choice([ASCII, ASCII + EXTRA, PUNCT + [" "], PUNCT + list("ab "), list("ilWm |/\\_")])
    return "".join(rng.choice(pool) for _ in range(n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", required=True)
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--all-fonts", action="store_true", help="use every .flf of fonts-standard")
    ap.add_argument("--pyfiglet", default=os.path.join(gen.TASK, "..", "pyfiglet"))
    ap.add_argument("--max-show", type=int, default=3)
    ns = ap.parse_args()

    signal.signal(signal.SIGALRM, gen._on_alarm)
    gen.check_original(ns.pyfiglet)
    pyfiglet = gen.load_original(ns.pyfiglet)

    fonts = gen.FONTS
    if ns.all_fonts:
        d = os.path.join(ns.pyfiglet, "pyfiglet", "fonts-standard")
        fonts = sorted(f[:-4] for f in os.listdir(d) if f.endswith(".flf"))

    rng = random.Random(ns.seed)
    tested = skipped = bad = 0
    while tested < ns.n:
        args = []
        if rng.random() < 0.9:
            args += ["-f", rng.choice(fonts)]
        if rng.random() < 0.9:
            args += ["-w", str(rng.choice([rng.randrange(1, 60), 10, 20, 40, 60, 80, 120]))]
        if rng.random() < 0.6:
            args += ["-j", rng.choice(gen.JUSTIFY)]
        if rng.random() < 0.6:
            args += ["-D", rng.choice(gen.DIRECTION)]
        flags = ["-r", "-F", "-s", "-n"]
        rng.shuffle(flags)
        args += [f for f in flags if rng.random() < 0.4]
        text = rand_text(rng)
        args += text.split(" ") if rng.random() < 0.5 and "\n" not in text else [text]
        if not gen.valid_shape(args):
            continue
        want = gen.run_original(pyfiglet, args)
        if want is None or want.decode("utf-8").strip() == "":
            skipped += 1
            continue
        tested += 1
        try:
            got = subprocess.run([ns.bin] + args, capture_output=True, timeout=10)
            same = got.returncode == 0 and got.stdout == want
        except subprocess.TimeoutExpired:
            same, got = False, None
        if not same:
            bad += 1
            if bad <= ns.max_show:
                print("DIFF", args)
                print("expected:\n" + want.decode("utf-8"))
                print("got:\n" + (got.stdout.decode("utf-8", "replace") if got else "<timeout>"))
                if got is not None and got.stderr:
                    print("stderr:", got.stderr.decode("utf-8", "replace")[:300])
    print("fuzz: tested %d, skipped %d (original failed/blank), differing %d" % (tested, skipped, bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
