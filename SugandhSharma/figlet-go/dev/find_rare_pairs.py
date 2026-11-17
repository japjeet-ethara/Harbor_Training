"""Finds two-character texts whose drawing depends on one small part of the smushing rules.

For every font with smushing rules, both directions and every ordered pair of printable ASCII characters, the
original draws the pair; then a copy of smushChars with ONE part switched off draws it again. A pair whose
drawing changes is a rare case for that part. The pairs found here are the RARE list of tests/gen.py.

Usage (from the task folder):  python dev/find_rare_pairs.py ..
"""
import sys
from pathlib import Path

work = Path(sys.argv[1])
sys.dont_write_bytecode = True
sys.path.insert(0, str(work / "pyfiglet"))
import pyfiglet

original_smush = pyfiglet.FigletBuilder.smushChars


def variant(drop=None, one_order=False, hardblank_letter=False):
    """smushChars of the original, copied line by line, with one part that can be switched off."""
    def smushChars(self, left='', right=''):
        if left == ' ':
            return right
        if right == ' ':
            return left
        if (self.prevCharWidth < 2) or (self.curCharWidth < 2):
            return
        if (self.font.smushMode & self.SM_SMUSH) == 0:
            return
        if (self.font.smushMode & 63) == 0:
            if left == self.font.hardBlank:
                return right
            if right == self.font.hardBlank:
                return left
            if self.direction == 'right-to-left':
                return left
            else:
                return right
        if self.font.smushMode & self.SM_HARDBLANK:
            if (left == self.font.hardBlank and right == self.font.hardBlank):
                return left
        if not hardblank_letter and (left == self.font.hardBlank or right == self.font.hardBlank):
            return
        if self.font.smushMode & self.SM_EQUAL:
            if left == right:
                return left
        smushes = ()
        if self.font.smushMode & self.SM_LOWLINE:
            smushes += (('_', r'|/\[]{}()<>'),)
        if self.font.smushMode & self.SM_HIERARCHY:
            classes = [('|', r'/\[]{}()<>'), (r'\/', '[]{}()<>'), ('[]', '{}()<>'), ('{}', '()<>'), ('()', '<>')]
            if drop is not None:
                classes[drop] = (classes[drop][0], '')
            smushes += tuple(classes)
        for a, b in smushes:
            if left in a and right in b:
                return right
            if right in a and left in b:
                return left
        if self.font.smushMode & self.SM_PAIR:
            for pair in ([left + right] if one_order else [left + right, right + left]):
                if pair in ['[]', '{}', '()']:
                    return '|'
        if self.font.smushMode & self.SM_BIGX:
            if (left == '/') and (right == '\\'):
                return '|'
            if (right == '/') and (left == '\\'):
                return 'Y'
            if (left == '>') and (right == '<'):
                return 'X'
        return
    return smushChars


VARIANTS = {
    "class | against / \\ [ ] { } ( ) < >": dict(drop=0),
    "class / \\ against [ ] { } ( ) < >": dict(drop=1),
    "class [ ] against { } ( ) < >": dict(drop=2),
    "class { } against ( ) < >": dict(drop=3),
    "class ( ) against < >": dict(drop=4),
    "opposite pair in one order only": dict(one_order=True),
    "hardblank treated as a letter": dict(hardblank_letter=True),
}
FONTS = ["standard", "slant", "small", "big", "ivrit"]
CHARS = [chr(c) for c in range(33, 127)]

figlets = {(f, d): pyfiglet.Figlet(font=f, direction=d) for f in FONTS for d in ("left-to-right", "right-to-left")}


def draw_all():
    out = {}
    for key, fig in figlets.items():
        for a in CHARS:
            for b in CHARS:
                try:
                    out[key + (a + b,)] = str(fig.renderText(a + b))
                except Exception:
                    out[key + (a + b,)] = None
    return out


reference = draw_all()
pyfiglet.FigletBuilder.smushChars = variant()
assert draw_all() == reference, "the copy of smushChars is not the same as the original"

found = {}
for name, switches in VARIANTS.items():
    pyfiglet.FigletBuilder.smushChars = variant(**switches)
    changed = [k for k, v in draw_all().items() if v != reference[k] and reference[k] is not None]
    found[name] = changed
    print(f"{name:40s} {len(changed):5d} pairs change")
pyfiglet.FigletBuilder.smushChars = original_smush

# A short list for tests/gen.py: for every part up to four pairs per font, left-to-right ones first.
print("\nRARE = [")
seen = set()
for name, changed in found.items():
    print(f"    # {name}")
    line = []
    for font in FONTS:
        picks = [k for k in changed if k[0] == font and not k[2].startswith("-")]
        picks.sort(key=lambda k: (k[1] != "left-to-right", k[2]))
        step = max(1, len(picks) // 4)
        for k in picks[::step][:4]:
            if (k[0], k[2]) not in seen:
                seen.add((k[0], k[2]))
                line.append((k[0], k[2]))
    for i in range(0, len(line), 6):
        print("    " + " ".join(repr(t) + "," for t in line[i:i + 6]))
print("]")
