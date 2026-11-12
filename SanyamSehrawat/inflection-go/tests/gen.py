#!/usr/bin/env python3
"""Generate the test lines and freeze the expected answers.

    python tests/gen.py

Writes four files into tests/data/:

    inputs.txt          2000 lines  (visible set, used while developing the oracle)
    expected.txt        their answers
    hidden_inputs.txt   2000 different lines (the set the verifier grades on)
    hidden_expected.txt their answers

Each input line is "<function>\\t<argument>". The answers are never written by
hand: every one comes from running the ORIGINAL inflection (the pinned snapshot
in environment/inflection). Output is deterministic: random.seed(1).
"""
import hashlib
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent / "environment" / "inflection"
DATA = HERE / "data"
N = 2000

# The snapshot is inflection 0.5.1, commit 88eefaacf7d0caaa701af7c8ab2d0ab3f17086f1.
PINNED_SHA256 = "b6b089383f812e6986f917a3c689722c54b8a69f04ded2ac32b627cbcfdaf35e"


def load_original():
    source = REPO / "inflection" / "__init__.py"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != PINNED_SHA256:
        sys.exit(f"{source} is not the pinned snapshot (sha256 {digest})")
    sys.path.insert(0, str(REPO))
    # A __pycache__ folder here would end up in the agent's image.
    sys.dont_write_bytecode = True
    import inflection

    return {
        "camelize": inflection.camelize,
        "camelize_lower": lambda s: inflection.camelize(s, False),
        "dasherize": inflection.dasherize,
        "humanize": inflection.humanize,
        "ordinalize": lambda s: inflection.ordinalize(int(s)),
        "parameterize": inflection.parameterize,
        "parameterize_underscore": lambda s: inflection.parameterize(s, "_"),
        "pluralize": inflection.pluralize,
        "singularize": inflection.singularize,
        "tableize": inflection.tableize,
        "titleize": inflection.titleize,
        "underscore": inflection.underscore,
    }


NOUNS = """post user comment category city query day key boy toy fly spy story party
quiz ox oxen mouse mice louse lice passerby passersby matrix matrices vertex vertices index
indices box fox church match kiss boss wish dish bush hive wolf half shelf calf knife wife life
safe chief roof analysis analyses basis bases crisis crises diagnosis thesis theses synopsis
prognosis parenthesis datum data medium media bacterium buffalo potato tomato hero photo piano
bus buses alias aliases status statuses octopus octopi virus viri axis axes testis testes
person people man men woman women human humans child children sex sexes move moves cow kine
zombie zombies equipment fish goldfish sheep series species money rice jeans information news
movie movies shoe shoes database databases tive hive archive perspective cookie quizzes
glass address process bonus campus census atlas canvas iris lens bias gas plus focus
salesman fireman roman german shaman talisman batman human cayman ottoman
tomatoes potatoes heroes echoes vetoes cargoes dwarf scarf leaf thief loaf elf half scarves
dwarves elves selves knives leaves wives lives sheaves""".split()

PREFIXES = "Camel Sales Field Big Little Black Red Blue Super Data Api Http Json User Admin Mega Gold".split()

WORDS = """device type employee salary author raiders of the lost ark man from boondocks x men last
stand without a past egg and ham fancy category raw scaled scorer html parser get http response code
io error my api key user id account number active record base view helper xml http request ssl
error url path first name last name zip code created at updated at is admin has many belongs to
puni donald e knuth the quick brown fox jumps over lazy dog hello world foo bar baz""".split()

CAMEL = """DeviceType IOError HTTPServer getHTTPResponseCode XMLHttpRequest URLPath SSLError
ActiveRecord ViewHelper RawScaledScorer fancyCategory TheManWithoutAPast iPhone eBay
ABCDefGHI aB aBC ABc A1B2 HTML5Parser Base64Encoder MyAPIKey userID utf8String JSONData
X ID Id iD SomeXMLData already_snake Mixed_Case_Words CamelCase_with_snake""".split()

PUNCT = list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def rand_case(w):
    r = random.random()
    if r < 0.6:
        return w
    if r < 0.72:
        return w.upper()
    if r < 0.86:
        return w.capitalize()
    return "".join(c.upper() if random.random() < 0.4 else c for c in w)


def noun_arg():
    r = random.random()
    if r < 0.55:
        return rand_case(random.choice(NOUNS))
    if r < 0.75:
        return random.choice(PREFIXES) + random.choice(NOUNS).capitalize()
    if r < 0.88:
        return "_".join(rand_case(random.choice(WORDS + NOUNS)) for _ in range(random.randint(2, 3)))
    return " ".join(random.choice(WORDS + NOUNS) for _ in range(random.randint(2, 3)))


def ident_arg():
    r = random.random()
    parts = [rand_case(random.choice(WORDS)) for _ in range(random.randint(1, 4))]
    if r < 0.30:
        return "_".join(parts)
    if r < 0.55:
        return random.choice(CAMEL) + random.choice(["", "", random.choice(CAMEL)])
    if r < 0.65:
        return "".join(p.capitalize() for p in parts)
    if r < 0.75:
        return "-".join(parts)
    if r < 0.85:
        joined = random.choice(["_", "__", "-", " ", "_-", "--"]).join(parts)
        return random.choice(["", "_", "__", "-"]) + joined + random.choice(["", "_", "-", "_id"])
    return "".join(random.choice(parts + PUNCT + list("0123456789_ ")) for _ in range(random.randint(1, 12)))


def phrase_arg():
    words = [rand_case(random.choice(WORDS)) for _ in range(random.randint(1, 6))]
    out = []
    for w in words:
        if random.random() < 0.12:
            w = w + random.choice(["'s", "'t", "'re", "'", "!", "?", ":", ",", "."])
        if random.random() < 0.07:
            w = random.choice(["'", "(", "\"", "#", "1st", "2nd", "42", "x-"]) + w
        out.append(w)
    sep = random.choice([" "] * 6 + ["_", "-", "  ", " - ", ": "])
    s = sep.join(out)
    if random.random() < 0.15:
        s = s + random.choice(["_id", "_ID", "_ids", "_id_"])
    if random.random() < 0.08:
        s = random.choice([" ", "_", "-", "'"]) + s
    return s


def number_arg():
    r = random.random()
    if r < 0.45:
        n = str(random.randint(0, 130))
    elif r < 0.65:
        n = str(random.choice([11, 12, 13, 111, 112, 113, 1011, 1012, 1013, 21, 22, 23, 101, 102, 103]))
    elif r < 0.80:
        n = str(random.randint(0, 10**random.randint(3, 9)))
    elif r < 0.90:
        n = str(random.randint(10**19, 10**30))
    else:
        n = "0" * random.randint(1, 3) + str(random.randint(0, 999))
    return ("-" if random.random() < 0.2 else "") + n


ARGS = {
    "camelize": ident_arg,
    "camelize_lower": ident_arg,
    "dasherize": ident_arg,
    "humanize": phrase_arg,
    "ordinalize": number_arg,
    "parameterize": phrase_arg,
    "parameterize_underscore": phrase_arg,
    "pluralize": noun_arg,
    "singularize": noun_arg,
    "tableize": lambda: random.choice([noun_arg, ident_arg])(),
    "titleize": lambda: random.choice([phrase_arg, ident_arg])(),
    "underscore": ident_arg,
}
WEIGHTS = {
    "camelize": 7, "camelize_lower": 6, "dasherize": 3, "humanize": 7, "ordinalize": 8,
    "parameterize": 7, "parameterize_underscore": 5, "pluralize": 16, "singularize": 16,
    "tableize": 8, "titleize": 10, "underscore": 7,
}

# Whole lines that exercise a specific rule or a known trap.
FIXED = [
    ("pluralize", "octopus"), ("pluralize", "CamelOctopus"), ("pluralize", "sheep"),
    ("pluralize", "black sheep"), ("pluralize", "woman"), ("pluralize", "human"),
    ("pluralize", "Roman"), ("pluralize", "cow"), ("pluralize", "Cow"), ("pluralize", "COW"),
    ("pluralize", "kine"), ("pluralize", "passerby"), ("pluralize", ""), ("pluralize", "quiz"),
    ("singularize", "octopi"), ("singularize", "goldfish"), ("singularize", "gold fish"),
    ("singularize", "SalesPeople"), ("singularize", "Kine"), ("singularize", "KINE"),
    ("singularize", "oxen"), ("singularize", "oxenfree"), ("singularize", "news"),
    ("singularize", "series"), ("singularize", "theses"), ("singularize", ""),
    ("camelize", "a__b"), ("camelize", "_leading"), ("camelize", "trailing_"), ("camelize", ""),
    ("camelize_lower", "_a"), ("camelize_lower", "Device_type"), ("camelize_lower", "x"),
    ("underscore", "IOError"), ("underscore", "HTTPServer"), ("underscore", "getHTTPResponseCode"),
    ("underscore", "ABCDefGHI"), ("underscore", "A1B2"),
    ("titleize", "they're here"), ("titleize", "1st place"), ("titleize", "x-men: the last stand"),
    ("titleize", "TheManWithoutAPast"), ("titleize", "author_id"), ("titleize", "'quoted' word"),
    ("humanize", "author_id"), ("humanize", "_id"), ("humanize", "employee_ID"), ("humanize", ""),
    ("parameterize", "Donald E. Knuth"), ("parameterize", "---"), ("parameterize", "a--b__c"),
    ("parameterize_underscore", "a-b c"), ("parameterize_underscore", "__x__"),
    ("ordinalize", "11"), ("ordinalize", "-1021"), ("ordinalize", "0"), ("ordinalize", "-0"),
    ("ordinalize", "007"), ("ordinalize", "112"), ("ordinalize", "123456789012345678901"),
    ("tableize", "RawScaledScorer"), ("tableize", "egg_and_ham"), ("tableize", "fancyCategory"),
    ("dasherize", "puni_puni"), ("dasherize", "__"),
]


def ok(name, arg):
    if any(c < " " or c > "~" for c in arg):
        return False
    return not (name == "camelize_lower" and arg == "")


def main():
    functions = load_original()
    random.seed(1)

    names = list(WEIGHTS)
    weights = [WEIGHTS[n] for n in names]
    lines = [f"{n}\t{a}" for n, a in FIXED]
    seen = set(lines)
    while len(lines) < 2 * N:
        name = random.choices(names, weights=weights)[0]
        arg = ARGS[name]()
        line = f"{name}\t{arg}"
        if line in seen or not ok(name, arg):
            continue
        seen.add(line)
        lines.append(line)
    random.shuffle(lines)

    DATA.mkdir(exist_ok=True)
    for prefix, chunk in (("", lines[:N]), ("hidden_", lines[N:])):
        answers = []
        for line in chunk:
            name, arg = line.split("\t", 1)
            answer = functions[name](arg)
            assert "\n" not in answer and "\r" not in answer
            answers.append(answer)
        for filename, rows in ((f"{prefix}inputs.txt", chunk), (f"{prefix}expected.txt", answers)):
            with open(DATA / filename, "w", encoding="utf-8", newline="\n") as f:
                f.write("".join(row + "\n" for row in rows))
        print(f"wrote {len(chunk)} lines to tests/data/{prefix}inputs.txt and {prefix}expected.txt")


if __name__ == "__main__":
    main()
