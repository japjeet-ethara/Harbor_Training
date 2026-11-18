"""
gen.py – Generate visible.jsonl and hidden.jsonl for the figlet-go Harbor task.

Run from anywhere inside the task tree or workspace:
    python figlet-go/tests/gen.py
    python tests/gen.py (when inside figlet-go/)

Output files:
    tests/data/visible.jsonl  (2000 cases)
    tests/data/hidden.jsonl   (2000 different cases)

Each line format:
    {"args": [...], "out": "..."}
"""

import io
import json
import pathlib
import random
import sys

# Locate pyfiglet next to task folder
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
TASK_DIR = SCRIPT_DIR.parent
WORKSPACE = TASK_DIR.parent
PYFIGLET_DIR = WORKSPACE / "pyfiglet"

if str(PYFIGLET_DIR) not in sys.path:
    sys.path.insert(0, str(PYFIGLET_DIR))

import pyfiglet  # noqa: E402

# Guard against pyfiglet's infinite loop bug when a word exceeds column width.
# In pyfiglet, when no space exists in the buffer and width is exceeded,
# cutBufferAtLastChar() decrements iterator and goToNextChar() increments it,
# looping forever. Raising CharNotPrinted lets us safely discard the impossible case.
orig_cut = pyfiglet.FigletBuilder.cutBufferAtLastChar


def _safe_cutBufferAtLastChar(self):
    raise pyfiglet.CharNotPrinted("Word exceeds line width")


pyfiglet.FigletBuilder.cutBufferAtLastChar = _safe_cutBufferAtLastChar

orig_add = pyfiglet.FigletBuilder.addCharToProduct


def _safe_addCharToProduct(self):
    if not hasattr(self, "_step_count"):
        self._step_count = 0
    self._step_count += 1
    if self._step_count > len(self.text) * 20 + 200:
        raise pyfiglet.CharNotPrinted("Loop step limit exceeded")
    return orig_add(self)


pyfiglet.FigletBuilder.addCharToProduct = _safe_addCharToProduct

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFIES = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

N_VISIBLE = 2000
N_HIDDEN = 2000

# ---------------------------------------------------------------------------
# Text corpus
# ---------------------------------------------------------------------------
NORMAL_WORDS = [
    "hello", "world", "figlet", "harbor", "task", "go", "code", "terminal",
    "banner", "quick", "brown", "fox", "jumps", "dog", "build", "output",
    "text", "line", "simple", "left", "right", "center", "auto", "font",
    "width", "wrap", "ascii", "art", "render", "smush", "kern",
]

# Smushing rule test cases from NOTES.md
NOTES_RARE = [
    # Equal character
    "AA", "BB", "CC", "||", "//",
    # Underscore rule
    "_|", "|_", "_/", "/_", "_\\", "\\_", "_[", "]_",
    "_{", "}_", "_(", ")_", "_<", ">_",
    # Hierarchy rule
    "|/", "/|", "|\\", "\\|", "/[", "]/", "[{", "}]", "(){", "()<", ">{}", "{(",
    # Opposite pair rule
    "[]", "][", "{}", "}{", "()", ")(",
    # Big X rule
    "/\\", "\\/", "><", "<>",
    # Hardblank rule
    "$", "$$", "$ $", "A$B",
    # Kerning
    "AV", "VA", "Ty", "Wa", "To", "Ta", "FA", "PA",
    # Raw punctuation run
    "| / \\ _ [ ] { } ( ) < >",
]

DOUBLE_SPACES = [
    "hello  world",
    "foo  bar  baz",
    "a  b  c",
    "space  test  here",
    "mix  |  and  /",
    "left  right  center",
]

LONG_SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "FIGlet is a program that generates text banners in ASCII art.",
    "Harbor tasks evaluate code against reference outputs for exact equivalence.",
    "When column width is limited text must wrap cleanly at word boundaries.",
    "The standard font has smushing rules one through six plus kerning.",
    "Big X smushing turns slash backslash into pipe and backslash slash into Y.",
]

LATIN1 = [
    "café", "Straße", "año", "über", "crème", "naïve",
    "façade", "piñata", "señor", "groß", "Fußball",
    "élégant", "mañana", "é ß ñ",
]

MISSING_CHARS = [
    "hello 😊 world",
    "cost is 100€ or 500¥",
    "rocket 🚀 launch 🎉",
    "unicode ★ symbols ♠ ♣ ♥ ♦",
    "section § copyright ©",
    "你好 世界",
    "こんにちは",
    "α β γ δ ε ζ η θ",
]

_pool_rng = random.Random(42)
TWO_WORDS = [" ".join(_pool_rng.sample(NORMAL_WORDS, k=2)) for _ in range(50)]
THREE_WORDS = [" ".join(_pool_rng.sample(NORMAL_WORDS, k=3)) for _ in range(50)]
MIXED_RARE = [
    f"{_pool_rng.choice(NORMAL_WORDS)} {t} {_pool_rng.choice(NORMAL_WORDS)}"
    for t in NOTES_RARE[:20]
]

TEXT_POOL = (
    NORMAL_WORDS
    + TWO_WORDS
    + THREE_WORDS
    + NOTES_RARE
    + DOUBLE_SPACES
    + LONG_SENTENCES
    + LATIN1
    + MISSING_CHARS
    + MIXED_RARE
)


# ---------------------------------------------------------------------------
# Runner (captures stdout from pyfiglet.main() in-process)
# ---------------------------------------------------------------------------
class _MockStdout:
    def __init__(self) -> None:
        self.buf = io.BytesIO()

    def detach(self) -> io.BytesIO:
        return self.buf

    def write(self, data) -> int:
        if isinstance(data, str):
            data = data.encode("utf-8")
        return self.buf.write(data)

    def flush(self) -> None:
        pass


def _run_pyfiglet(argv_tail: list[str]) -> str | None:
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    orig_argv = sys.argv

    mock = _MockStdout()
    sys.stdout = mock
    sys.stderr = io.StringIO()
    sys.argv = ["pyfiglet"] + argv_tail

    try:
        ret = pyfiglet.main()
        if ret not in (None, 0):
            return None
        return mock.buf.getvalue().decode("utf-8")
    except (pyfiglet.CharNotPrinted, SystemExit):
        return None
    except Exception:
        return None
    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        sys.argv = orig_argv


def _make_args(rng: random.Random, text: str) -> list[str]:
    args: list[str] = []

    args += ["-f", rng.choice(FONTS)]
    args += ["-w", str(rng.choice(WIDTHS))]
    args += ["-j", rng.choice(JUSTIFIES)]
    args += ["-D", rng.choice(DIRECTIONS)]

    if rng.randint(0, 3) == 0:
        args.append("-r")
    if rng.randint(0, 3) == 0:
        args.append("-F")
    if rng.randint(0, 3) == 0:
        args.append("-s")
    if rng.randint(0, 3) == 0:
        args.append("-n")

    args.append(text)
    return args


def generate_split(n: int, rng: random.Random, seen: set) -> list[dict]:
    cases: list[dict] = []
    attempts = 0
    max_attempts = n * 50

    while len(cases) < n and attempts < max_attempts:
        attempts += 1
        text = rng.choice(TEXT_POOL)
        argv_tail = _make_args(rng, text)
        key = tuple(argv_tail)
        if key in seen:
            continue

        out = _run_pyfiglet(argv_tail)
        if out is None:
            continue

        seen.add(key)
        cases.append({"args": argv_tail, "out": out})

        if len(cases) % 400 == 0:
            print(f"  progress: {len(cases)}/{n}", flush=True)

    if len(cases) < n:
        raise RuntimeError(f"Could only generate {len(cases)} of {n} cases")
    return cases


def main():
    random.seed(7)
    rng = random.Random(7)

    out_dir = SCRIPT_DIR / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    seen = set()

    print(f"Generating {N_VISIBLE} visible cases...", flush=True)
    visible_cases = generate_split(N_VISIBLE, rng, seen)
    visible_file = out_dir / "visible.jsonl"
    with visible_file.open("w", encoding="utf-8") as f:
        for c in visible_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote {len(visible_cases)} cases to {visible_file}", flush=True)

    print(f"Generating {N_HIDDEN} hidden cases...", flush=True)
    hidden_cases = generate_split(N_HIDDEN, rng, seen)
    hidden_file = out_dir / "hidden.jsonl"
    with hidden_file.open("w", encoding="utf-8") as f:
        for c in hidden_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote {len(hidden_cases)} cases to {hidden_file}", flush=True)

    print("Complete!", flush=True)


if __name__ == "__main__":
    main()
