import hashlib
import importlib.util
import json
import platform
import re
import sys
import unicodedata
from pathlib import Path


def ranges(values):
    result = []
    for n in values:
        if result and result[-1][1] + 1 == n:
            result[-1][1] = n
        else:
            result.append([n, n])
    return result


def main():
    assert platform.python_version() == '3.12.8'
    assert importlib.util.find_spec('regex') is None
    output = Path(sys.argv[1])
    word, space, cased, ignorable = [], [], [], []
    upper, lower, title, fold = {}, {}, {}, {}
    ascii_patterns = [(x, re.compile(x, re.I)) for x in 'abcdefghijklmnopqrstuvwxyz']
    ascii_fold = re.compile('[a-z]', re.I)
    for n in range(0x110000):
        if 0xD800 <= n <= 0xDFFF:
            continue
        c = chr(n)
        if re.fullmatch(r'\w', c):
            word.append(n)
        if re.fullmatch(r'\s', c):
            space.append(n)
        if c.islower() or c.isupper() or c.istitle():
            cased.append(n)
        if ('AΣ' + c + 'A').lower()[1] == 'σ' and ('AΣ' + c).lower()[1] == 'ς':
            ignorable.append(n)
        for table, value in [(upper, c.upper()), (lower, c.lower()), (title, c.title())]:
            if value != c:
                table[str(n)] = value
        if ascii_fold.fullmatch(c):
            for a, pattern in ascii_patterns:
                if pattern.fullmatch(c):
                    fold[str(n)] = a
                    break
    data = dict(word=ranges(word), space=ranges(space), cased=ranges(cased),
                ignorable=ranges(ignorable), upper=upper, lower=lower, title=title, fold=fold)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=True, separators=(',', ':')) + '\n', encoding='utf-8')
    print(json.dumps(dict(python=platform.python_version(), unicode=unicodedata.unidata_version,
                         regex_installed=False, sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                         ranges={k: len(data[k]) for k in ['word', 'space', 'cased', 'ignorable']},
                         mappings={k: len(data[k]) for k in ['upper', 'lower', 'title', 'fold']}), indent=2))


if __name__ == '__main__':
    main()
