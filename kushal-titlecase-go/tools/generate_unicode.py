import ctypes
import hashlib
import json
import sys
from pathlib import Path

import regex


def ranges(values):
    result = []
    start = previous = None
    for value in values:
        if start is None:
            start = previous = value
        elif value == previous + 1:
            previous = value
        else:
            result.extend((start, previous))
            start = previous = value
    if start is not None:
        result.extend((start, previous))
    return result


def main():
    predicates = {
        "letters": regex.compile(r"\p{Letter}\Z").fullmatch,
        "foldedLetters": regex.compile(r"\p{Letter}\Z", regex.I).fullmatch,
        "upperLetters": regex.compile(r"\p{Lu}\Z").fullmatch,
        "wordChars": regex.compile(r"\w\Z").fullmatch,
        "spaceChars": regex.compile(r"\s\Z").fullmatch,
    }
    for name, symbol in (("casedChars", "_PyUnicode_IsCased"), ("ignorableChars", "_PyUnicode_IsCaseIgnorable")):
        function = getattr(ctypes.pythonapi, symbol)
        function.argtypes = [ctypes.c_uint32]
        function.restype = ctypes.c_int
        predicates[name] = lambda value, function=function: function(ord(value))
    properties = {name: [] for name in predicates}
    casing = {"upperMap": {}, "lowerMap": {}, "titleMap": {}}
    folds = {}
    ascii_match = regex.compile(r"[a-z]\Z", regex.I)
    matchers = {letter: regex.compile(letter + r"\Z", regex.I) for letter in "abcdefghijklmnopqrstuvwxyz"}
    for code in range(0x110000):
        if 0xD800 <= code <= 0xDFFF:
            continue
        char = chr(code)
        for name, predicate in predicates.items():
            if predicate(char):
                properties[name].append(code)
        for name, mapped in (("upperMap", char.upper()), ("lowerMap", char.lower()), ("titleMap", char.title())):
            if mapped != char:
                casing[name][code] = mapped
        if ascii_match.fullmatch(char):
            matches = [letter for letter, matcher in matchers.items() if matcher.fullmatch(char)]
            if len(matches) != 1:
                raise ValueError((code, matches))
            if char != matches[0]:
                folds[code] = matches[0]
    parts = ['package main\n']
    for name, values in properties.items():
        rows = ranges(values)
        parts.append(f"var {name} = []rune{{\n")
        for index in range(0, len(rows), 12):
            parts.append("\t" + ", ".join(hex(value) for value in rows[index:index + 12]) + ",\n")
        parts.append("}\n")
    for name, table in {**casing, "foldMap": folds}.items():
        parts.append(f"var {name} = map[rune]string{{\n")
        for code, value in table.items():
            parts.append(f"\t{hex(code)}: {json.dumps(value, ensure_ascii=False)},\n")
        parts.append("}\n")
    content = "\n".join(parts)
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(json.dumps({"path": str(output), "bytes": output.stat().st_size, "sha256": hashlib.sha256(content.encode()).hexdigest(), "regex": regex.__version__}))


if __name__ == "__main__":
    main()
