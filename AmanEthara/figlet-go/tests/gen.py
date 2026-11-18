import json
import random
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "pyfiglet"))
from pyfiglet import Figlet, CharNotPrinted

random.seed(7)

FONT_DIR = Path.home() / "pyfiglet/pyfiglet/fonts-standard"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

fonts = sorted(p.stem for p in FONT_DIR.glob("*.flf"))
assert len(fonts) == 67, f"Expected 67 fonts, found {len(fonts)}"

texts = [
    "Hello World", "FIGlet", "Go programming", "Agent evaluation",
    "0123456789", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz",
    "!@#$%^&*()", "[]{}()<>", "one two three four five",
    "A  B   C", "short words here", "wrap these words",
    "cafe", "resume", "Testing 123!", "Go is fast",
    "small text", "a", "AB", "quick brown fox",
    "mixed CASE Text", "test", "hello world",
]

widths = [20, 30, 40, 60, 80, 100, 120]
directions = ["auto", "left-to-right", "right-to-left"]
justifications = ["auto", "left", "center", "right"]

class CaseTimeout(Exception):
    pass

def timeout_handler(signum, frame):
    raise CaseTimeout()

signal.signal(signal.SIGALRM, timeout_handler)

def make_case():
    font = random.choice(fonts)
    width = random.choice(widths)
    direction = random.choice(directions)
    justify = random.choice(justifications)
    text = random.choice(texts)

    if random.random() < 0.35:
        text = " ".join(
            random.choice(["Go", "test", "hello", "world", "agent", "font"])
            for _ in range(random.randint(2, 4))
        )

    width = max(width, max(map(len, text.split()), default=1))

    args = ["-f", font, "-w", str(width), "-D", direction, "-j", justify]

    if random.random() < 0.25:
        args.append("-r")
    if random.random() < 0.25:
        args.append("-F")

    newline_mode = random.choice(["none", "strip", "normalize", "both"])
    if newline_mode in ("strip", "both"):
        args.append("-s")
    if newline_mode in ("normalize", "both"):
        args.append("-n")

    args.append(text)

    for _ in range(1000):
        try:
            rendered = Figlet(
                font=font, width=width,
                direction=direction, justify=justify
            ).renderText(text)
            break
        except CharNotPrinted:
            width += 1
            args[3] = str(width)
    else:
        raise RuntimeError("Could not find a printable width")

    if "-r" in args:
        rendered = rendered.reverse()
    if "-F" in args:
        rendered = rendered.flip()
    if "-s" in args:
        rendered = rendered.strip_surrounding_newlines()
    elif "-n" in args:
        rendered = rendered.normalize_surrounding_newlines()

    return {"args": args, "out": str(rendered) + "\n"}

DATA_DIR.mkdir(parents=True, exist_ok=True)

for filename in ("visible.jsonl", "hidden.jsonl"):
    path = DATA_DIR / filename
    count = 0
    skipped = 0

    with path.open("w", encoding="utf-8", newline="\n") as f:
        while count < 2000:
            signal.alarm(3)
            try:
                case = make_case()
            except CaseTimeout:
                skipped += 1
                if skipped % 10 == 0:
                    print(f"{filename}: skipped {skipped} timed-out cases", flush=True)
                continue
            finally:
                signal.alarm(0)

            f.write(json.dumps(case, ensure_ascii=False) + "\n")
            count += 1

            if count % 100 == 0:
                print(f"{filename}: {count}/2000", flush=True)

    print(f"{filename}: complete; skipped {skipped}", flush=True)

print(f"Fonts: {len(fonts)} | Seed: 7", flush=True)
