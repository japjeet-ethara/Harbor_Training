"""Generate a deterministic, unique titlecase input pool."""

import argparse
import importlib.util
from pathlib import Path
import random


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("count", type=int)
    parser.add_argument("seed", type=int)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    generator = Path(__file__).resolve().parents[1] / "task/tests/gen.py"
    spec = importlib.util.spec_from_file_location("practice_generator", generator)
    practice = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(practice)

    random.seed(args.seed)
    words = (
        "v1.2", "_dream", "Mcx-", "ıstanbul", "ſound", "Fuß", "Σίσυφος",
        "é.œ", "X-RAY", "o’neil", "l‘oiseau", "x².y", "A\u0301",
    )
    separators = (" ", "\t", "\u00a0", "\u2003", "\u2009")
    seen = set()
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        while len(seen) < args.count:
            title = practice.make_title()
            if random.randrange(4) == 0:
                title += random.choice(separators) + random.choice(words)
            if title not in seen:
                seen.add(title)
                output.write(title + "\n")


if __name__ == "__main__":
    main()
