"""Generate fixed titlecase inputs and expected output from the original library.

Expected lines are produced only by calling titlecase() in ../python-titlecase.
"""

import random
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = TASK_ROOT / "tests" / "data"
COUNT = 2000

# Small words kept lowercase in the middle of a title.
SMALL_WORDS = (
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "en",
    "for",
    "if",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "v",
    "v.",
    "via",
    "vs",
    "vs.",
)

# Ordinary words mixed in with the tricky cases.
NORMAL_WORDS = (
    "apple",
    "bridge",
    "candle",
    "river",
    "market",
    "garden",
    "silver",
    "window",
    "people",
    "story",
    "light",
    "sound",
    "paper",
    "music",
    "winter",
    "summer",
    "letter",
    "orange",
    "yellow",
    "purple",
    "circle",
    "gentle",
    "bright",
    "quiet",
    "simple",
    "public",
    "early",
    "clear",
    "fresh",
    "sharp",
    "round",
    "final",
    "open",
    "close",
    "harbor",
    "stone",
    "field",
    "cloud",
    "north",
)

# Uncorrected examples from NOTES.md. Outputs are not stored here.
NOTES_WRONG_EXAMPLES = (
    "Line number one",
    "and Line three",
    "a simple tcp and udp wrapper",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "o'grange",
    "l'grange",
    "mcclelland",
    "mr",
    "this is just an example.com",
    "iTunes is great",
    "this v that",
    "word/word",
    "foo//bar",
    "end-to-end",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "Words with all consonants like cnn are acronyms",
    "34th 3rd 2nd",
    "a title",
    "nothing to be afraid of",
    "'by the Way, small word at the start but within quotes.'",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
    "text\twith\ttabs",
    "this shouldn't",
    "get mangled",
    "del.icio.us",
    "example.com",
)

SUBPHRASE_MARKS = (":", ".", ";", "?", "!", "-", "–", "—", "‒", "―")
JOINERS = (" ", " ", " ", "  ", "\t")
CONSONANTS = "bcdfghjklmnpqrstvwxz"
APOSTROPHE_LETTERS = ("d", "l", "o", "D", "L", "O")
HONORIFICS = ("mr", "mrs", "ms", "dr", "MR", "MRS", "MS", "DR", "Mr", "Dr")


def find_original_library():
    """Locate the original python-titlecase package."""
    candidates = [
        (TASK_ROOT / ".." / "python-titlecase").resolve(),
        Path.home() / "Desktop" / "my_first_task" / "python-titlecase",
    ]
    for path in candidates:
        if (path / "titlecase" / "__init__.py").is_file():
            return path
    searched = "\n".join(str(path) for path in candidates)
    raise SystemExit("original python-titlecase not found:\n" + searched)


def load_titlecase():
    library = find_original_library()
    sys.path.insert(0, str(library))
    from titlecase import titlecase

    return titlecase


def normal_token():
    word = random.choice(NORMAL_WORDS)
    roll = random.randrange(3)
    if roll == 0:
        return word.capitalize()
    if roll == 1:
        return word.upper()
    return word


def apostrophe_name():
    stem = random.choice(NORMAL_WORDS)
    suffix = random.choice(("", "'s", "’s"))
    mark = random.choice(("'", "’"))
    return random.choice(APOSTROPHE_LETTERS) + mark + stem + suffix


def mc_name():
    prefix = random.choice(("mc", "MC", "Mc", "mC"))
    return prefix + random.choice(NORMAL_WORDS)


def honorific():
    return random.choice(HONORIFICS)


def domain():
    host = random.choice(NORMAL_WORDS)
    if random.randrange(2) == 0:
        return host + "." + random.choice(("com", "org", "us", "io"))
    return host + ".icio." + random.choice(("us", "com"))


def internal_capital():
    word = random.choice(NORMAL_WORDS)
    if len(word) < 4:
        return "iTunes"
    index = random.randint(1, len(word) - 2)
    return word[:index] + word[index].upper() + word[index + 1 :]


def slash_word():
    left = random.choice(NORMAL_WORDS)
    right = random.choice(NORMAL_WORDS + SMALL_WORDS)
    if random.randrange(3) == 0:
        return left + "//" + right
    return left + "/" + right


def hyphen_word():
    count = random.randint(2, 4)
    parts = [random.choice(NORMAL_WORDS + SMALL_WORDS) for _ in range(count)]
    return "-".join(parts)


def consonant_acronym():
    length = random.randint(3, 5)
    letters = [random.choice(CONSONANTS) for _ in range(length)]
    word = "".join(letters)
    if random.randrange(2) == 0:
        return word.upper()
    return word


def short_ordinary():
    return random.choice(("st", "St", "ST", "by", "at"))


def digit_word():
    number = random.choice((1, 2, 3, 4, 5, 21, 22, 23, 34))
    suffix = random.choice(("st", "nd", "rd", "th"))
    return f"{number}{suffix}"


def initialism():
    letters = [random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(random.randint(2, 4))]
    if random.randrange(2) == 0:
        return ".".join(letters) + "."
    return letters[0] + "." + letters[1]


def subphrase():
    return random.choice(SUBPHRASE_MARKS) + " " + random.choice(SMALL_WORDS)


def quoted_small():
    quote = random.choice(("'", '"', "‘", "“"))
    close = {"'": "'", '"': '"', "‘": "’", "“": "”"}[quote]
    return quote + random.choice(SMALL_WORDS) + " " + random.choice(NORMAL_WORDS) + close


TRICKY_BUILDERS = (
    apostrophe_name,
    mc_name,
    honorific,
    domain,
    internal_capital,
    slash_word,
    hyphen_word,
    consonant_acronym,
    short_ordinary,
    digit_word,
    initialism,
    subphrase,
    quoted_small,
    lambda: random.choice(SMALL_WORDS),
    lambda: random.choice(NOTES_WRONG_EXAMPLES),
)


def tricky_token():
    return random.choice(TRICKY_BUILDERS)()


def join_parts(parts):
    joiner = random.choice(JOINERS)
    return joiner.join(parts)


def mix_with(example):
    """Place one uncorrected example among normal words."""
    if random.randrange(4) == 0:
        return example
    before = [normal_token() for _ in range(random.randint(1, 3))]
    after = [normal_token() for _ in range(random.randint(1, 3))]
    return " ".join(before + [example] + after)


def all_caps_title():
    parts = [normal_token() for _ in range(random.randint(2, 5))]
    parts.insert(random.randint(0, len(parts)), initialism())
    parts.append(random.choice(SMALL_WORDS))
    parts.append(random.choice(("cnn", "html", "gps", "d.c.")))
    return join_parts(parts).upper()


def mixed_title():
    count = random.randint(4, 9)
    tricky_slots = set(random.sample(range(count), k=random.randint(1, 3)))
    if len(tricky_slots) == count:
        tricky_slots.pop()
    parts = [
        tricky_token() if index in tricky_slots else normal_token()
        for index in range(count)
    ]
    if random.randrange(2) == 0:
        parts[0] = random.choice(SMALL_WORDS)
    if random.randrange(2) == 0:
        parts[-1] = random.choice(SMALL_WORDS)
    title = join_parts(parts)
    if random.randrange(8) == 0:
        return title.upper()
    return title


def make_title():
    roll = random.randrange(10)
    if roll == 0:
        title = all_caps_title()
    elif roll == 1:
        title = mix_with(random.choice(NOTES_WRONG_EXAMPLES))
    else:
        title = mixed_title()
    if "\n" in title or "\r" in title or title == "":
        raise RuntimeError("generated title is not a single line")
    return title


def plant_notes_examples(titles):
    """Make sure every NOTES.md example occurs, still mixed with normal words."""
    for example in NOTES_WRONG_EXAMPLES:
        titles[random.randrange(len(titles))] = mix_with(example)
    return titles


def generate(count):
    titles = [make_title() for _ in range(count)]
    return plant_notes_examples(titles)


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            if "\n" in line or "\r" in line:
                raise RuntimeError("refusing to write a multi-line record")
            handle.write(line + "\n")


def expected_for(titlecase, lines):
    results = []
    for line in lines:
        result = titlecase(line)
        if not isinstance(result, str):
            raise RuntimeError("titlecase() did not return a string")
        if "\n" in result or "\r" in result:
            raise RuntimeError("titlecase() returned more than one line")
        results.append(result)
    return results


def main():
    random.seed(1)
    titlecase = load_titlecase()
    inputs = generate(COUNT)
    hidden_inputs = generate(COUNT)
    if inputs == hidden_inputs:
        raise RuntimeError("visible and hidden inputs must differ")
    write_lines(DATA_DIR / "inputs.txt", inputs)
    write_lines(DATA_DIR / "hidden_inputs.txt", hidden_inputs)
    write_lines(DATA_DIR / "expected.txt", expected_for(titlecase, inputs))
    write_lines(DATA_DIR / "hidden_expected.txt", expected_for(titlecase, hidden_inputs))


if __name__ == "__main__":
    main()
