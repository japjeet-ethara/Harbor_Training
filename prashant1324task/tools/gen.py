import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "python-titlecase"

sys.path.insert(0, str(REFERENCE))
from titlecase import titlecase

random.seed(1)

WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over",
    "a", "lazy", "dog", "guide", "story", "book",
    "design", "system", "project", "river", "garden",
    "technology", "science", "history", "music",
    "technology", "university", "language", "computer"
]

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by",
    "en", "for", "if", "in", "of", "on", "or",
    "the", "to", "v.", "via", "vs."
]

SPECIAL_WORDS = [
    "NASA", "USA", "API", "HTML", "iPhone",
    "McDonald", "MacArthur", "O'NEIL", "D'Angelo",
    "Mr.", "Mrs.", "Dr.", "J.R.R.", "U.S.A.",
    "mother-in-law", "state-of-the-art",
    "rock/roll", "and/or", "hello-world",
    "one.two", "AT&T", "CNN", "TCP", "UDP",
    "A.B.", "A.B.C.", "D.C.", "l'grange",
    "o'grange's", "del.icio.us", "example.com",
    "d'Artagnan", "O'Reilly", "McTavish"
]

PUNCTUATION = ["", ",", ".", ":", ";", "!", "?"]

# Curated cases based on the original project's tests.
EDGE_CASES = [
    "a title and/or string",
    "dance with me/let’s face the music and dance",
    "a-b end-to-end two-not-three/three-by-four/five-and",
    "Q&A with steve jobs: 'that's what happens in technology'",
    "What is AT&T's problem?",
    "Words with all consonants like cnn are acronyms",
    "this v that",
    "this vs. that",
    "The SEC's Apple probe: what you need to know",
    "'by the Way, small word at the start but within quotes.'",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "Snakes on a Plane — The TV Edit — The Famous Line",
    "EPISODE 7 — THE FORCE AWAKENS",
    "THE CASE OF X ≤ 7",
    "this is just an example.com",
    "this is something listed on del.icio.us",
    "iTunes should be unmolested",
    "O'Reilly should be untouched",
    "my name is o'reilly",
    "WASHINGTON, D.C. SHOULD BE FIXED",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "Mr McTavish went to MacDonalds",
    "mac mc MAC MC machine",
    "l'grange l'Grange o'grange O'grange",
    "o'grange's O'grange's",
    "mccay-mcbut-mcdo mcdonalds/mcby",
    "mcfoo-bar MCFOO-BAR McFoo-Bar",
    "‘QUOTE’ A GREAT",
    "“YOUNG AND RESTLESS”",
    "EL NIÑO A ARRIVÉ HIER",
    "ÝÆ ÑØ",
    "ýæ ñø",
    "Mr mr Mrs Ms Mss Dr dr",
    "a mix of\tdifferent\u200aspace\u2006characters",
    "crème brûlée",
    "A.B. meets J.R.R. Tolkien",
    "War: and peace; but not the end!",
    "a title with 'quoted small words'",
    "TCP and UDP wrapper",
    "http://foo.com and https://example.com",
]

SEPARATORS = [" ", " ", " ", "\t", "\u00a0", "\u200a", "\u2006"]


def make_title():
    count = random.randint(3, 10)
    words = []

    for _ in range(count):
        choice = random.random()

        if choice < 0.25:
            word = random.choice(SPECIAL_WORDS)
        elif choice < 0.45:
            word = random.choice(SMALL_WORDS)
        else:
            word = random.choice(WORDS)

        casing = random.choice(["lower", "upper", "title", "mixed"])

        if casing == "lower":
            word = word.lower()
        elif casing == "upper":
            word = word.upper()
        elif casing == "title":
            word = word.capitalize()
        else:
            word = "".join(
                c.upper() if random.random() < 0.5 else c.lower()
                for c in word
            )

        words.append(word)

    return "".join(
    word + (random.choice(SEPARATORS) if i < len(words) - 1 else "")
    for i, word in enumerate(words)
)


def generate_unique_titles(count, excluded=None, seeds=None):
    excluded = excluded or set()
    generated = set()

    for title in seeds or []:
        if title not in excluded and len(generated) < count:
            generated.add(title)

    while len(generated) < count:
        title = make_title()
        if title not in excluded:
            generated.add(title)

    return sorted(generated)


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(line + "\n" for line in lines),
        encoding="utf-8"
    )


def main():
    data_dir = ROOT / "tests" / "data"

    midpoint = len(EDGE_CASES) // 2
    visible_seeds = EDGE_CASES[:midpoint]
    hidden_seeds = EDGE_CASES[midpoint:]

    visible = generate_unique_titles(2000, seeds=visible_seeds)
    hidden = generate_unique_titles(
        2000,
        excluded=set(visible),
        seeds=hidden_seeds
    )

    visible_expected = [titlecase(line) for line in visible]
    hidden_expected = [titlecase(line) for line in hidden]

    write_lines(data_dir / "inputs.txt", visible)
    write_lines(data_dir / "expected.txt", visible_expected)
    write_lines(data_dir / "hidden_inputs.txt", hidden)
    write_lines(data_dir / "hidden_expected.txt", hidden_expected)

    print("Generation complete.")
    print("Visible titles:", len(visible))
    print("Hidden titles:", len(hidden))
    print("Visible and hidden inputs are distinct.")
    print("Curated edge cases:", len(EDGE_CASES))


if __name__ == "__main__":
    main()

