#!/usr/bin/env python3
"""Generate the frozen inputs and answers for this task.

Run from anywhere with CPython 3.12:  python tests/gen.py

Answers come only from running the original python-titlecase, which must be
checked out next to the task folder as ../python-titlecase. Never edit the
files in tests/data by hand.
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent.parent / "python-titlecase"
DATA = HERE / "data"
COUNT = 2000

# The reference is the stdlib `re` branch, so answers must not depend on
# whether `regex` happens to be installed on this machine.
sys.modules["regex"] = None
sys.path.insert(0, str(ORIGINAL))
from titlecase import REGEX_AVAILABLE, titlecase  # noqa: E402

assert not REGEX_AVAILABLE
assert sys.version_info[:2] == (3, 12), "answers are frozen with CPython 3.12"

NORMAL = """lord rings river mountain story house night city garden dream winter
summer ocean forest history science music engine python language computer
window letter market bridge journey shadow silver golden ancient modern simple
quick brown jumping lazy bright broken hidden little great final second people
world water planet machine theory thanks because during without about under
over into from with nothing everything always never sometimes""".split()

SMALL = """a an and as at but by en for if in of on or the to v v. via vs vs.
A An AND As AT But BY En FOR If IN Of ON Or THE To V V. Via VS Vs.""".split()

CONSONANT = """xml http css php rss sql html st mr ny nth bcd tv dvd pdf gym my
fly sky MP3 mp3 XML Xml hTML""".split()

MIXED = """iPhone eBay macOS GitHub YouTube iOS LaTeX JavaScript PowerPoint aB Ab
ABc abC McGregor deVito FBI NASA NaSA mIxEd""".split()

DOTTED = """example.com node.js v1.2.3 a.b U.S. U.S.A. p.m. e.g. i.e. Ph.D.
www.foo.org A.B. A.B A.B.C A. a. Z.Z.Z. x.y.z foo.bar. .hidden end. one..two
3.14 café.com éa.éb v.x vs.x""".split()

APOS = """d'angelo o'reilly l'oreal o'reilly's d'artagnan l‘amour O'REILLY
D'ANGELO L'ORE o's d's l'ss d'x o'neil's d'ab'' l'oreal's o'' d' D'a o‘brien
it's don't dog's d'été l'école o'ßa d'ıx O'Neil's""".split()

MAC = """mcdonald McDonald MCDONALD mcgregor macdonald mc mcx mc. mc-donald MCX
Mc mC mcdonald-smith mcdonald/smith mcdonald. mcdonald's mcAdam mcé mc1a
MCdonald mc_a mc.a mCdonald mCgregor""".split()

HONORIFIC = """mr mrs ms dr Mr. mr. mrs. MR MRS DR mRs Dr dR Ms MS mſ mrſ""".split()

SLASHED = """this/that and/or a/b foo/the/bar http://foo.com/bar //x a//b /leading
trailing/ THIS/that in/out 1/2 AND/OR the/a xml/css mc/donald o'neil/smith
on/off/on a/ /a x/y/z""".split()

HYPHENED = """step-by-step well-to-do -leading trailing- x-ray NON-STOP e-mail
mother-in-law a-b-c co--op the-end in-the-know pre-XML xml-rpc a- -a of-the
T-SHIRT t-shirt mid-iPhone é-mail""".split()

WRAPPED = """"hello" (world) [foo] “quoted” ‘single’ ¿que?
«guillemet» ...wow —dash _under_ *star* #tag @user $100 100% ~tilde
a: of: the, to! (the) "a" 'an' [of] “the” (a) ...and --or "v." (vs.) &
&and 'tis 'twas ?why !wow {x} |y| \\z ^up +plus =eq <lt> …dots
”closing ’tis ’hello” ”the ’a""".split()

UNICODE = """café naïve über ÉCOLE straße STRASSE ßeta
ﬁsh ﬂow ﬀ ŉa ǆabc ǄABC ǅab ΟΔΟΣ ΣΑΣ
σίσυφος Σ ΑΣ. İstanbul ıf aſ ſt K Kelvin
ᾈx ᾳy école ÉCOLE １２ ٣ २० 东京 \U0001f600 æon œuvre
Ångström Ångstrom дом ДОМ աբ ևx ẞ µm μm
º ª ² Ⅷ ⅷx ① Ⓐ ⓐbc Ა ა ⱥ \U00010428x
cafÉ Α'Σ Α:Σ ΑΣ'Α ΑΣ:Α Α’Σ""".split() + [
    "a\N{COMBINING ACUTE ACCENT}", "o\N{COMBINING ACUTE ACCENT}f",
    "the\N{COMBINING ACUTE ACCENT}", "to\N{COMBINING DIAERESIS}",
    "d'e\N{COMBINING ACUTE ACCENT}te", "\N{COMBINING ACUTE ACCENT}x",
]

# Characters whose upper case is several letters: a line can look upper case
# to a simple per-character check while Python says it is not.
UPPER_GAPS = "GROß STRAßE ﬁNAL ŉ ǰ ß".split()

NUMERIC = "1984 2nd 3d 1st 100 007 1a a1 12:30 10-20 3/4".split()

SEPARATORS = [": ", ". ", "; ", "? ", "! ", " - ", " – ", " ‒ ", " — ",
              " ― ", ", ", " / ", ":", " : ", "- ", "— ", ".. "]

SPACES = ["  ", "   ", "\t", " ", " ", "　", "\x0b", "\x0c", "\x1c",
          "\x1d", "\x1e", "\x1f", "\x85", " ", " ", " ", " ",
          " ", " \t "]

TRICKY = [CONSONANT, MIXED, DOTTED, APOS, MAC, HONORIFIC, SLASHED, HYPHENED,
          WRAPPED, UNICODE, NUMERIC]


def word(rng, tricky_share):
    if rng.random() < tricky_share:
        return rng.choice(rng.choice(TRICKY))
    return rng.choice(SMALL if rng.random() < 0.4 else NORMAL)


def plain_title(rng, tricky_share):
    return " ".join(word(rng, tricky_share) for _ in range(rng.randint(1, 8)))


def make_title(rng):
    kind = rng.random()
    if kind < 0.25:          # mostly ordinary words
        title = plain_title(rng, 0.1)
    elif kind < 0.60:        # heavy on the rule-specific words
        title = plain_title(rng, 0.6)
    elif kind < 0.75:        # sub-phrases
        title = rng.choice(SEPARATORS).join(
            plain_title(rng, 0.3) for _ in range(rng.randint(2, 3)))
    elif kind < 0.85:        # unusual whitespace
        parts = [word(rng, 0.4) for _ in range(rng.randint(2, 6))]
        title = parts[0]
        for part in parts[1:]:
            title += rng.choice(SPACES + [" "]) + part
    elif kind < 0.93:        # one word, so first and last rules meet
        title = word(rng, 0.8)
    else:                    # small word at the end, with or without punctuation
        title = (plain_title(rng, 0.2) + " " + rng.choice(SMALL)
                 + rng.choice(["", "", ".", "?", "!", ",", ":", "..", "—", ")", "”"]))

    style = rng.random()
    if style < 0.18:
        title = title.upper()
        if rng.random() < 0.25:
            title += " " + rng.choice(UPPER_GAPS)
    elif style < 0.33:
        title = title.lower()
    elif style < 0.43:
        title = title.title()

    edge = rng.random()
    if edge < 0.05:
        title += rng.choice([" ", "  ", "\t", " "])
    elif edge < 0.10:
        title = rng.choice([" ", "  ", "\t", "　"]) + title
    return title


def unique_titles(rng, seen, count):
    titles = []
    while len(titles) < count:
        title = make_title(rng)
        if title in seen or "\r" in title or "\n" in title:
            continue
        seen.add(title)
        titles.append(title)
    return titles


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def freeze(titles, input_name, expected_name):
    answers = [titlecase(title) for title in titles]
    for title, answer in zip(titles, answers):
        assert "\n" not in answer and "\r" not in answer, repr(title)
    write_lines(DATA / input_name, titles)
    write_lines(DATA / expected_name, answers)


def main():
    random.seed(1)
    DATA.mkdir(exist_ok=True)
    seen = {""}  # the empty title is added once, by hand, to the hidden set
    visible = unique_titles(random, seen, COUNT)
    hidden = unique_titles(random, seen, COUNT - 1) + [""]
    random.shuffle(hidden)
    freeze(visible, "inputs.txt", "expected.txt")
    freeze(hidden, "hidden_inputs.txt", "hidden_expected.txt")


if __name__ == "__main__":
    main()
