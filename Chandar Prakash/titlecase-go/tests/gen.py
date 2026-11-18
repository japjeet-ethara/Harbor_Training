import importlib.util
import random
from pathlib import Path


random.seed(1)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT.parent / "python-titlecase" / "titlecase" / "__init__.py"
DATA = ROOT / "tests" / "data"

NORMAL_WORDS = [
    "bright", "quiet", "river", "garden", "silver", "morning", "window",
    "paper", "cloud", "gentle", "music", "forest", "little", "story",
    "yellow", "winter", "travel", "simple", "curious", "stone", "blue",
    "market", "open", "shadow", "green", "letter", "fresh", "evening",
]

TRICKY_CASES = [
    "Line number one",
    "a simple tcp and udp wrapper",
    "WASHINGTON, D.C. SHOULD BE FIXED",
    "my name is o'reilly",
    "mcclelland",
    "mr mrs ms dr",
    "this is just an example.com",
    "i.e. iTunes AT&T",
    "pride and prejudice",
    "word/word",
    "end-to-end",
    "THIS IS ALL CAPS",
    "words like cnn are acronyms",
    "hello world",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "text\twith\ttabs",
    "a an and as at but by en for if in of on or the to v v. via vs vs.",
]


def load_original_titlecase():
    if not ORIGINAL.is_file():
        raise FileNotFoundError("Original titlecase implementation not found: " + str(ORIGINAL))

    spec = importlib.util.spec_from_file_location("_original_titlecase", ORIGINAL)
    if spec is None or spec.loader is None:
        raise ImportError("Could not load original titlecase implementation: " + str(ORIGINAL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.titlecase


def generate_title(index, used):
    while True:
        if index < len(TRICKY_CASES):
            title = TRICKY_CASES[index]
        else:
            parts = random.choices(TRICKY_CASES, k=random.randint(1, 3))
            before = random.choices(NORMAL_WORDS, k=random.randint(1, 3))
            between = random.choices(NORMAL_WORDS, k=random.randint(0, 3))
            after = random.choices(NORMAL_WORDS, k=random.randint(1, 3))
            title = " ".join(before + [parts[0]] + between + parts[1:] + after)

        if title not in used:
            used.add(title)
            return title

        before = random.choices(NORMAL_WORDS, k=random.randint(1, 3))
        after = random.choices(NORMAL_WORDS, k=random.randint(1, 3))
        title = " ".join(before + [random.choice(TRICKY_CASES)] + after)
        if title not in used:
            used.add(title)
            return title


def write_lines(path, lines):
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(lines))
        output.write("\n")


def main():
    titlecase = load_original_titlecase()
    DATA.mkdir(parents=True, exist_ok=True)
    used = set()

    for prefix in ("", "hidden_"):
        titles = [generate_title(index, used) for index in range(2000)]
        expected = [titlecase(title) for title in titles]
        write_lines(DATA / (prefix + "inputs.txt"), titles)
        write_lines(DATA / (prefix + "expected.txt"), expected)


if __name__ == "__main__":
    main()
