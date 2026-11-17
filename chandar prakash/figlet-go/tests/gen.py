#!/usr/bin/env python3
import json
import os
import random
import sys
from pathlib import Path

# Add pyfiglet to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYFIGLET_DIR = REPO_ROOT / "pyfiglet"
sys.path.insert(0, str(PYFIGLET_DIR))

import pyfiglet
from pyfiglet import CharNotPrinted

FONTS = ["standard", "slant", "small", "big", "mini", "banner", "shadow", "script"]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFIES = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

TRICKY_TEXTS = [
    # Smushing pairs and operators
    "AA", "XX", "||", "__", "++", "--",
    "_|", "|_", "/|", "|/", "\\|", "|\\",
    "/\\", "\\/", "><", "<>",
    "[]", "][", "{}", "}{", "()", ")(",
    "<_>", "[|]", "{/}", "(\\)",
    "| / \\ _ [ ] { } ( ) < >",
    "|| // \\\\ __ [[ ]] {{ }} (( )) << >>",
    "/|\\ /|\\ _|_",
    "[[((||))]]",
    "|/|/|/|",
    "_/_/_/_",
    "> <", "\\ /", "/ \\",
    "smush: /\\ and \\/ and ><",
    "foo | bar / baz \\ qux",
    "[a] {b} (c) <d>",
    "|_|",
    "/_\\",
    "\\_/",
    "|X|",
    # Whitespace tests
    "hello  world",
    "a   b",
    "  leading",
    "trailing  ",
    "  both  ",
    "foo   bar   baz",
    # Long sentences that wrap
    "The quick brown fox jumps over the lazy dog.",
    "FIGlet is a program that generates text banners from ordinary text.",
    "Smushing rules stack together when giant letters stand next to each other.",
    "A twin of the machine in Go matching every single space and slash.",
    "Testing narrow width wrapping with several words in one line.",
    # Latin-1 / accents
    "café", "Straße", "über", "naïve", "señor", "ÄÖÜ äöü ß", "coöperation",
    # Characters missing from FIGlet fonts
    "hello 🚀 world", "test 中文 text", "alpha α beta β", "smile 😊",
    # Normal short words and phrases
    "hello", "world", "Harbor", "Go", "Docker", "test", "FIGlet", "smush",
    "ASCII", "code", "Go 1.23", "Alpine", "OK", "YES", "NO", "12345",
]

# Pre-load font definitions to speed up generation
FONTS_CACHE = {f: pyfiglet.FigletFont(f) for f in FONTS}

def render_case(font, width, justify, direction, r, F, s, n, text):
    fig = pyfiglet.Figlet.__new__(pyfiglet.Figlet)
    fig.font = font
    fig._direction = direction
    fig._justify = justify
    fig.width = width
    fig.Font = FONTS_CACHE[font]
    fig.engine = pyfiglet.FigletRenderingEngine(base=fig)
    
    res = fig.renderText(text)
    if r:
        res = res.reverse()
    if F:
        res = res.flip()
    if s:
        res = res.strip_surrounding_newlines()
    elif n:
        res = res.normalize_surrounding_newlines()
    return res + "\n"

def make_case(seen_keys):
    while True:
        font = random.choice(FONTS)
        width = random.choice(WIDTHS)
        justify = random.choice(JUSTIFIES)
        direction = random.choice(DIRECTIONS)
        
        # 1 in 4 chance for each flag
        flag_r = (random.randint(1, 4) == 1)
        flag_F = (random.randint(1, 4) == 1)
        flag_s = (random.randint(1, 4) == 1)
        flag_n = (random.randint(1, 4) == 1)
        
        # Pick text: either a single tricky text or combined
        if random.random() < 0.7:
            text = random.choice(TRICKY_TEXTS)
        else:
            text = f"{random.choice(TRICKY_TEXTS)} {random.choice(TRICKY_TEXTS)}"
        
        f_obj = FONTS_CACHE[font]
        max_char_w = max((f_obj.width.get(ord(c), 0) for c in text), default=0)
        # In pyfiglet, width must strictly exceed character width
        if width <= max_char_w:
            continue
            
        args = ["-f", font, "-w", str(width), "-j", justify, "-D", direction]
        if flag_r:
            args.append("-r")
        if flag_F:
            args.append("-F")
        if flag_s:
            args.append("-s")
        if flag_n:
            args.append("-n")
        args.append(text)
        
        key = " ".join(args)
        if key in seen_keys:
            continue
            
        try:
            out = render_case(font, width, justify, direction, flag_r, flag_F, flag_s, flag_n, text)
            seen_keys.add(key)
            return {"args": args, "out": out}
        except CharNotPrinted:
            continue

def main():
    random.seed(7)
    
    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    visible_file = out_dir / "visible.jsonl"
    hidden_file = out_dir / "hidden.jsonl"
    
    seen_keys = set()
    
    print("Generating 2000 visible cases...", flush=True)
    with open(visible_file, "w", encoding="utf-8") as f:
        for _ in range(2000):
            case = make_case(seen_keys)
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
            
    print("Generating 2000 hidden cases (completely disjoint)...", flush=True)
    with open(hidden_file, "w", encoding="utf-8") as f:
        for _ in range(2000):
            case = make_case(seen_keys)
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
            
    print("Done generating test cases.", flush=True)

if __name__ == "__main__":
    main()
