"""Isolated pyfiglet oracle invocation used by gen.py's killable timeout."""
import contextlib
import io
import json
import sys

sys.path.insert(0, sys.argv[1])
import pyfiglet

args = json.loads(sys.argv[2])
name, font, width, _j, justify, _d, direction, *rest = args
flags = set(rest[:-1])
text = rest[-1]
f = pyfiglet.Figlet(font=font, width=int(width), justify=justify, direction=direction)
try:
    rendered = f.renderText(text)
except pyfiglet.CharNotPrinted:
    raise SystemExit(2)
if "-r" in flags:
    rendered = rendered.reverse()
if "-F" in flags:
    rendered = rendered.flip()
if "-s" in flags:
    rendered = rendered.strip_surrounding_newlines()
elif "-n" in flags:
    rendered = rendered.normalize_surrounding_newlines()
sys.stdout.write(json.dumps(rendered + "\n", ensure_ascii=False))
