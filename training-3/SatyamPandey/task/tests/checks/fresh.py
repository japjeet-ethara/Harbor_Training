"""Fresh titles made at grading time (this file defines no criterion of its own).

The 100,000 frozen answers live in a public repository, so a program can simply
carry them as a lookup table. To make that worthless, every grading run also makes
a new random sample of titles nobody has seen: words and spaces taken from the
frozen pool (so the same weird families), about half of the words mutated into
words that never occur in the pool, recombined, never equal to a pool title.
(Without the mutation a word-by-word table learned from the public answers was
right on 88.8% of fresh titles; see HARDEN.md.)
Their answers come from the ORIGINAL titlecase WITH `regex`, run twice in separate
processes (different hash seeds); only answers that agree both times are graded.
"""
import os
import random
import re
import subprocess
import sys
import tempfile

ORIGINAL = "/tests/original"           # copy of python-titlecase/titlecase (MIT)
SPLIT = re.compile(r"(\s)")            # how titlecase splits a line (stdlib re; same for these spaces)

CHILD = ("import sys; sys.path.insert(0, sys.argv[1]); import titlecase as m; "
         "lines = open(sys.argv[2], encoding='utf-8').read().split('\\n')[:-1]; "
         "print('\\x00'.join(m.titlecase(t) for t in lines), end=''); "
         "print('\\x01' + str(m.REGEX_AVAILABLE), end='')")


LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = LOWER.upper()


def _mutate(w: str, rng: random.Random) -> str:
    """A word nobody has seen: some ASCII letters replaced (same case), some cases flipped.
    Non-ASCII letters, digits, punctuation and prefixes like mc/o'/d' mostly survive, so
    the rare paths are still exercised, but a word-by-word table learned from the public
    answers no longer knows the word."""
    out = []
    for c in w:
        r = rng.random()
        if c in LOWER and r < 0.35:
            c = rng.choice(LOWER)
        elif c in UPPER and r < 0.35:
            c = rng.choice(UPPER)
        elif r < 0.45:
            c = c.swapcase() if len(c.swapcase()) == 1 else c
        out.append(c)
    return "".join(out)


def _word(words: list[str], rng: random.Random) -> str:
    w = rng.choice(words)
    r = rng.random()
    if r < 0.45:
        w = _mutate(w, rng)
    elif r < 0.55:                                   # glue two words: new hyphen/slash/apostrophe forms
        w = w + rng.choice("-/'") + _mutate(rng.choice(words), rng)
    return w


def make_titles(pool: list[str], n: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    words, spaces = [], []
    for t in pool:
        parts = SPLIT.split(t)
        words.extend(w for w in parts[::2] if w)
        spaces.extend(parts[1::2])
    seen, out = set(pool), []
    while len(out) < n:
        k = rng.randint(1, 9)
        parts = []
        for i in range(k):
            parts.append(_word(words, rng))
            if i < k - 1:
                parts.append(rng.choice(spaces))
        t = "".join(parts)
        r = rng.random()
        if r < 0.10:
            t = t.upper()
        elif r < 0.15:
            t = t.lower()
        r = rng.random()
        if r < 0.02:
            t = rng.choice(spaces) + t
        elif r < 0.04:
            t = t + rng.choice(spaces)
        if t in seen or "\n" in t or "\r" in t:
            continue
        seen.add(t)
        out.append(t)
    return out


def _run_original(path: str, hash_seed: int) -> list[str]:
    env = {"PYTHONHASHSEED": str(hash_seed), "PATH": "/usr/bin:/bin"}
    out = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, ORIGINAL, path],
                         capture_output=True, text=True, encoding="utf-8", env=env,
                         check=True, timeout=120).stdout
    body, regex_flag = out.rsplit("\x01", 1)
    if regex_flag != "True":
        raise RuntimeError("the original must run WITH the regex package")
    return body.split("\x00")


def fresh_exam(pool: list[str], n: int) -> tuple[int, list[str], list[str]]:
    """(seed, inputs, answers) for n new titles, answers frozen twice."""
    seed = int.from_bytes(os.urandom(8), "big")
    titles = make_titles(pool, n, seed)
    fd, path = tempfile.mkstemp(prefix="tc-fresh-")      # mode 0600, root only
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(t + "\n" for t in titles)
        first, second = _run_original(path, 1), _run_original(path, 2)
    finally:
        os.remove(path)
    keep = [i for i in range(len(titles)) if first[i] == second[i]]
    return seed, [titles[i] for i in keep], [first[i] for i in keep]
