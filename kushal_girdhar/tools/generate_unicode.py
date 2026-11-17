import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import unicodedata


def flags(ch):
    ignorable = ("AΣ" + ch + "!").lower()[1] == "ς" and (
        "AΣ" + ch + "A"
    ).lower()[1] == "σ"
    cased = ("AΣ" + ch + "!").lower()[1] == "σ"
    return (
        (ch == "_" or ch.isalnum())
        | (ch.isspace() << 1)
        | (ignorable << 2)
        | (cased << 3)
    )


def ranges():
    first, previous = 0, 0
    for point in range(sys.maxunicode + 2):
        current = flags(chr(point)) if point <= sys.maxunicode else 0
        if current != previous:
            if previous:
                yield first, point - 1, previous
            first, previous = point, current


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if sys.version_info[:3] != (3, 12, 14) or unicodedata.unidata_version != "15.0.0":
        parser.error("use CPython 3.12.14 with UCD 15.0.0")
    source = ["package main", "var pythonProperties = [...]propertyRange{"]
    source.extend(f"{{{a:#x}, {b:#x}, {mask}}}," for a, b, mask in ranges())
    source.append("}")
    for name in ("upper", "lower", "title"):
        source.append(f"var python{name.title()} = map[rune]string{{")
        operation = getattr(str, name)
        for point in range(sys.maxunicode + 1):
            ch = chr(point)
            mapped = operation(ch)
            if mapped != ch:
                literal = json.dumps(mapped, ensure_ascii=False)
                source.append(f"{point:#x}: {literal},")
        source.append("}")
    args.output.write_bytes(("\n".join(source) + "\n").encode())
    subprocess.run([os.environ.get("GOFMT", "gofmt"), "-w", args.output], check=True)


if __name__ == "__main__":
    main()
