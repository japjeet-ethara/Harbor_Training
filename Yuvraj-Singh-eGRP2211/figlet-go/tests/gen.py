#!/usr/bin/env python3
import sys
import os
import io
import json
import random

random.seed(7)

# Insert the sibling pyfiglet folder into sys.path
HERE = os.path.dirname(os.path.abspath(__file__))
SIBLING_PYFIGLET = os.path.abspath(os.path.join(HERE, '..', '..', 'pyfiglet'))
if SIBLING_PYFIGLET not in sys.path:
    sys.path.insert(0, SIBLING_PYFIGLET)

import pyfiglet

FONTS = ['standard', 'slant', 'small', 'big', 'mini', 'banner', 'shadow', 'script']
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTS = ['left', 'right', 'center']
DIRECTIONS = ['left-to-right', 'right-to-left']

TEXTS = [
    # Normal English words
    "hello", "world", "Python", "Go", "figlet", "computer", "programming", "code", "terminal", "test",
    # Tricky characters: | / \ _ [ ] { } ( ) < >
    "|", "/", "\\", "_", "[", "]", "{", "}", "(", ")", "<", ">",
    "|/\\_", "[]{}()<>", "|/\\|", "_[]_", "{()}", "<><>",
    "a|b", "foo/bar", "c:\\path", "x_y", "[tag]", "{key}", "(val)", "<div/>",
    "a|b/c\\d", "/ \\ /", "> < >", "[ ] [ ]",
    # Double spaces
    "hello  world", "foo  bar  baz", "a  b  c", "double  space", "x  y  z",
    # Long sentences that must wrap
    "The quick brown fox jumps over the lazy dog",
    "Sphinx of black quartz, judge my vow",
    "Pack my box with five dozen liquor jugs",
    "How vexingly quick daft zebras jump!",
    "To be or not to be that is the question",
    # Latin-1 letters like é ß ñ
    "café", "naïve", "façade", "coöperation", "fußball", "año", "señor", "piñata", "groß", "über",
    "crème brûlée", "déjà vu", "vis-à-vis",
    # Characters the font does not have
    "alpha beta", "copyright ©", "star ★", "smile 😊", "漢字", "λ func",
]

# Preload font metrics
FONTS_DATA = {name: pyfiglet.Figlet(font=name).Font for name in FONTS}

class CaptureStringIO(io.StringIO):
    def detach(self):
        return self

    def write(self, s):
        if isinstance(s, bytes):
            s = s.decode('utf-8', 'replace')
        return super().write(s)

def capture_pyfiglet(args):
    sio = CaptureStringIO()
    old_stdout = sys.stdout
    old_argv = sys.argv
    sys.stdout = sio
    sys.argv = ['pyfiglet'] + list(args)
    try:
        pyfiglet.main()
    finally:
        sys.stdout = old_stdout
        sys.argv = old_argv
    return sio.getvalue()

def build_args():
    while True:
        font = random.choice(FONTS)
        width = random.choice(WIDTHS)
        args = ['-f', font, '-w', str(width)]

        if random.random() < 0.5:
            args += ['-j', random.choice(JUSTS)]
        if random.random() < 0.5:
            args += ['-D', random.choice(DIRECTIONS)]

        for flag in ('-r', '-F', '-s', '-n'):
            if random.random() < 0.25:
                args.append(flag)

        text = random.choice(TEXTS)
        font_data = FONTS_DATA[font]
        # Avoid terminal width smaller than individual character glyph width
        if all(font_data.width.get(ord(c), 0) < width for c in text):
            args.append(text)
            return args

def generate_cases(count):
    cases = []
    while len(cases) < count:
        args = build_args()
        try:
            out = capture_pyfiglet(args)
        except Exception:
            continue
        cases.append({'args': args, 'out': out})
    return cases

def main():
    data_dir = os.path.join(HERE, 'data')
    os.makedirs(data_dir, exist_ok=True)

    visible_path = os.path.join(data_dir, 'visible.jsonl')
    hidden_path = os.path.join(data_dir, 'hidden.jsonl')

    visible_cases = generate_cases(2000)
    hidden_cases = generate_cases(2000)

    with open(visible_path, 'w', encoding='utf-8') as f:
        for c in visible_cases:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

    with open(hidden_path, 'w', encoding='utf-8') as f:
        for c in hidden_cases:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    main()
