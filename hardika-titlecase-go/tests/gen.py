import argparse
import hashlib
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reference import ROOT, record_bytes, titlecase

GENRES = (
    "bibliography", "exhibition", "catalogue", "songbook", "program", "recital",
    "collected correspondence", "folio notes", "manuscript inventory", "wall labels",
    "selections", "field recordings", "travel diaries", "reading list", "index",
    "chamber works", "curator's notes", "annotated facsimiles", "press proofs",
)
SUBJECTS = (
    "the glass harmonica", "woodcut portraits", "unfinished minuets", "coastal maps",
    "hand-dyed linen", "pattern books", "the mariner's almanac", "early photography",
    "embroidered panels", "harpsichord suites", "vernacular lettering", "artists' proofs",
    "folding screens", "painted ceilings", "cabinet miniatures", "maritime ballads",
    "metal type", "private libraries", "counterpoint", "stained glass", "studio pottery",
)
NAMES = (
    "dr mccracken", "mrs d‘arcy", "d'oisy", "ms mclaren-von arnim", "O'KEEFFE",
    "o'brien's", "l'alouette", "J.A. mcbride", "mR de la cruz", "mr l'estrange",
    "d'ßelle", "mc-toledo", "mcand", "mcof-via/at", "mcdonald and mckee",
    "Ν.Κ. καβάφης", "mc𐐨va", "ǳordana", "DeVries", "mCiNTOSH", "d‘oštić",
    "o'ǆikić", "Mcand/or", "l'ﬃore", "łucja kowalska", "İpek", "ıpek",
)
PLACES = (
    "brno", "tallinn", "córdoba", "the hague", "aix-en-provence", "kyōto", "oslo",
    "trieste", "vilnius", "palermo", "porto", "tromsø", "istanbul", "tbilisi",
    "thessaloníki", "l’viv", "new orleans", "santa fe", "angers", "lübeck",
    "’s-hertogenbosch", "škofja loka", "český krumlov", "são paulo",
)
SMALL = ("a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of",
         "on", "or", "the", "to", "v.", "via", "vs.", "ın", "İn", "aſ")
COMPOUNDS = (
    "in-and/of", "by/of-to", "up-to-date", "in-between", "of-the-sea",
    "en-plein-air", "verso/recto", "in/of-and-to", "folio//proof",
    "mcname-and/or", "work-in-progress", "print-on-demand", "voice-and/for-piano",
    "sea/land-and-sky", "notes///revisions", "at-/of", "to/at--in", "and_in",
    "the\u0301-index", "v./vs./via", "the/--/and", "and‒or",
)
WRITING = (
    "ﬃ ligatures", "ß in letterpress", "ŉederlandse teksten", "ǳ and ǅ in annotations",
    "ΑΘΗΝΑΣ", "ΛΟΓΟΣ·", "ΛΟΓΟΣ\u0301", "Σ\u0345", "ΩΣ’Α", "ΟΔΥΣΣΕΎΣ",
    "αρχεία-λόγος", "𐐨𐐻 inscriptions", "ᲐᲜᲑᲐᲜᲘ", "épreuves", "İşaret", "a\u0301.the",
    "日本語目録", "K vs. kelvin", "İn.of", "ſtencil", "é.à", "𞤢𞤤",
    "\u0301letters", "λέξεις.of", "in\u200d", "and‿folio", "₂.a", "Ⱥ.Β",
)
MARKS = (":", ";", ".", "?", "!", "-", "–", "‒", "—", "―")
GAPS = (" ", " ", " ", "  ", "\t", "\v", "\f", "\u00a0", "\u2002", "\u2003",
        "\u202f", "\u205f", "\u3000", "\u2028", "\u0085", "\u200b", "\x1c")
FRAMES = (("“", '"'), ("[", "]"), ("(", ")"), ("‘", "'"), ("__", "_"),
          ("«", "»"), ("!", "?"), ("", ""), ("\x60", "~"))
TEMPLATES = {
    "bibliographic": (
        "{open}{small}{close} {genre} of {subject} by {name}",
        "{name}{mark} {small} {genre} on {subject}",
        "{genre} for {place}{mark} {small} index of {subject}",
    ),
    "museum": (
        "{open}{small}{close} {subject} {mark} {small} {genre} at {place}",
        "{subject} {compound}{mark} {small} {genre}",
        "{place} {genre} on {writing} and {subject}",
    ),
    "publication": (
        "{compound} {genre} of {subject}{mark} {small} {place}",
        "{genre} of {subject}{mark} {writing} / {compound}",
        "{name} on {compound}{mark} {small} {genre} for {place}",
    ),
    "music": (
        "{name}{mark} {small} {genre} for {subject} at {place}",
        "{open}{small}{close} {subject} with {name} {compound}",
        "{genre} of {writing} and {subject} {mark} for {place}",
    ),
    "historical": (
        "{writing} {mark} {small} {subject} of {place}",
        "{name} in {place} {mark} a {genre} against {writing}",
        "{small} {name} and {writing}{mark} {compound} {last}{close}",
    ),
}
COUNT = 2000


def compose(family):
    opening, closing = random.choice(FRAMES)
    candidate = random.choice(TEMPLATES[family]).format(
        genre=random.choice(GENRES), subject=random.choice(SUBJECTS),
        name=random.choice(NAMES), place=random.choice(PLACES),
        small=random.choice(SMALL), last=random.choice(SMALL),
        compound=random.choice(COMPOUNDS), writing=random.choice(WRITING),
        mark=random.choice(MARKS), open=opening, close=closing,
    )
    casing = random.randrange(8)
    if casing < 2:
        candidate = candidate.upper()
    elif casing == 2:
        candidate = candidate.lower()
    elif casing == 3:
        first, _, tail = candidate.partition(" ")
        candidate = first.upper() + " " + tail

    if random.randrange(3) == 0:
        words = candidate.split(" ")
        gap = random.choice(GAPS)
        index = random.randrange(len(words) - 1)
        candidate = " ".join(words[:index + 1]) + gap + " ".join(words[index + 1:])
    if random.randrange(13) == 0:
        candidate = random.choice(GAPS[:13]) + candidate
    if random.randrange(13) == 0:
        candidate += random.choice(GAPS[:13])
    return candidate


def generate(destination):
    random.seed(1)
    destination.mkdir(parents=True, exist_ok=True)
    families = tuple(TEMPLATES)
    seen_inputs, seen_outputs = set(), set()
    for prefix in ("", "hidden_"):
        inputs, outputs = [], []
        coverage = Counter()
        while len(inputs) < COUNT:
            family = families[len(inputs) % len(families)]
            item = compose(family)
            expected = titlecase(item)
            if item in seen_inputs or expected in seen_outputs:
                continue
            if any(ch in item or ch in expected for ch in "\r\n"):
                raise ValueError("A record contains a line terminator")
            seen_inputs.add(item)
            seen_outputs.add(expected)
            inputs.append(item)
            outputs.append(expected)
            coverage[family] += 1

        for file, records in (("inputs.txt", inputs), ("expected.txt", outputs)):
            data = record_bytes(records)
            (destination / (prefix + file)).write_bytes(data)
            print(f"{prefix + file} count={len(records)} sha256={hashlib.sha256(data).hexdigest()}")
        print(f"{prefix or 'visible'} families={dict(coverage)}")
    print(f"distinct inputs={len(seen_inputs)} distinct outputs={len(seen_outputs)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "tests/data")
    generate(parser.parse_args().output)
