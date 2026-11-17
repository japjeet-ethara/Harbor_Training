"""Makes the visible and the hidden case files and freezes the answers of the ORIGINAL pyfiglet.

Run on the laptop (not in Docker), from the task folder:   python tests/gen.py
It needs the original project, with its font setup done, in the folder next to the task folder:
    ../pyfiglet            (commit 255827efbc09d662875dad50fa0edc1e1263bf45)
    mkdir -p ../pyfiglet/pyfiglet/fonts && cp ../pyfiglet/pyfiglet/fonts-standard/* ../pyfiglet/pyfiglet/fonts/

Rules this script keeps:
- Every "out" is what main() of the original wrote to standard output for those arguments. Nobody types one.
- The same run always writes the same two files (fixed seed).
- A case is kept only if the original ends with status 0 and draws something. Cases in which it stops with
  an error, never finishes, or draws nothing are thrown away, so a program that prints nothing earns nothing.
- No case is in both files.
- Files are ASCII JSON lines with "\n" line ends, also on Windows.
"""
import io
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent.parent / "pyfiglet"
DATA = HERE / "data"
N = 2000

# The eight fonts the cases are mostly drawn with.
FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
# Two more standard fonts, used in about one case in seven, because the eight cannot reach these paths:
# "term" prints every character as itself, so it is the only way most of the -F and -r tables decide a case;
# "ivrit" is the only standard font whose header says right-to-left, which is what "-D auto" reads.
EXTRA_FONTS = ["term", "ivrit"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFY = ["auto", "left", "center", "right"]
DIRECTION = ["auto", "left-to-right", "right-to-left"]

WORDS = """hello world figlet banner Harbor golang python twin shout giant letters slash under score Agent Task
Oracle verify reward hidden quick brown fox jumps over lazy dog The and of to in it is a I x Go OK Hi Yo no
2026 42 3.14 v1.0 e-mail snake_case CamelCase UPPER MiXeD zigzag jazz buzz pizza llama illicit minimum
William AVATAR Tokyo kayak level rotor Xerxes Qatar jungle wizard fjord nymph glyph waltz""".split()

# Pieces whose neighbours touch in ways the squeezing rules decide.
TRICKY = ["|_|", "||", "|/", "/|", "/\\", "\\/", "//", "\\\\", "__", "_|_", "[]", "][", "{}", "}{", "()", ")(",
          "<>", "><", "[|]", "(/)", "{_}", "<_>", "_/", "/_", "\\_", "_\\", "|[", "]|", "({[<", ">]})",
          "/\\/\\", "|||", "_-_", "=|=", "#_#", "!|!", "l|l", "T_T", "V/\\", "X><X", "ii", "ll", "i", "l",
          ".", "..", ",", "'", "`", ":", ";", "!", "i.i", "(.)", "[.]", "L_", "_J", "/_/", "\\_\\", "|-|",
          "(_)", "[_]", "<|>", "}|{", ")|(", "]|[", "/(", ")\\", "<(", ")>", "{[", "]}", "_.", "._", "'|'",
          "AV", "VA", "WA", "To", "LT", "fj", "rn", "oo", "@@", "##", "$$", "%&", "*+*", "~^~", "\"\"", "?!"]

# Texts for the font "term": the characters the -F and -r tables change.
TABLES = ["AbMW^v_", "PRb mw", "[{(<>)}]", "V/\\A", "wave^form", "MoM WoW", "bPR", "A_V m^w", "</>", "{[()]}"]

LATIN = ["é", "ß", "ñ", "ü", "Ä", "Ö", "ö", "ä", "Ü", "ç",
         "ø", "Straße", "über", "naïve", "café", "señor", "Ærø",
         "Grüße", "Mädchen", "Öl"]

# Characters most fonts do not have. A few fonts have some of them through code lines in the font file.
UNKNOWN = ["→", "π", "λ", "你好", "\U0001f600", "Ж", "Ω", "ā", "\t",
           "€", "©", "☃", "ć", "ę", "ł", "ş", "ž", "α", "β",
           "Σ", "Д", "я"]

# Two-character texts whose drawing depends on one small part of the smushing rules, each with the font
# it was found for. dev/find_rare_pairs.py finds them with the original code and prints this list.
RARE = [
    # class | against / \ [ ] { } ( ) < >
    ('standard', '!"'), ('standard', 'QE'), ('standard', '~t'), ('standard', 'O}'), ('slant', '!)'), ('slant', 'Ki'),
    ('slant', '~}'), ('slant', 'Vd'), ('small', '!"'), ('small', 'P7'), ('small', '~l'), ('small', 'O2'),
    ('big', '!"'), ('big', 'Qf'), ('big', '~t'), ('big', 'PQ'), ('ivrit', '!"'), ('ivrit', 'QE'),
    ('ivrit', '~t'), ('ivrit', 'O}'),
    # class / \ against [ ] { } ( ) < >
    ('standard', '!%'), ('standard', ';w'), ('standard', '~i'), ('standard', ';p'), ('slant', '!"'), ('slant', 'C&'),
    ('slant', '~i'), ('slant', '?&'), ('small', '!$'), ('small', ';\\'), ('small', '~i'), ('small', "<'"),
    ('big', '!%'), ('big', '<.'), ('big', '~j'), ('big', '<R'), ('ivrit', '!%'), ('ivrit', ';w'),
    ('ivrit', '~i'), ('ivrit', ';p'),
    # class [ ] against { } ( ) < >
    # class { } against ( ) < >
    # class ( ) against < >
    ('slant', '"1'), ('slant', '`1'), ('slant', '}s'), ('slant', '1B'), ('small', '$$'), ('small', '>s'),
    ('small', 'ss'), ('small', '&e'), ('big', '&$'), ('big', '$&'),
    # opposite pair in one order only
    ('standard', '!!'), ('standard', '.:'), ('standard', ',?'), ('slant', '!!'), ('slant', '8`'), ('slant', 'ss'),
    ('slant', ',:'), ('small', '!!'), ('small', ':"'), ('small', '8`'), ('big', '!!'), ('big', '.;'),
    ('big', 'ji'), ('big', '..'), ('ivrit', '!!'), ('ivrit', '.:'), ('ivrit', ',?'),
    # hardblank treated as a letter
    ('big', '_+'), ('big', '_-'), ('big', '+_'),
]


def one_text(rng):
    kind = rng.random()
    if kind < 0.30:                                   # one to three ordinary words
        text = " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 3)))
    elif kind < 0.50:                                 # touching pieces, with and without spaces
        sep = rng.choice(["", "", " "])
        text = sep.join(rng.choice(TRICKY) for _ in range(rng.randint(1, 4)))
    elif kind < 0.62:                                 # a word against a touching piece
        parts = [rng.choice(WORDS), rng.choice(TRICKY), rng.choice(WORDS)][:rng.randint(2, 3)]
        rng.shuffle(parts)
        text = rng.choice(["", " "]).join(parts)
    elif kind < 0.76:                                 # a long sentence that has to wrap
        text = " ".join(rng.choice(WORDS + TRICKY[:12]) for _ in range(rng.randint(6, 14)))
    elif kind < 0.86:                                 # Latin-1 letters and characters the font does not have
        parts = [rng.choice(WORDS), rng.choice(LATIN + UNKNOWN), rng.choice(LATIN + UNKNOWN + WORDS)]
        rng.shuffle(parts)
        text = rng.choice(["", " "]).join(parts[:rng.randint(2, 3)])
    elif kind < 0.93:                                 # raw printable characters
        text = "".join(chr(rng.randint(33, 126)) for _ in range(rng.randint(2, 8)))
    else:                                             # one long word with no space to wrap at
        text = "".join(rng.choice(WORDS) for _ in range(rng.randint(3, 6)))
    extra = rng.random()
    if extra < 0.06:
        text = text.replace(" ", "  ", 1)             # a double space
    elif extra < 0.09:
        text = " " + text                             # a leading space
    elif extra < 0.12:
        text = text + " "                             # a trailing space
    elif extra < 0.15 and " " in text:
        text = text.replace(" ", "\n", 1)             # a line break inside the text
    elif extra < 0.18:
        text = text + "\n"                            # a line break at the end
    return text


def one_args(rng):
    """Options first, each as its own argument with its value next, in any order; then the text."""
    groups = []
    font, text = None, None
    pick = rng.random()
    if pick < 0.09 and RARE:                          # a rare pair, with the font it belongs to
        font, text = rng.choice(RARE)
        if rng.random() < 0.3:
            text = text + " " + rng.choice(WORDS)
    elif pick < 0.23:                                 # one of the two extra fonts
        font = rng.choice(EXTRA_FONTS)
        if font == "term" and rng.random() < 0.5:
            text = rng.choice(TABLES)
    elif pick < 0.88:                                 # one of the eight fonts; otherwise the default font
        font = rng.choice(FONTS)
    if font is not None:
        groups.append(["-f", font])
    if rng.random() < 0.80:
        groups.append(["-w", str(rng.choice(WIDTHS))])
    if rng.random() < 0.65:
        groups.append(["-j", rng.choice(JUSTIFY)])
    if rng.random() < 0.65:
        groups.append(["-D", rng.choice(DIRECTION)])
    for flag in ("-r", "-F", "-s", "-n"):
        if rng.random() < 0.25:
            groups.append([flag])
    rng.shuffle(groups)
    args = [a for g in groups for a in g]
    if text is None:
        text = one_text(rng)
    plain = " " in text and "  " not in text and text == text.strip()
    words = text.split(" ") if plain and rng.random() < 0.5 else [text]
    if any(w == "" or w.startswith("-") for w in words):
        return None                                   # the option parser would read such a word as an option
    return args + words


def load_original():
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ORIGINAL))
    import pyfiglet
    assert pyfiglet.__version__ == "1.0.4", "this is not the pinned pyfiglet"

    step = pyfiglet.FigletBuilder.goToNextChar

    def counted(self):
        # The original loops for ever when a character is exactly as wide as the window. This only counts
        # the steps and stops such a run; it changes nothing in a run that ends.
        self.steps_taken = getattr(self, "steps_taken", 0) + 1
        if self.steps_taken > 100 * len(self.text) + 1000:
            raise RuntimeError("the original never finishes on this input")
        step(self)

    pyfiglet.FigletBuilder.goToNextChar = counted
    return pyfiglet


def run_original(pyfiglet, args):
    """What main() of the original writes to standard output for these arguments, or None if it fails."""
    real_out, real_err, real_argv = sys.stdout, sys.stderr, sys.argv
    raw = io.BytesIO()
    sys.stdout = io.TextIOWrapper(raw, encoding="utf-8", newline="")   # main() detaches it and writes bytes
    sys.stderr = io.StringIO()
    sys.argv = ["pyfiglet"] + list(args)
    try:
        status = pyfiglet.main()
    except (SystemExit, Exception):
        return None
    finally:
        sys.stdout, sys.stderr, sys.argv = real_out, real_err, real_argv
    if status != 0:
        return None
    try:
        out = raw.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        return None
    return out if out.strip() else None


def make_cases(pyfiglet, rng, count, seen):
    cases = []
    while len(cases) < count:
        args = one_args(rng)
        if args is None or tuple(args) in seen:
            continue
        out = run_original(pyfiglet, args)
        if out is None:
            continue
        seen.add(tuple(args))
        cases.append({"args": args, "out": out})
    return cases


def write_cases(path, cases):
    with open(path, "w", encoding="ascii", newline="\n") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=True) + "\n")


def describe(name, cases):
    def value(args, flag, default):
        return args[args.index(flag) + 1] if flag in args else default

    def share(test):
        return "%4.1f%%" % (100.0 * sum(1 for c in cases if test(c["args"])) / len(cases))

    print(name, len(cases), "cases |",
          "right-to-left", share(lambda a: value(a, "-D", "auto") == "right-to-left"), "|",
          "width 10 or 20", share(lambda a: value(a, "-w", "80") in ("10", "20")), "|",
          "center or right", share(lambda a: value(a, "-j", "auto") in ("center", "right")), "|",
          "-r", share(lambda a: "-r" in a), "-F", share(lambda a: "-F" in a),
          "-s", share(lambda a: "-s" in a), "-n", share(lambda a: "-n" in a), "|",
          "term", share(lambda a: value(a, "-f", "") == "term"),
          "ivrit", share(lambda a: value(a, "-f", "") == "ivrit"),
          "no -f", share(lambda a: "-f" not in a), "|",
          "more than one block", "%4.1f%%" % (100.0 * sum(1 for c in cases if c["out"].count("\n") > 12) / len(cases)))


def main():
    pyfiglet = load_original()
    random.seed(7)
    rng = random.Random(7)
    seen = set()
    visible = make_cases(pyfiglet, rng, N, seen)
    hidden = make_cases(pyfiglet, rng, N, seen)
    assert not {tuple(c["args"]) for c in visible} & {tuple(c["args"]) for c in hidden}

    DATA.mkdir(exist_ok=True)
    write_cases(DATA / "visible.jsonl", visible)
    write_cases(DATA / "hidden.jsonl", hidden)
    describe("visible", visible)
    describe("hidden ", hidden)


if __name__ == "__main__":
    main()
