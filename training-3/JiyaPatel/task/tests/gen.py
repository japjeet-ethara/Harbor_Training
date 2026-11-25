import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "python-titlecase"))
from titlecase import titlecase

TRICKY_CASES = [
    "the lord of the rings",
    "war and peace",
    "the end is near",
    "star wars: a new hope",
    "what? a question! an answer; the end",
    "iPhone and NASA",
    "visit https://example.com/foo/bar for info",
    "contact user@example.com for details",
    "state-of-the-art design",
    "either/or choice",
    "don't stop believing",
    "it's a dog's life",
    "mcdonald and macgregor",
    "a clash of kings: book two",
    "the quick brown fox jumps over the lazy dog",
    "v. the people",
    "one vs. two",
    "sub-title: the return of the king",
    "Q&A session on AI and ML",
    "2026: a space odyssey",
    "  leading and trailing spaces  ",
    "ALL CAPS TITLE WITH A SMALL WORD",
    "step-by-step guide to go",
    "in-and-out burger",
    "for whom the bell tolls",
]

WORDS = [
    "the", "of", "and", "in", "to", "a", "an", "for", "on", "with", "at", "by", "from",
    "lord", "rings", "star", "wars", "hope", "new", "world", "king", "queen", "dragon",
    "iPhone", "NASA", "macOS", "GitHub", "API", "Go", "Python", "mcdonald", "macarthur",
    "state-of-the-art", "either/or", "don't", "it's", "https://example.com/test",
    "admin@site.org", "v.", "vs.", "via", "as", "but", "if", "or", "nor", "end", "start"
]

SEPS = [" ", " ", " ", ": ", " - ", " / ", "; ", "? ", "! "]

def make_titles(rng, n):
    titles = []
    for i in range(n):
        if i < len(TRICKY_CASES):
            titles.append(TRICKY_CASES[i])
        else:
            length = rng.randint(2, 9)
            parts = [rng.choice(WORDS)]
            for _ in range(length - 1):
                parts.append(rng.choice(SEPS) + rng.choice(WORDS))
            titles.append("".join(parts).replace("\n", " ").replace("\r", " "))
    return titles

def main():
    rng = random.Random(1)
    vis_in = make_titles(rng, 2000)
    hid_in = make_titles(rng, 2000)
    vis_exp = [titlecase(t).replace("\n", " ").replace("\r", " ") for t in vis_in]
    hid_exp = [titlecase(t).replace("\n", " ").replace("\r", " ") for t in hid_in]
    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "inputs.txt").write_text("\n".join(vis_in) + "\n", encoding="utf-8")
    (out_dir / "expected.txt").write_text("\n".join(vis_exp) + "\n", encoding="utf-8")
    (out_dir / "hidden_inputs.txt").write_text("\n".join(hid_in) + "\n", encoding="utf-8")
    (out_dir / "hidden_expected.txt").write_text("\n".join(hid_exp) + "\n", encoding="utf-8")
    print("Generated 4 deterministic data files (2000 lines each).")

if __name__ == "__main__":
    main()
