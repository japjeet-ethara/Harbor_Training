import random
import sys
from pathlib import Path


COUNT = 2000
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "environment" / "repo-source"
DATA = ROOT / "tests" / "data"


def build_titles(prefix, rng):
    titles = [
        "a tale of two cities",
        "an example of the rule",
        "war and peace",
        "rules: and exceptions",
        "hello\t  world",
        "(hello) [world]",
        "state-of-the-art design",
        "input/output values",
        "double//slash example",
        "d'art l'amour o'neill",
        "mcdonald meets mccarthy",
        "mr mRS ms dr",
        "use e.g. values",
        "visit iPhone users",
        "MEET U.S. AT 5",
        "THIS IS A TEST",
        "usa bcd",
        "one; and another",
        "wait! for the answer",
        "question? or answer",
        "part - and more",
        "v vs via",
        "the end of a",
        "  leading and trailing  ",
        "tabs\tand\tspaces",
        "version 2.0 of api",
        "rock'n'roll and r&d",
        "pre/post-processing",
        "mother-in-law's secret",
        "C++ and c# tools",
    ]

    ordinary = [
        "alpha", "bravo", "charlie", "delta", "echo", "foxtrot",
        "garden", "holiday", "language", "market", "network", "orange",
        "project", "quiet", "river", "signal", "title", "under", "yellow",
    ]
    small = [
        "a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
        "in", "of", "on", "or", "the", "to", "v", "via", "vs",
    ]
    tricky = [
        "d'art", "l'amour", "o'neill", "mcdonald", "MCdonald",
        "e.g.", "iPhone", "u.s.", "usa", "bcd", "input/output",
        "state-of-the-art", "double//slash", "(word)", "[sample]",
    ]
    separators = [" ", "  ", "\t", " \t "]

    while len(titles) < COUNT:
        words = []
        for _ in range(rng.randint(2, 6)):
            choice = rng.randrange(10)
            if choice < 5:
                word = rng.choice(ordinary)
            elif choice < 7:
                word = rng.choice(small)
            elif choice < 9:
                word = rng.choice(tricky)
            else:
                word = rng.choice(ordinary).upper()

            if rng.random() < 0.18:
                word = rng.choice(["(", "[", '"', "'"]) + word
            if rng.random() < 0.12:
                word += rng.choice([")", "]", '"', "'", ","])
            words.append(word)

        separator = rng.choice(separators)
        title = separator.join(words)
        if rng.random() < 0.12:
            title = rng.choice(["", "  ", "\t"]) + title
        if rng.random() < 0.12:
            title += rng.choice(["", " ", "  ", "\t"])
        titles.append(title)

    return [f"{prefix} {title}" for title in titles[:COUNT]]


def main():
    random.seed(1)
    DATA.mkdir(parents=True, exist_ok=True)
    visible = build_titles("visible", random)
    hidden = build_titles("hidden", random)

    sys.path.insert(0, str(SOURCE))
    from titlecase import titlecase

    paths = {
        "inputs.txt": visible,
        "hidden_inputs.txt": hidden,
    }
    for name, titles in paths.items():
        (DATA / name).write_text("\n".join(titles) + "\n", encoding="utf-8", newline="\n")

    for input_name, output_name in (
        ("inputs.txt", "expected.txt"),
        ("hidden_inputs.txt", "hidden_expected.txt"),
    ):
        inputs = (DATA / input_name).read_text(encoding="utf-8").splitlines()
        outputs = [titlecase(title) for title in inputs]
        (DATA / output_name).write_text(
            "\n".join(outputs) + "\n", encoding="utf-8", newline="\n"
        )


if __name__ == "__main__":
    main()
