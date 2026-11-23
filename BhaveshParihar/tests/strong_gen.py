"""Generate a stronger deterministic hidden titlecase examination."""

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20261121
COUNT = 2400

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
]


def explicit_cases() -> list[str]:
    rows: list[str] = []
    for word in SMALL_WORDS:
        rows.extend([
            f"{word} small title",
            f"middle {word} word",
            f"small title {word}",
            f"opening: {word} phrase",
            f"opening. {word} phrase",
            f"opening; {word} phrase",
            f"opening? {word} phrase",
            f"opening! {word} phrase",
            f"opening - {word} phrase",
        ])

    apostrophe = "'"
    curly = "\u2018"
    rows.extend([
        apostrophe.join(["d", "angelo"]),
        apostrophe.join(["d", "angelo"]) + apostrophe + "s",
        apostrophe.join(["l", "neil"]),
        apostrophe.join(["l", "neil"]) + apostrophe + "s",
        apostrophe.join(["o", "hare"]),
        apostrophe.join(["o", "hare"]) + apostrophe + "s",
        curly.join(["d", "angelo"]),
        curly.join(["l", "neil"]),
        curly.join(["o", "hare"]),
        "mcclelland", "McClelland", "mcmahon", "MacDonald",
        "macintosh", "MCintosh", "mr smith", "mrs smith",
        "ms brown", "dr house", "MR smith", "Mrs SMITH",
        "MS brown", "DR house",
        "A.B.", "D.C.", "U.S.A.", "Ph.D",
        "WASHINGTON, D.C. SHOULD BE FIXED",
        "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
        "cnn", "bbc", "nfl", "html", "sql", "gym", "tv", "St", "st",
        "end-to-end", "and-to-art", "by-the-book", "well-known-state",
        "end/at", "and/or", "by/white", "vs/at",
        "http://foo.com", "https://example.com/a",
        "http://foo.com//bar", "ftp://host/path",
        "iTunes", "iPhone", "eBay", "YouTube", "macOS",
        "node.js", "example.com", "A.B.C", "APIv2", "x86_64", "A1B",
        "small title.", "small title!", "small title?",
        "small title...", "...the end", "--- at title",
        "title \u2013 the end",
        "text\twith\ttabs",
        "text  with  repeated   spaces",
        "text\u00a0with\u00a0nonbreaking\u00a0spaces",
        "left  \t  right", "\tleading title", "trailing title\t",
        "crème brûlée", "élan vital", "東京 title",
        "naïve résumé", "über cool", "straße bridge",
        "Dvořák concerto", "Ångström article",
        "A VERY LONG TITLE WITH MANY SMALL WORDS AND A FEW CNN BBC NFL "
        "TOKENS ABOUT HTTP://FOO.COM AND/OR END-TO-END",
        "Title?!;: - a small phrase ... (parenthetical) \u2013 the end",
        "The ::quick:: brown-fox jumps/over the lazy-dog: an example",
    ])
    return list(dict.fromkeys(rows))


def generate(count: int) -> list[str]:
    random.seed(SEED)
    normal = [
        "simple", "title", "string", "wrapper", "problem", "words", "line",
        "start", "end", "quotes", "trick", "perhaps", "number", "three",
        "afraid", "nothing", "small", "garden", "river", "bridge", "yellow",
        "orange", "quiet", "people", "summer", "winter", "monday", "chapter",
        "notes", "final", "text", "tabs", "iTunes", "eBay", "macOS",
        "crème", "naïve", "résumé",
    ]
    curly = "\u2018"
    apostrophe = "'"
    tricky = [
        "D.C.", "U.S.A.", "l" + curly + "grange",
        "o" + curly + "hare", "d" + apostrophe + "angelo",
        "McClelland", "macdonald", "mcintosh", "mr", "mrs", "ms", "dr",
        "example.com", "node.js", "http://foo.com",
        "https://example.com/a", "and/or", "end-to-end",
        "cnn", "bbc", "nfl", "St", "st", "A.B.", "iPhone", "YouTube",
    ]

    rows = explicit_cases()
    seen = set(rows)
    while len(rows) < count:
        row: list[str] = []
        for _ in range(random.randint(3, 9)):
            choice = random.randrange(10)
            if choice < 5:
                word = random.choice(normal)
                style = random.randrange(3)
                if style == 1:
                    word = word.upper()
                elif style == 2:
                    word = word.capitalize()
                row.append(word)
            elif choice < 7:
                row.append(random.choice(SMALL_WORDS))
            else:
                row.append(random.choice(tricky))

        separator = random.choice([" ", " ", "  ", "\t", "\u00a0"])
        line = separator.join(row)
        if random.randrange(5) == 0:
            line = line.upper()
        if random.randrange(5) == 0:
            separator_phrase = random.choice([
                ": ", ". ", "; ", "? ", "! ", " - ", " \u2013 ",
            ])
            line += separator_phrase + random.choice(SMALL_WORDS) + " " + random.choice(normal)
        if "\n" not in line and "\r" not in line and line not in seen:
            seen.add(line)
            rows.append(line)
    return rows


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            if "\n" in line or "\r" in line:
                raise SystemExit(f"refusing to write multiline record to {path}")
            handle.write(line)
            handle.write("\n")


def main() -> None:
    source = HERE.parent / "environment" / "python-titlecase"
    sys.path.insert(0, str(source))
    from titlecase import titlecase

    strong = generate(COUNT)
    first = [titlecase(line) for line in strong]
    second = [titlecase(line) for line in strong]
    if first != second:
        raise SystemExit("reference output was not stable across two runs")
    if len(strong) != COUNT or len(first) != COUNT:
        raise SystemExit("strong exam count mismatch")

    data = HERE / "data"
    write_lines(data / "strong_hidden_inputs.txt", strong)
    write_lines(data / "strong_hidden_expected.txt", first)
    print(f"wrote {COUNT} strong hidden inputs and answers")


if __name__ == "__main__":
    main()
