import random
import sys
from pathlib import Path


random.seed(1)

REPO_DIR = Path(__file__).resolve().parents[1]


TRICKY_CASES = (
    "api",
    "NASA",
    "o'clock",
    "mcDonald",
    "dr jekyll",
    "iPhone",
    "a tale of two cities",
    "foo/bar",
    "state-of-the-art",
    "brr",
    "hello world",
)

NORMAL_WORDS = (
    "a",
    "bright",
    "curious",
    "day",
    "garden",
    "in",
    "little",
    "mountain",
    "near",
    "old",
    "quiet",
    "river",
    "story",
    "under",
    "with",
    "yellow",
)


def generate_titles():
    titles = list(TRICKY_CASES)
    while len(titles) < 2000:
        words = [
            random.choice(NORMAL_WORDS)
            for _ in range(random.randint(2, 7))
        ]
        case = random.choice(TRICKY_CASES)
        words.insert(random.randrange(len(words) + 1), case)
        titles.append(" ".join(words))
    return titles


def write_lines(path, lines):
    with path.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write("\n".join(lines))
        output_file.write("\n")


def main():
    sys.path.insert(0, str(REPO_DIR.parent / "python-titlecase"))
    from titlecase import titlecase

    data_dir = REPO_DIR / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    inputs = generate_titles()
    hidden_inputs = generate_titles()

    write_lines(data_dir / "inputs.txt", inputs)
    write_lines(data_dir / "hidden_inputs.txt", hidden_inputs)
    write_lines(data_dir / "expected.txt", [titlecase(line) for line in inputs])
    write_lines(
        data_dir / "hidden_expected.txt",
        [titlecase(line) for line in hidden_inputs],
    )


if __name__ == "__main__":
    main()
