#!/usr/bin/env python3
"""Generate the visible and hidden test sets and freeze the expected answers.

Run:  python tests/gen.py            (needs `regex` installed, same Python as NOTES.md)
Env:  TITLECASE_REPO=/path/to/python-titlecase   (default: ../python-titlecase)

Rules of the game
- fully deterministic (random.seed(1))
- expected answers come ONLY from running the ORIGINAL titlecase(); never typed by hand
- inputs obey the contract in instruction.md: one line, UTF-8, no CR/LF,
  whitespace = space or tab only, no characters whose case mapping changes length
- visible and hidden sets are disjoint
"""
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
N = 2000

PLAIN = """about above across action after again against age air all also always amazing american ancient another answer
apple art autumn baby back bad bag ball bank battle beach bear beautiful beauty bed before beginning behind best better beyond
big bird birth black blood blue boat body book border born boy bread breaking bridge bright brother brown build burning
business cabin call car castle cat cave center century chance change child children city clean clear clock cloud cold color
come company complete country court crazy cross crown cruel dance dark daughter day dead death deep desert desire devil
different dinner doctor door dream drive dry early earth east easy edge eight empire end enemy engine evening ever every
eye face fall family fast father fear fight fire first fish flight flower follow food fool forest forever friend front full
future game garden ghost gift girl glass gold good grand great green ground guide hand happy hard heart heaven heavy
hidden high hill history home honest hope horse hotel hour house human hundred hunter ice iron island journey judge jungle
keeper key killer king kiss kitchen knight lady lake land last late law legend letter life light line lion little long lost
love lucky machine magic man map market master memory middle midnight mind mirror moon morning mother mountain music mystery
name nation never new night noble north nothing ocean old only open other outside paper party past peace people perfect piano
place planet play poison power pretty prince prison proud queen quick quiet rain red return rich river road rock room rose
round royal rule run sacred safe salt school sea secret seven shadow ship short silent silver sister sky sleep slow small
snow soldier song soul south spirit spring star stone storm story strange street strong summer sun sweet sword tale tears
tenth thin thing third thousand thunder tiger time tiny tower town tree true trust truth twelve under universe valley
village voice wall war water way west white wide wild wind window winter wish witch wolf woman wonder world young zero""".split()

SMALL = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
# words that START with a small word (SUBPHRASE has no word boundary)
SMALL_PREFIXED = """about above across after again against along also among another any around aside asleep atlas atom
attic button butter byte bypass entry engine envy force foreign forest formal forty ifconfig inner inside into
island office often onto only onward orbit order other ought theater their theme theory these thick tokyo today
together tomorrow tonight total touch toward vision visit via-ferrata vsync""".split()
ACRONYMS = "NASA FBI NATO UNESCO USA UK EU IBM BBC CNN DNA RNA AI OK TV PC CD DVD".split()
BRANDS = "iPhone eBay YouTube iTunes PayPal GitHub JavaScript PhD McKinsey LinkedIn DeVry macOS iOS WiFi".split()
CONSONANT_ACRONYMS = "html css http php xml sql cpt cdn ltd pdf rpm tv st dr hmm brr shh psst nth gym myth lynx".split()
APOS_NAMES = ["o'neil", "d'artagnan", "l'amour", "O'Brien", "D'Arcy", "d'arcy's", "o'neil's", "l'ss", "d'a", "o'er",
              "l‘ami", "d‘or", "d'ss", "O'REILLY", "o'brien's", "don't", "rock'n'roll", "'tis", "l'oreal", "d'angelo"]
MC_NAMES = ["mcdonald", "MCDONALD", "McDonald", "mcgregor", "McKay", "mckinley", "mcand", "mcx", "mcv", "mcof", "Mcthe",
            "macdonald", "MacArthur", "mcd", "mc", "MCI", "mcmillan", "mcivor"]
TITLES = ["mr", "Mr", "MR", "mrs", "Mrs", "ms", "MS", "dr", "Dr", "DR", "dR", "mS"]
INITIALS = ["J.R.R.", "U.S.A.", "J.R", "A.B.C", "J.", "j.r.r.", "e.g.", "i.e.", "T.S.", "H.P.", "A.B", "a.b."]
URLS = ["www.example.com", "http://foo/bar", "x.org/path", "a//b", "foo.bar", "node.js", "e.mail", "3.14", "v1.2", "a.b.c",
        "file.txt", "my_file.py", "example.com/a-b", "ftp://x.y/z"]
HYPHEN = ["state-of-the-art", "well-known", "x-ray", "e-mail", "Spider-Man", "twenty-one", "up-to-date", "ex-wife",
          "end-of", "foo-of", "of-the", "a-b", "-a", "a-", "--", "mid-century", "A-List", "re-enter", "to-do", "by-and-by"]
SLASH = ["and/or", "either/or", "w/o", "24/7", "a/b/c", "he/she", "of/the", "A/B", "on/off", "I/O", "TCP/IP", "yes/no", "/", "//",
         "/a", "a/", "r/of"]
WRAPPED = ["(the)", "\"quoted\"", "“curly”", "‘single’", "'x'", "[a]", "{of}", "...and", "the...", "--the", "(a)", "(of,",
           "to.", "in:", "by;", "at!", "as?", "(in)", "[the]", "“a", "of”", "'of'", "(v.)", "(vs)", "_the_", "*of*"]
UNICODE = ["café", "naïve", "über", "élan", "señor", "ÉCOLE", "ÀB", "çà", "crème", "brûlée", "jalapeño", "Zoë", "façade",
           "doppelgänger", "smörgåsbord", "éclair", "ÑANDÚ", "über-cool", "café/bar", "o'Ñandú"]
DIGITS = ["3d", "2nd", "42", "1.5", "$5", "100%", "1984", "9/11", "#1", "50-50", "24-7", "7th", "R2-D2", "C3PO", "4k"]
SMALL_ACCENT = ["inï", "ofé", "ané", "toñ", "bye", "byé", "asü", "atö", "orç", "ifé", "ená", "theé", "foré", "viaé", "andé"]
ACCENT_SMALL = ["éof", "ñin", "caféor", "naïve-of", "über-the", "señor-to", "élan-in", "çà-by", "éa", "ñan", "üand"]
PUNCT_ONLY = [":", "!", "?", "-", "—", "–", "...", "&", "+", "@", "#", "—-", "?!", "&c"]
SUB_PUNCT = [":", ".", ";", "?", "!", "-", "–", "—", "‒", "―"]
OPENERS = ["(", "[", "{", "“", "‘", '"', "'"]
CLOSERS = [")", "]", "}", "”", "’", '"', "'", ".", ",", ":", ";", "!", "?"]


def pick(seq):
    return random.choice(seq)


def plain(n):
    out = []
    for _ in range(n):
        out.append(pick(SMALL) if random.random() < 0.3 else pick(PLAIN))
    return out


def tricky():
    pools = [ACRONYMS, BRANDS, CONSONANT_ACRONYMS, APOS_NAMES, MC_NAMES, TITLES, INITIALS, URLS, HYPHEN, SLASH,
             WRAPPED, UNICODE, DIGITS, PUNCT_ONLY, SMALL_PREFIXED]
    return pick(pick(pools))


def mutate_case(w):
    r = random.random()
    if r < 0.10:
        return w.upper()
    if r < 0.14:
        return w.lower()
    if r < 0.17:
        return w.capitalize()
    return w


def edge_line():
    W, S = lambda: pick(PLAIN), lambda: pick(SMALL)
    t = random.randrange(30)
    if t == 0:
        return f"{W()} v. {S()} {W()}"
    if t == 1:
        return f"{W()}. v. {S()} {W()}"
    if t == 2:
        return f"{W()} vs. {W()} {S()} {W()}"
    if t == 3:
        return f"{W()}{pick(SUB_PUNCT)} {pick(SMALL_PREFIXED)} {W()}"
    if t == 4:
        return f"{W()}{pick(SUB_PUNCT)} {S()} {W()}{pick(SUB_PUNCT)} {S()} {W()}"
    if t == 5:
        return f"{W()}-{S()}"
    if t == 6:
        return f"{W()}-{S()}-{W()} {W()}"
    if t == 7:
        return f"{W()} {W()}-{S()}"
    if t == 8:
        return f"{S()}/{S()} {W()}"
    if t == 9:
        return f"{W()} {W()}/{S()}"
    if t == 10:
        return f"{pick(MC_NAMES)} {S()} {pick(MC_NAMES)}"
    if t == 11:
        return " ".join(w.upper() for w in [pick(INITIALS), W(), S(), pick(APOS_NAMES), W()])
    if t == 12:
        return " ".join(w.upper() for w in plain(3) + [pick(INITIALS)] + plain(2))
    if t == 13:
        return f"{pick(OPENERS)}{S()}{pick(CLOSERS)} {W()} {S()} {pick(OPENERS)}{S()}{pick(CLOSERS)}"
    if t == 14:
        return f"{S()} {W()} {S()}{pick('.,:;!?')}"
    if t == 15:
        return f"{pick(TITLES)} {W()} {S()} {pick(TITLES)} {W()}"
    if t == 16:
        return f"{pick(MC_NAMES)}"
    if t == 17:
        return f"{W()} {pick(SMALL)}{pick('.,:;!?)')}"
    if t == 18:
        return " ".join(plain(2) + [pick(URLS)] + plain(2))
    if t == 19:
        return f"{pick(APOS_NAMES)} {S()} {pick(APOS_NAMES)}"
    if t == 20:
        return f"{pick(ACRONYMS)} {S()} {pick(CONSONANT_ACRONYMS)} {W()}"
    if t == 21:
        return f"{pick(SUB_PUNCT)} {S()} {W()}"
    if t == 22:
        return f"{W()}  {S()}\t{W()}"
    if t == 23:
        return f"{pick(HYPHEN)} {S()} {pick(SLASH)}"
    if t == 24:
        return f"{pick(UNICODE)} {S()} {pick(UNICODE)}"
    if t == 25:
        return f"{pick(DIGITS)} {S()} {W()} {pick(DIGITS)}"
    if t == 26:  # small word glued to an accented letter: \b must be Unicode-aware
        return f"{pick(SMALL_ACCENT)} {W()} {S()}"
    if t == 27:
        return f"{W()} {W()} {pick(ACCENT_SMALL)}"
    if t == 28:  # small word at the very end, with trailing punctuation
        return f"{W()} {W()} {S()}{pick(CLOSERS)}"
    return f"{S()}{pick(CLOSERS)}"


def headline():
    n = random.choice([1, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9, 10, 12])
    words = plain(n)
    # sprinkle 0-3 tricky tokens
    for _ in range(random.choice([0, 0, 1, 1, 2, 3])):
        words.insert(random.randrange(len(words) + 1), tricky())
    words = [mutate_case(w) for w in words]
    seps = []
    for _ in range(len(words) - 1):
        r = random.random()
        seps.append(" " if r < 0.93 else ("  " if r < 0.96 else ("\t" if r < 0.98 else " \t ")))
    s = "".join(w + (seps[i] if i < len(seps) else "") for i, w in enumerate(words))
    r = random.random()
    if r < 0.07:
        s = s.upper()
    elif r < 0.10:
        s = s.lower()
    elif r < 0.12:
        s = " " + s
    elif r < 0.14:
        s = s + " "
    elif r < 0.16:
        s = pick(["(", "\"", "“", "'", "‘", "[", "- ", "... "]) + s
    elif r < 0.19:
        s = s + pick([".", ",", "!", "?", ")", ":", "”", "...", ";"])
    return s


def make_line():
    r = random.random()
    if r < 0.25:
        return edge_line()
    if r < 0.30:
        return " ".join(w.upper() for w in plain(random.randint(2, 7)))
    return headline()


def ok(s):
    return bool(s.strip()) and "\n" not in s and "\r" not in s


def main():
    random.seed(1)
    repo = Path(os.environ.get("TITLECASE_REPO", HERE.parent.parent / "python-titlecase"))
    sys.path.insert(0, str(repo))
    import titlecase as tcmod  # the ORIGINAL implementation
    assert tcmod.REGEX_AVAILABLE, "install the `regex` module: ground truth is the regex-flavoured behaviour"
    titlecase = tcmod.titlecase

    seen, lines = set(), []
    while len(lines) < 2 * N:
        s = make_line()
        if not ok(s) or s in seen:
            continue
        seen.add(s)
        lines.append(s)
    visible, hidden = lines[:N], lines[N:]

    DATA.mkdir(exist_ok=True)
    for name, ins in (("", visible), ("hidden_", hidden)):
        outs = [titlecase(s) for s in ins]
        assert all("\n" not in o and "\r" not in o for o in outs)
        (DATA / f"{name}inputs.txt").write_text("\n".join(ins) + "\n", encoding="utf-8", newline="\n")
        (DATA / f"{name}expected.txt").write_text("\n".join(outs) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(visible)} visible and {len(hidden)} hidden cases to {DATA}")


if __name__ == "__main__":
    main()
