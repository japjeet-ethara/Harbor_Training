#!/usr/bin/env python3
"""Compare the Go program with the original library on random titles.

Runs INSIDE the agent image (it needs python3, `regex` and go), for example:

    docker run --rm -v "<task folder>:/task" <image> \
        sh -c 'cd /task/solution/src && go build -o /tmp/tc . && python3 /task/scripts/fuzz.py /tmp/tc 50000 wide'

    fuzz.py <go binary> [count] [narrow|wide]

narrow: titles from the same generator as tests/gen.py (a different seed).
wide:   also random runs of unusual characters (more scripts, symbols, odd whitespace).
Prints the first differences and exits 1 if there is any.
"""

import random
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
import gen  # noqa: E402

WIDE_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "àáâäåæçèéêëìíîïðñòóôöøùúûüýþÿÀÁÂÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÖØÙÚÛÜÝÞßœŒšŠžŽłŁđĐ"
    "ǅǆǄİıĳĲﬁﬂ"
    "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "‘’“”‚„«»‹›–—―‒…•¿¡§¶†‡€£¥©®™°±×÷≤≥≠∞√∑∏∫µ¼½¾"
    " \t   　  "
)


def wide_title(rng):
    if rng.random() < 0.5:
        return gen.make_title(rng)
    n = rng.randint(1, 40)
    s = "".join(rng.choice(WIDE_CHARS) for _ in range(n))
    if rng.random() < 0.2:
        s = s.upper()
    return s


def main():
    binary = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
    mode = sys.argv[3] if len(sys.argv) > 3 else "narrow"
    original = gen.load_original()
    rng = random.Random(20261116)
    make = gen.make_title if mode == "narrow" else wide_title
    titles = []
    while len(titles) < count:
        t = make(rng)
        if not (gen.FORBIDDEN & set(t)):
            titles.append(t)
    data = "".join(t + "\n" for t in titles).encode("utf-8")
    got = subprocess.run([binary], input=data, capture_output=True, check=True).stdout.decode("utf-8").split("\n")[:-1]
    want = [original(t) for t in titles]
    bad = [(t, w, g) for t, w, g in zip(titles, want, got) if w != g]
    if len(got) != len(titles):
        print(f"line count differs: {len(got)} output lines for {len(titles)} inputs")
    for t, w, g in bad[:10]:
        print(f"input:    {t!r}\nexpected: {w!r}\ngot:      {g!r}\n")
    print(f"{mode}: {len(bad)} of {count} titles differ")
    sys.exit(1 if bad or len(got) != len(titles) else 0)


if __name__ == "__main__":
    main()
