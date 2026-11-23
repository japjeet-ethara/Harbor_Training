"""Generate fixed titlecase fixtures.

Inputs are random titles seeded with random.seed(1). Expected lines are the
return values of the original python-titlecase titlecase(), one argument only.
NOTES.md lists no example whose recorded output disagrees with that function.
"""

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
DATA = HERE / "data"

# Single-line inputs from NOTES.md. Rules 1-3 are shown there as multi-line
# strings; each physical line is its own title. "Examples the notes got wrong"
# is empty.
NOTE_LINES = [
    "this shouldn't",
    "get mangled",
    "Line number one",
    "and Line three",
    "",
    "text\twith\ttabs",
    "a simple tcp and udp wrapper",
    "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
    "my name is o'reilly",
    "l'grange l'grange l'Grange l'Grange",
    "oblon, spivak, mcclelland, maier & neustadt",
    "Mr mr Mrs Ms Dr dr",
    "this is just an example.com",
    "iTunes should be unmolested",
    "this v that",
    "a title and/or string",
    "end-to-end",
    "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
    "Words with all consonants like cnn are acronyms",
    "Q&A with steve jobs: 'that's what happens in technology'",
    "a thing",
    "Small word at end is nothing to be afraid of",
    "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
]

NORMAL = [
    "apple", "bridge", "camera", "document", "editor", "forest", "garden",
    "harbor", "island", "journal", "kitchen", "library", "market", "notebook",
    "orange", "paper", "quarter", "river", "silver", "table", "umbrella",
    "village", "window", "yellow", "title", "string", "example", "problem",
    "music", "plane", "probe", "deal", "report", "history", "science",
    "people", "number", "system", "program", "company", "family", "school",
    "state", "world", "information", "government", "health", "water", "book",
    "shouldn't", "addressed", "unmolested", "washington", "technology",
]

SMALL = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
    "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]

SEPARATORS = [": ", ". ", "; ", "? ", "! ", " - ", " – ", " ‒ ", " — ", " ― "]
CONSONANTS = "bcdfghjklmnpqrstvwxz"


def original_package():
    candidates = [
        (TASK / "../python-titlecase").resolve(),
        (TASK.parents[1] / "python-titlecase").resolve(),
    ]
    for path in candidates:
        if (path / "titlecase" / "__init__.py").is_file():
            return path
    raise SystemExit("original python-titlecase package not found")


def pick(items):
    return random.choice(items)


def variant(word):
    return pick((word, word.lower(), word.upper(), word.capitalize()))


def glue(parts):
    gap = pick((" ", " ", "  ", "\t", " \t"))
    return gap.join(parts)


def normal_words(count):
    return [variant(pick(NORMAL)) for _ in range(count)]


def normal():
    return glue(normal_words(random.randint(2, 10)))


def with_tabs():
    return "\t".join(normal_words(random.randint(2, 6)))


def all_caps():
    tokens = [word.upper() for word in normal_words(random.randint(3, 8))]
    if random.random() < 0.75:
        initials = pick(("A.B", "D.C.", "U.S.", "A.B.C", "D.C"))
        tokens.insert(random.randrange(len(tokens) + 1), initials)
    return " ".join(tokens)


def apostrophe():
    vowel = pick(("o", "O")) + pick(("'", "‘")) + pick(("reilly", "brien", "neil", "reilly's"))
    consonant = pick(("d", "l", "D", "L")) + pick(("'", "‘")) + pick(
        ("grange", "angelo", "clock", "Grange", "grange's")
    )
    return glue(normal_words(random.randint(1, 3)) + [vowel, consonant] + normal_words(random.randint(0, 2)))


def mc_name():
    prefix = pick(("Mc", "mc", "MC", "mC"))
    rest = pick(("clelland", "donald", "coy", "intosh", "mahon", "Clelland"))
    token = prefix + rest
    return glue([pick(NORMAL), token, pick(("&", "and")), pick(NORMAL)])


def honorific():
    titles = [pick(("Mr", "mr", "MR", "Mrs", "Ms", "ms", "Dr", "dr", "DR", "M", "m")) for _ in range(random.randint(2, 6))]
    return glue(titles + normal_words(random.randint(0, 3)))


def hostname():
    host = pick(("example.com", "EXAMPLE.COM", "news.example.co.uk", "a.b", "a.b.c", "i.imgur.com"))
    return glue(normal_words(random.randint(1, 4)) + [host] + normal_words(random.randint(0, 3)))


def internal_caps():
    token = pick(("iTunes", "iPhone", "eBay", "YouTube", "IPv4", "MacOS", "FedEx", "AT&T"))
    return glue(normal_words(random.randint(1, 4)) + [token] + normal_words(random.randint(0, 3)))


def small_middle():
    words = normal_words(random.randint(1, 3)) + [pick(SMALL)] + normal_words(random.randint(1, 3))
    return glue(words)


def slash_word():
    if random.random() < 0.35:
        token = pick(("http://example.com", "a//b", "foo//bar", "n//a"))
    else:
        token = "/".join(pick(SMALL + NORMAL) for _ in range(pick((2, 3))))
    return glue(normal_words(random.randint(0, 3)) + [token] + normal_words(random.randint(0, 3)))


def hyphen_word():
    parts = [pick(SMALL + NORMAL) for _ in range(pick((2, 3, 4)))]
    token = "-".join(variant(part) for part in parts)
    return glue(normal_words(random.randint(0, 2)) + [token] + normal_words(random.randint(0, 2)))


def acronym():
    length = pick((2, 2, 3, 4, 5, 6))
    token = "".join(pick(CONSONANTS) for _ in range(length))
    if random.random() < 0.3:
        token = pick(("St", "st", "ST", "cnn", "html", "bbc", "by", "my", "rhythm"))
    return glue(normal_words(random.randint(1, 4)) + [variant(token)] + normal_words(random.randint(1, 3)))


def leading_punct():
    token = pick(("'", '"', "(", "*")) + pick(NORMAL)
    fancy = pick(("Q&A", "AT&T", "34th", "3rd", "'that's", '"trick'))
    return glue([token, fancy] + normal_words(random.randint(1, 5)))


def small_first():
    first = pick(SMALL)
    if random.random() < 0.4:
        first = pick(("'", '"', "(")) + first
    return glue([first] + normal_words(random.randint(1, 6)))


def small_last():
    last = pick(SMALL)
    if random.random() < 0.5:
        last += pick((".", ",", "?", "!", ";"))
    return glue(normal_words(random.randint(2, 6)) + [last])


def subphrase():
    head = glue(normal_words(random.randint(2, 6)))
    tail = glue([pick(SMALL)] + normal_words(random.randint(1, 4)))
    return head + pick(SEPARATORS) + tail


def note_line():
    return pick(NOTE_LINES)


def combo():
    return glue([
        normal(),
        pick((apostrophe, mc_name, honorific, hostname, internal_caps, slash_word, hyphen_word, acronym))(),
    ])


BUILDERS = (
    normal, normal, normal,
    with_tabs, all_caps, apostrophe, mc_name, honorific, hostname,
    internal_caps, small_middle, slash_word, hyphen_word, acronym,
    leading_punct, small_first, small_last, subphrase, note_line, combo,
)


def one_title():
    line = pick(BUILDERS)()
    if "\n" in line or "\r" in line:
        raise SystemExit("generated title contains a line break")
    return line


def write_lines(path, lines):
    payload = "\n".join(lines) + "\n"
    path.write_bytes(payload.encode("utf-8"))


def expect(titlecase, lines):
    results = []
    for line in lines:
        result = titlecase(line)
        if not isinstance(result, str) or "\n" in result or "\r" in result:
            raise SystemExit("titlecase() did not return one line")
        results.append(result)
    return results


def main():
    random.seed(1)
    sys.path.insert(0, str(original_package()))
    from titlecase import titlecase

    public = [one_title() for _ in range(2000)]
    hidden = [one_title() for _ in range(2000)]
    if public == hidden:
        raise SystemExit("hidden inputs matched the public inputs")

    DATA.mkdir(parents=True, exist_ok=True)
    write_lines(DATA / "inputs.txt", public)
    write_lines(DATA / "hidden_inputs.txt", hidden)
    write_lines(DATA / "expected.txt", expect(titlecase, public))
    write_lines(DATA / "hidden_expected.txt", expect(titlecase, hidden))


if __name__ == "__main__":
    main()
