#!/usr/bin/env python3
"""
Test title generator for Harbor task titlecase-go.
Generates reproducible test datasets and runs the original Python titlecase()
implementation to produce expected outputs.
"""

import os
import random
import sys

# 1. Reproducibility
random.seed(1)

# 2. Locate and import the original Python titlecase implementation
repo_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "environment", "python-titlecase")
)
if not os.path.exists(os.path.join(repo_dir, "titlecase")):
    # Fallback to parent directory layout if applicable
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

try:
    from titlecase import titlecase
except ImportError as err:
    sys.stderr.write(f"Error importing titlecase from '{repo_dir}': {err}\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Vocabulary and Pattern Pools (Based on NOTES.md and original package tests)
# ---------------------------------------------------------------------------

SMALL_WORDS = [
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."
]

HONORIFICS = [
    "mr", "mrs", "ms", "dr", "Mr", "Mrs", "Ms", "Dr",
    "MR", "MRS", "MS", "DR", "mr.", "mrs.", "ms.", "dr.",
    "Mr.", "Mrs.", "Ms.", "Dr.", "MR.", "MRS.", "MS.", "DR."
]

APOS_CONSONANTS = [
    "d'angelo", "d'Angelo", "d'artagnan", "d'Artagnan", "d'alembert", "d'Alembert",
    "l'grange", "l'Grange", "l'enfant", "l'Enfant", "l'enfant's", "d'orazio",
    "d‘angelo", "l‘grange", "d‘Artagnan", "l‘Enfant's", "d‘alembert",
    "D'ANGELO", "L'GRANGE", "D'ALEMBERT", "L'ENFANT", "L'ENFANT'S"
]

APOS_VOWELS = [
    "o'connor", "o'reilly", "o'grange", "o'neill", "o'grange's", "o'brien",
    "o‘connor", "o‘reilly", "o‘neill", "o‘brien", "o‘grange's",
    "O'CONNOR", "O'REILLY", "O'NEILL", "O'BRIEN", "O'GRANGE'S", "O'HARE"
]

MC_WORDS = [
    "mcdonald", "mcdonalds", "mctavish", "mcclelland", "mckay", "mcfoo-bar",
    "mcoblon", "mcmaier", "mcneustadt", "mccloud", "mccarthy", "mcguire",
    "mccay-mcbut-mcdo", "mcdonalds/mcby", "mcfoo-mcbar", "foo-mcbar",
    "MCDONALD", "MCTAVISH", "MCCLELLAND", "MCKAY", "MCFOO-BAR", "MCCARTHY",
    "McTavish", "McDonalds", "MacDonald", "macdonald", "mc", "MC", "mac", "MAC"
]

CONSONANT_ACRONYMS = [
    "cnn", "fbi", "html", "xml", "bbc", "tldr", "tcp", "udp", "cctv", "svg",
    "rgb", "nth", "sync", "crypt", "lynx", "st", "tv", "ps", "dr", "CNN", "FBI"
]

DOMAINS_AND_DOTS = [
    "example.com", "del.icio.us", "node.js", "amazon.co.uk", "vue.js",
    "python.org", "google.com", "golang.org", "github.io", "test.dev",
    "A.", "A.B", "A.B.", "D.C.", "U.S.A.", "N.Y.", "E.T.", "U.K."
]

INTERNAL_UC_WORDS = [
    "iTunes", "eBay", "iPhone", "iPad", "microSoft", "PlayStation", "JavaScript",
    "GitHub", "PostgreSQL", "macOS", "OpenAI", "YouTube", "FedEx", "NeXT", "QuickTime"
]

SLASH_COMPOUNDS = [
    "and/or", "input/output", "read/write", "client/server", "tcp/ip",
    "one/two/three", "24/7", "true/false", "win/loss", "yes/no", "on/off",
    "dance with me/let’s face the music and dance",
    "http://example.com", "https://github.com/ppannuto/python-titlecase"
]

HYPHEN_COMPOUNDS = [
    "end-to-end", "peer-to-peer", "state-of-the-art", "follow-up", "real-time",
    "all-in-one", "built-in", "up-to-date", "jack-in-the-box", "mother-in-law",
    "high-level", "low-level", "step-by-step", "part-time", "full-time",
    "two-not-three", "three-by-four", "five-and", "client-side", "server-side"
]

SUBPHRASE_PUNCT = [
    ": ", ". ", "; ", "? ", "! ", " - ", " – ", " ‒ ", " — ", " ― "
]

UNICODE_PHRASES = [
    "el niño a arrivé hier", "EL NIÑO A ARRIVÉ HIER",
    "crème brûlée", "CRÈME BRÛLÉE",
    "café au lait", "CAFÉ AU LAIT",
    "déjà vu", "DÉJÀ VU",
    "façade of reality", "FAÇADE OF REALITY",
    "résumé tips", "RÉSUMÉ TIPS",
    "über den wolken", "ÜBER DEN WOLKEN",
    "ýæ ñø", "ÝÆ ÑØ",
    "the case of x ≤ 7", "THE CASE OF X ≤ 7",
    "α and β testing", "Α AND Β TESTING",
    "π in the sky", "Π IN THE SKY",
    "vis-à-vis an issue", "VIS-À-VIS AN ISSUE",
    "naïve approach", "NAÏVE APPROACH",
    "señor and señorita", "SEÑOR AND SEÑORITA"
]

ORDINALS_AND_NUMBERS = [
    "1st", "2nd", "3rd", "4th", "5th", "21st", "34th", "100th",
    "1984", "2001", "chapter 1", "section 4.2", "v2.0", "episode 7"
]

NOUNS = [
    "time", "year", "people", "way", "day", "man", "thing", "woman", "life",
    "child", "world", "school", "state", "family", "student", "group", "country",
    "problem", "hand", "part", "place", "case", "week", "company", "system",
    "program", "question", "work", "government", "number", "night", "point",
    "home", "water", "room", "mother", "area", "money", "story", "fact",
    "month", "lot", "right", "study", "book", "eye", "job", "word", "business",
    "issue", "side", "kind", "head", "house", "service", "friend", "father",
    "power", "hour", "game", "line", "end", "member", "law", "car", "city",
    "community", "name", "president", "team", "minute", "idea", "kid", "body",
    "information", "back", "parent", "face", "others", "level", "office",
    "door", "health", "person", "art", "war", "history", "party", "result",
    "change", "morning", "reason", "research", "girl", "guy", "moment", "air",
    "teacher", "force", "education", "journey", "shadow", "whisper", "echo",
    "storm", "ocean", "river", "mountain", "forest", "desert", "horizon",
    "galaxy", "universe", "planet", "starlight", "voyage", "silence", "destiny",
    "protocol", "compiler", "runtime", "memory", "thread", "network", "socket"
]

ADJECTIVES = [
    "good", "new", "first", "last", "long", "great", "little", "own", "other",
    "old", "right", "big", "high", "different", "small", "large", "next",
    "early", "young", "important", "few", "public", "bad", "same", "able",
    "brave", "bright", "calm", "dark", "eager", "fierce", "gentle", "happy",
    "ancient", "mysterious", "secret", "hidden", "lost", "forgotten", "golden",
    "silver", "iron", "silent", "endless", "infinite", "wild", "frozen",
    "broken", "sacred", "distant", "curious", "strange", "epic", "legendary",
    "modern", "classic", "digital", "analog", "parallel", "distributed"
]

VERBS = [
    "speaks", "whispers", "cries", "shines", "falls", "rises", "runs", "walks",
    "awakens", "dreams", "fights", "remembers", "returns", "discovers", "escapes",
    "wanders", "journeys", "builds", "destroys", "unfolds", "awaits", "vanishes",
    "conquers", "reveals", "transforms", "embraces", "crosses", "navigates"
]


# ---------------------------------------------------------------------------
# Title Generators for Rules & Tricky Edge Cases
# ---------------------------------------------------------------------------

def gen_normal_title():
    """Generates standard book/article/movie title variations."""
    template = random.choice([
        "{art} {adj} {noun}",
        "{art} {noun} of {noun}",
        "{adj} {noun} and {art} {adj} {noun}",
        "{noun} in the {noun}",
        "{art} {noun} that {verb} the {noun}",
        "{adj} {noun}: {art} {noun} of {noun}",
        "{noun}, {noun}, and {noun}",
        "{verb} through the {adj} {noun}",
        "{noun} for the {adj} {noun}",
        "{art} {noun} with no {noun}"
    ])
    return template.format(
        art=random.choice(["a", "an", "the"]),
        adj=random.choice(ADJECTIVES),
        noun=random.choice(NOUNS),
        verb=random.choice(VERBS)
    )

def gen_small_word_edge_cases():
    """Edge cases for small words at start, end, in quotes, or after subphrases."""
    mode = random.choice(["start", "end", "quotes_start", "quotes_end", "subphrase", "consecutive"])
    small = random.choice(SMALL_WORDS)
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)

    if mode == "start":
        return f"{small} {adj} {noun}"
    elif mode == "end":
        return f"{adj} {noun} to {random.choice(['be', 'have', 'find'])} {small}"
    elif mode == "quotes_start":
        q = random.choice(["'", '"', "‘", "“"])
        q_close = "'" if q == "'" else ('"' if q == '"' else ("’" if q == "‘" else "”"))
        return f"{q}{small} {adj}{q_close} {noun}"
    elif mode == "quotes_end":
        q = random.choice(["'", '"', "‘", "“"])
        q_close = "'" if q == "'" else ('"' if q == '"' else ("’" if q == "‘" else "”"))
        punc = random.choice(["", "?", "!", "."])
        return f"{adj} {noun} {q}{noun} {small}{punc}{q_close}"
    elif mode == "subphrase":
        sub = random.choice(SUBPHRASE_PUNCT)
        return f"{adj} {noun}{sub}{small} {noun} of {noun}"
    else:  # consecutive small words
        s1 = random.choice(["in", "out", "up", "down", "by", "for"])
        s2 = random.choice(["of", "to", "and", "the", "a"])
        return f"{adj} {noun} {s1} and {s2} {noun}"

def gen_name_prefix_cases():
    """Edge cases for d'..., o'..., l'..., Mc..., and bare mc / mac."""
    mode = random.choice(["apos_consonant", "apos_vowel", "mc", "compound_prefix", "allcaps_prefix"])
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)

    if mode == "apos_consonant":
        pfx = random.choice(APOS_CONSONANTS)
        return f"{pfx} and the {adj} {noun}"
    elif mode == "apos_vowel":
        pfx = random.choice(APOS_VOWELS)
        return f"the life of {pfx}: {adj} {noun}"
    elif mode == "mc":
        mc = random.choice(MC_WORDS)
        return f"{mc} visits the {adj} {noun}"
    elif mode == "compound_prefix":
        p1 = random.choice(APOS_VOWELS)
        p2 = random.choice(MC_WORDS)
        return f"{p1}/{p2} in {noun}"
    else:  # all-caps with prefix
        pfx = random.choice(APOS_CONSONANTS + APOS_VOWELS + MC_WORDS).upper()
        return f"{pfx} AND {noun.upper()} OF {adj.upper()}"

def gen_honorific_cases():
    """Edge cases for mr, mrs, ms, dr with varied casing and punctuation."""
    hon = random.choice(HONORIFICS)
    hon2 = random.choice(HONORIFICS)
    noun = random.choice(NOUNS)
    adj = random.choice(ADJECTIVES)
    return random.choice([
        f"{hon} {noun} and {hon2} {noun}",
        f"the story of {hon} {noun}",
        f"{hon} {noun}: {adj} {noun}",
        f"meeting with {hon} {noun.capitalize()}"
    ])

def gen_acronym_cases():
    """Edge cases for consonant acronyms and short words."""
    acr = random.choice(CONSONANT_ACRONYMS)
    acr2 = random.choice(CONSONANT_ACRONYMS)
    noun = random.choice(NOUNS)
    adj = random.choice(ADJECTIVES)
    return random.choice([
        f"words like {acr} are acronyms",
        f"{acr} and {acr2} in the {noun}",
        f"the {adj} guide to {acr}",
        f"why {acr} vs {acr2} matters",
        f"{noun} on {acr} broadcast"
    ])

def gen_compound_cases():
    """Edge cases for slash-separated and hyphen-separated compound words."""
    mode = random.choice(["slash", "hyphen", "mixed", "small_inside"])
    noun = random.choice(NOUNS)
    adj = random.choice(ADJECTIVES)

    if mode == "slash":
        sl = random.choice(SLASH_COMPOUNDS)
        return f"{sl} for the {adj} {noun}"
    elif mode == "hyphen":
        hy = random.choice(HYPHEN_COMPOUNDS)
        return f"{hy} {noun} in {adj} systems"
    elif mode == "mixed":
        sl = random.choice(SLASH_COMPOUNDS)
        hy = random.choice(HYPHEN_COMPOUNDS)
        return f"{hy}/{sl} design patterns"
    else:  # small words inside compounds
        comp = random.choice([
            "state-of-the-art", "up-to-date", "end-to-end",
            "peer-to-peer", "jack-in-the-box", "two-not-three/three-by-four"
        ])
        return f"{comp} {noun}"

def gen_dotted_and_initials_cases():
    """Edge cases for domains, dotted words, and uppercase initials on all-caps lines."""
    mode = random.choice(["domain", "allcaps_initials", "mixed_initials"])
    dom = random.choice(DOMAINS_AND_DOTS)
    noun = random.choice(NOUNS)
    adj = random.choice(ADJECTIVES)

    if mode == "domain":
        return f"this is something listed on {dom}"
    elif mode == "allcaps_initials":
        initials = random.choice(["D.C.", "U.S.A.", "N.Y.", "A.B.", "A."])
        return f"WASHINGTON, {initials} IS NEXT AND {noun.upper()} WILL FOLLOW"
    else:
        initials = random.choice(["J.K.", "G.R.R.", "E.T.", "A.B."])
        return f"{initials} {noun.capitalize()}: {adj.capitalize()} {noun.capitalize()}"

def gen_internal_uc_cases():
    """Edge cases for CamelCase / internal uppercase words."""
    word = random.choice(INTERNAL_UC_WORDS)
    noun = random.choice(NOUNS)
    adj = random.choice(ADJECTIVES)
    return random.choice([
        f"{word} should be unmolested in this title",
        f"developing with {word} and {random.choice(INTERNAL_UC_WORDS)}",
        f"the {adj} future of {word}",
        f"{word}: {adj} {noun} for developers"
    ])

def gen_all_caps_cases():
    """Edge cases for lines that are entirely uppercase."""
    base = random.choice([
        "THIS IS ALL CAPS AND SHOULD BE ADDRESSED",
        "EPISODE 7 — THE FORCE AWAKENS",
        "WAR AND PEACE IN THE MODERN ERA",
        "THE CASE OF X ≤ 7",
        "WASHINGTON, D.C. SHOULD BE FIXED",
        "FOO BAR 5TH ST AND 2ND AVE",
        "CNN AND BBC NEWS BROADCAST",
        "O'REILLY AND MCDONALD REPORT"
    ])
    extra = random.choice(["", f" PART {random.randint(1, 10)}", " — FINAL EDITION"])
    return f"{base}{extra}"

def gen_unicode_cases():
    """Edge cases for Unicode, accented letters, and mathematical symbols."""
    phrase = random.choice(UNICODE_PHRASES)
    adj = random.choice(ADJECTIVES)
    return random.choice([
        phrase,
        f"{phrase}: an overview",
        f"the {adj} study of {phrase}",
        f"{phrase} and other stories"
    ])

def gen_whitespace_cases():
    """Edge cases testing whitespace preservation (tabs, consecutive spaces)."""
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    mode = random.choice(["consecutive_spaces", "tabs", "leading_trailing"])

    if mode == "consecutive_spaces":
        return f"{adj}   {noun}     and   the   {random.choice(NOUNS)}"
    elif mode == "tabs":
        return f"text\twith\ttabs\tand\t{adj}\t{noun}"
    else:
        return f"   {adj} {noun} with whitespace   "

def gen_quotes_and_brackets_cases():
    """Edge cases for titles wrapped in various quotes and brackets."""
    q_pairs = [
        ("'", "'"), ('"', '"'), ("‘", "’"), ("“", "”"),
        ("(", ")"), ("[", "]"), ("{", "}")
    ]
    left, right = random.choice(q_pairs)
    small = random.choice(SMALL_WORDS)
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    return f"{left}{small} {adj} {noun}{right}: the story"


GENERATOR_FUNCS = [
    gen_normal_title,
    gen_small_word_edge_cases,
    gen_name_prefix_cases,
    gen_honorific_cases,
    gen_acronym_cases,
    gen_compound_cases,
    gen_dotted_and_initials_cases,
    gen_internal_uc_cases,
    gen_all_caps_cases,
    gen_unicode_cases,
    gen_whitespace_cases,
    gen_quotes_and_brackets_cases
]


def generate_unique_titles(count, existing_set):
    """
    Generates a specified count of unique titles, ensuring no overlap
    with existing_set.
    """
    titles = []
    seen = set(existing_set)
    attempts = 0
    max_attempts = count * 50

    while len(titles) < count and attempts < max_attempts:
        attempts += 1
        fn = random.choice(GENERATOR_FUNCS)
        candidate = fn()
        # Ensure single-line clean string without newlines
        candidate = candidate.replace("\r", " ").replace("\n", " ")
        if candidate not in seen:
            seen.add(candidate)
            titles.append(candidate)

    if len(titles) < count:
        raise RuntimeError(f"Could only generate {len(titles)} unique titles out of {count} requested.")

    return titles


def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    os.makedirs(data_dir, exist_ok=True)

    inputs_path = os.path.join(data_dir, "inputs.txt")
    expected_path = os.path.join(data_dir, "expected.txt")
    hidden_inputs_path = os.path.join(data_dir, "hidden_inputs.txt")
    hidden_expected_path = os.path.join(data_dir, "hidden_expected.txt")

    print("Generating 2,000 public test titles...")
    inputs = generate_unique_titles(2000, existing_set=set())

    print("Generating 2,000 different hidden test titles...")
    hidden_inputs = generate_unique_titles(2000, existing_set=set(inputs))

    # Assert complete disjointness
    overlap = set(inputs) & set(hidden_inputs)
    assert len(overlap) == 0, f"Overlap detected between public and hidden inputs: {len(overlap)} items"

    print("Running original Python titlecase() to compute expected outputs...")
    expected = [titlecase(title) for title in inputs]
    hidden_expected = [titlecase(title) for title in hidden_inputs]

    # Write public inputs and expected outputs
    print(f"Writing to {inputs_path} and {expected_path}...")
    with open(inputs_path, "w", encoding="utf-8") as f_in:
        f_in.write("\n".join(inputs) + "\n")

    with open(expected_path, "w", encoding="utf-8") as f_exp:
        f_exp.write("\n".join(expected) + "\n")

    # Write hidden inputs and expected outputs
    print(f"Writing to {hidden_inputs_path} and {hidden_expected_path}...")
    with open(hidden_inputs_path, "w", encoding="utf-8") as f_hin:
        f_hin.write("\n".join(hidden_inputs) + "\n")

    with open(hidden_expected_path, "w", encoding="utf-8") as f_hexp:
        f_hexp.write("\n".join(hidden_expected) + "\n")

    print("Verification:")
    print(f"  inputs.txt:        {len(inputs)} lines")
    print(f"  expected.txt:      {len(expected)} lines")
    print(f"  hidden_inputs.txt: {len(hidden_inputs)} lines")
    print(f"  hidden_expected.txt: {len(hidden_expected)} lines")
    print("Done! Generator completed successfully.")


if __name__ == "__main__":
    main()
