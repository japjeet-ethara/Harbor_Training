import random
import sys
from pathlib import Path


NORMAL_WORDS = [
    "amber", "ancient", "bridge", "bright", "brook", "calm", "castle",
    "cloud", "coast", "forest", "garden", "glass", "golden", "harbor",
    "island", "journey", "lantern", "morning", "mountain", "quiet",
    "river", "silver", "stone", "summer", "valley", "winter",
]

TRICKY_CASES = [
    "hello world",
    "the lord of the rings",
    "in the",
    "a: and then",
    "a; and then",
    "a? and then",
    "a! and then",
    "iPhone and eBay",
    "d'artagnan o'neill",
    "l'enfant",
    "mcdonald and mcintosh",
    "mr smith and mrs jones",
    "ms and dr",
    "rock/roll and black/white",
    "state-of-the-art",
    "brrr",
    "THE WAR OF THE WORLDS",
    "A. B. C. and USA",
    "a - and the end",
    "this is a test of punctuation: and more",
]


def random_title():
    if random.random() < 0.45:
        tricky = random.choice(TRICKY_CASES)
        prefix = " ".join(
            random.choices(NORMAL_WORDS, k=random.randint(0, 3))
        )
        suffix = " ".join(
            random.choices(NORMAL_WORDS, k=random.randint(0, 3))
        )
        parts = [part for part in (prefix, tricky, suffix) if part]
        title = " ".join(parts)
    else:
        words = random.choices(NORMAL_WORDS, k=random.randint(2, 9))
        if random.random() < 0.5:
            words.insert(random.randrange(len(words) + 1), random.choice([
                "a", "an", "and", "as", "at", "but", "by", "for", "in",
                "of", "on", "or", "the", "to", "via", "vs",
            ]))
        title = " ".join(words)

    if random.random() < 0.2:
        title = title.upper()
    elif random.random() < 0.2:
        title = title.title()
    return title


def unique_titles(count, used):
    titles = []
    while len(titles) < count:
        title = random_title()
        if title not in used:
            used.add(title)
            titles.append(title)
    return titles


def write_pair(data_dir, input_name, expected_name, titles, titlecase):
    (data_dir / input_name).write_text(
        "".join(title + "\n" for title in titles), encoding="utf-8"
    )
    results = [titlecase(title) for title in titles]
    (data_dir / expected_name).write_text(
        "".join(result + "\n" for result in results), encoding="utf-8"
    )


def main():
    random.seed(1)
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "python-titlecase"))
    from titlecase import titlecase

    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    used = set()
    inputs = unique_titles(2000, used)
    hidden_inputs = unique_titles(2000, used)
    write_pair(data_dir, "inputs.txt", "expected.txt", inputs, titlecase)
    write_pair(data_dir, "hidden_inputs.txt", "hidden_expected.txt", hidden_inputs, titlecase)


if __name__ == "__main__":
    main()
