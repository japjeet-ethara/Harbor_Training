"""Generate fixed titlecase inputs and the original Python results."""

import os
import random
import re
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COUNT = 2000

ORDINARY = (
    "apple", "bridge", "castle", "river", "market", "garden", "silver",
    "harbor", "winter", "summer", "copper", "velvet", "lantern", "meadow",
    "oracle", "pebble", "quartz", "shadow", "timber", "voyage", "forest",
    "island", "kettle", "mirror", "needle", "piano", "rocket", "saddle",
    "temple", "violet", "window", "basket", "candle", "dragon", "engine",
    "falcon", "glove", "hammer", "insect", "jacket",
)
SMALL = (
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
)
SMALL_POSITIONS = (
    "start", "middle", "end", ":", ".", ";", "?", "!", "-", "\u2013", "\u2014",
)
SMALL_WORD = re.compile(
    r"^(?:a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.|v|via|vs\.|vs)$",
    re.IGNORECASE,
)
INITIALS = ("A.B.", "A.B.", "A.B", "A.", "J.R.R.", "U.S.")
INTERNAL = ("iTunes", "AT&T", "eBay")
APOSTROPHES = (
    "l'grange", "o'neil", "d'artagnan",
    "l\u2018grange", "o\u2018neil", "d\u2018artagnan",
    "L'GRANGE", "O'NEIL", "D'ARTAGNAN", "l'grange's",
)
MC_WORDS = ("mcdonald", "MCDONALD", "mcintyre", "MCBRIDE", "mckinley", "MCMAHON")
HONORIFICS = ("mr", "mrs", "ms", "dr", "MR", "MRS", "MS", "DR")
PERIOD_WORDS = ("example.com", "i.e", "i.e.", "docs.python.org")
URLS = (
    "http://example.com/the-page",
    "https://example.com/a/b",
    "www.example.com",
    "http://foo.com/path",
    "https://news.example.org/story",
    "www.shop.example.net",
)
EMAILS = ("bob@example.com", "ada@mail.example.org", "dev@example.co.uk")
TAILS = ("", ",", ".", ";", "?", "!")
ACRONYMS = ("cnn", "html", "nyc", "rhythm", "st")
LEADS = ("(", '"', "'", "[")
ACCENTS = (
    "caf\u00e9", "ni\u00f1o", "\u00fcber", "r\u00e9sum\u00e9",
    "se\u00f1or", "m\u00fcller", "\u00e9l", "fa\u00e7ade",
)


def one():
    return random.choice(ORDINARY)


def phrase(n):
    return " ".join(one() for _ in range(n))


def add_extra(line, attempt, upper=False):
    if not attempt:
        return line
    word = ORDINARY[attempt % len(ORDINARY)]
    if upper:
        word = word.upper()
    return f"{line} {word}"


def build_small(k, attempt):
    sw = SMALL[k % len(SMALL)]
    pos = SMALL_POSITIONS[(k // len(SMALL)) % len(SMALL_POSITIONS)]
    left = phrase(2)
    right = phrase(2)
    extra = ""
    if attempt:
        extra = " " + ORDINARY[attempt % len(ORDINARY)]
    if pos == "start":
        return f"{sw} {left} {right}{extra}"
    if pos == "middle":
        return f"{left} {sw} {right}{extra}"
    if pos == "end":
        return f"{left} {right}{extra} {sw}"
    if pos in "-–\u2013\u2014":
        return f"{left} {pos} {sw} {right}{extra}"
    return f"{left}{pos} {sw} {right}{extra}"


def build_upper(k, attempt):
    if k % 3 == 2:
        sw = SMALL[k % len(SMALL)].upper()
        line = f"{one().upper()} {sw} {one().upper()} {one().upper()}"
    else:
        initial = INITIALS[(k // 3) % len(INITIALS)]
        words = [one().upper() for _ in range(3)]
        words.insert(1, initial)
        line = " ".join(words)
    return add_extra(line, attempt, upper=True)


def build_internal(k, attempt):
    return add_extra(f"{phrase(2)} {INTERNAL[k % len(INTERNAL)]} {phrase(2)}", attempt)


def build_apos(k, attempt):
    return add_extra(f"{phrase(2)} {APOSTROPHES[k % len(APOSTROPHES)]} {phrase(1)}", attempt)


def build_mc(k, attempt):
    return add_extra(f"{phrase(1)} {MC_WORDS[k % len(MC_WORDS)]} {phrase(2)}", attempt)


def build_honorific(k, attempt):
    return add_extra(f"{HONORIFICS[k % len(HONORIFICS)]} {phrase(3)}", attempt)


def build_period(k, attempt):
    return add_extra(f"{phrase(2)} {PERIOD_WORDS[k % len(PERIOD_WORDS)]} {phrase(1)}", attempt)


def build_url(k, attempt):
    if k % 2 == 0:
        token = URLS[(k // 2) % len(URLS)]
    else:
        token = EMAILS[(k // 2) % len(EMAILS)]
    token += TAILS[k % len(TAILS)]
    return add_extra(f"{phrase(1)} {token} {phrase(2)}", attempt)


def build_slash(k, attempt):
    if k % 2 == 0:
        token = f"{one()}/{one()}"
    else:
        token = f"{one()}//{one()}"
    return add_extra(f"{phrase(1)} {token} {phrase(1)}", attempt)


def build_hyphen(k, attempt):
    if k % 4 == 0:
        token = "end-to-end"
    else:
        token = f"{one()}-{SMALL[k % len(SMALL)]}-{one()}"
    return add_extra(f"{phrase(1)} {token} {phrase(1)}", attempt)


def build_acronym(k, attempt):
    return add_extra(f"{phrase(2)} {ACRONYMS[k % len(ACRONYMS)]} {phrase(1)}", attempt)


def build_lead(k, attempt):
    return add_extra(f"{LEADS[k % len(LEADS)]}{phrase(3)}", attempt)


def build_spacing(k, attempt):
    del k
    words = [one() for _ in range(4)]
    line = f"{words[0]}\t{words[1]}  {words[2]} {words[3]}"
    return add_extra(line, attempt)


def build_accent(k, attempt):
    return add_extra(f"{phrase(1)} {ACCENTS[k % len(ACCENTS)]} {phrase(2)}", attempt)


def build_ordinary(k, attempt):
    return add_extra(phrase(3 + (k % 3)), attempt)


BUILDERS = (
    build_small, build_small, build_small, build_small,
    build_upper, build_internal, build_apos, build_mc, build_honorific,
    build_period, build_url, build_slash, build_hyphen, build_acronym,
    build_lead, build_spacing, build_accent, build_ordinary,
)


def is_valid(line):
    if not line or "\n" in line or "\r" in line:
        return False
    if line != line.strip(" ") or line[0].isspace() or line[-1].isspace():
        return False
    return True


def unique(builder, k, seen):
    for attempt in range(40):
        line = builder(k, attempt)
        if is_valid(line) and line not in seen:
            seen.add(line)
            return line
    raise RuntimeError(f"no unique line from {builder.__name__}")


def generate(n, seen):
    counters = {}
    lines = []
    step = 0
    while len(lines) < n:
        builder = BUILDERS[step % len(BUILDERS)]
        k = counters.get(builder, 0)
        lines.append(unique(builder, k, seen))
        counters[builder] = k + 1
        step += 1
    return lines


def tokens(line):
    return re.split(r"\s+", line)


def small_after(line, mark, own_token):
    parts = line.split(" ")
    for index, part in enumerate(parts[:-1]):
        if not SMALL_WORD.match(parts[index + 1]):
            continue
        if own_token and part == mark:
            return True
        if not own_token and part.endswith(mark) and part != mark:
            return True
    return False


def has_token(line, word):
    return any(part == word for part in tokens(line))


def has_honorific(line, word):
    return any(part.lower() == word for part in tokens(line))


def link_then_punct(line):
    for part in tokens(line):
        if part[-1:] not in ",.;?!":
            continue
        body = part[:-1]
        if "://" in body or body.startswith("www.") or "@" in body:
            return True
    return False


def single_slash_word(line):
    for part in tokens(line):
        if "/" in part and "//" not in part:
            return True
    return False


def double_slash_word(line):
    for part in tokens(line):
        if "//" in part and "://" not in part:
            return True
    return False


def is_upper_line(line):
    letters = [char for char in line if char.isalpha()]
    return bool(letters) and line == line.upper()


def dotted_initials(line):
    return re.search(r"(?<![A-Za-z])[A-Z]\.[A-Z]", line) is not None


def check_mix(lines):
    checks = (
        ("small at start", lambda line: SMALL_WORD.match(tokens(line)[0]) is not None),
        ("small in middle", lambda line: any(SMALL_WORD.match(part) for part in tokens(line)[1:-1])),
        ("small at end", lambda line: SMALL_WORD.match(tokens(line)[-1]) is not None),
        ("small after colon", lambda line: small_after(line, ":", False)),
        ("small after period", lambda line: small_after(line, ".", False)),
        ("small after semicolon", lambda line: small_after(line, ";", False)),
        ("small after question", lambda line: small_after(line, "?", False)),
        ("small after bang", lambda line: small_after(line, "!", False)),
        ("small after hyphen", lambda line: small_after(line, "-", True)),
        ("small after en dash", lambda line: small_after(line, "\u2013", True)),
        ("small after em dash", lambda line: small_after(line, "\u2014", True)),
        ("uppercase line", is_upper_line),
        ("dotted initials", dotted_initials),
        ("A.B.", lambda line: "A.B." in line),
        ("iTunes", lambda line: "iTunes" in line),
        ("AT&T", lambda line: "AT&T" in line),
        ("eBay", lambda line: "eBay" in line),
        ("l'grange", lambda line: "l'grange" in line or "L'GRANGE" in line),
        ("o'neil", lambda line: "o'neil" in line or "O'NEIL" in line),
        ("d'artagnan", lambda line: "d'artagnan" in line or "D'ARTAGNAN" in line),
        ("curly apostrophe", lambda line: "\u2018" in line),
        ("mcdonald", lambda line: "mcdonald" in line),
        ("MCDONALD", lambda line: "MCDONALD" in line),
        ("mr", lambda line: has_honorific(line, "mr")),
        ("mrs", lambda line: has_honorific(line, "mrs")),
        ("ms", lambda line: has_honorific(line, "ms")),
        ("dr", lambda line: has_honorific(line, "dr")),
        ("example.com", lambda line: has_token(line, "example.com")),
        ("i.e", lambda line: has_token(line, "i.e") or has_token(line, "i.e.")),
        ("http", lambda line: "http://" in line),
        ("https", lambda line: "https://" in line),
        ("www", lambda line: "www." in line),
        ("email", lambda line: "@" in line),
        ("link punctuation", link_then_punct),
        ("single slash", single_slash_word),
        ("double slash", double_slash_word),
        ("end-to-end", lambda line: "end-to-end" in line),
        ("cnn", lambda line: has_token(line, "cnn")),
        ("html", lambda line: has_token(line, "html")),
        ("nyc", lambda line: has_token(line, "nyc")),
        ("rhythm", lambda line: has_token(line, "rhythm")),
        ("st", lambda line: has_token(line, "st")),
        ("lead paren", lambda line: line.startswith("(")),
        ("lead quote", lambda line: line.startswith('"')),
        ("lead apos", lambda line: line.startswith("'")),
        ("lead bracket", lambda line: line.startswith("[")),
        ("tab", lambda line: "\t" in line),
        ("double space", lambda line: "  " in line),
        ("accent e", lambda line: "\u00e9" in line),
        ("accent n", lambda line: "\u00f1" in line),
        ("accent u", lambda line: "\u00fc" in line),
    )
    short = []
    for name, pred in checks:
        found = sum(1 for line in lines if pred(line))
        if found < 12:
            short.append(f"{name}={found}")
    if short:
        raise RuntimeError("case appeared too rarely: " + ", ".join(short))


def write_lines(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line)
            handle.write("\n")


def results_for(lines, titlecase):
    results = []
    for line in lines:
        result = titlecase(line)
        if "\n" in result or "\r" in result:
            raise RuntimeError("titlecase returned a line break")
        results.append(result)
    return results


def _titlecase():
    repo_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "environment", "repo")
    )
    sys.path.insert(0, repo_dir)
    from titlecase import titlecase

    return titlecase


def main():
    titlecase = _titlecase()
    random.seed(1)
    seen = set()
    inputs = generate(COUNT, seen)
    hidden = generate(COUNT, seen)
    if len(inputs) != COUNT or len(hidden) != COUNT:
        raise RuntimeError("unexpected line count")
    if len(set(inputs)) != COUNT or len(set(hidden)) != COUNT:
        raise RuntimeError("titles are not distinct")
    if set(inputs) & set(hidden):
        raise RuntimeError("input files share a line")
    for line in inputs + hidden:
        if not is_valid(line):
            raise RuntimeError("invalid title")
    check_mix(inputs)
    check_mix(hidden)
    write_lines(os.path.join(DATA_DIR, "inputs.txt"), inputs)
    write_lines(os.path.join(DATA_DIR, "expected.txt"), results_for(inputs, titlecase))
    write_lines(os.path.join(DATA_DIR, "hidden_inputs.txt"), hidden)
    write_lines(os.path.join(DATA_DIR, "hidden_expected.txt"), results_for(hidden, titlecase))


if __name__ == "__main__":
    main()
