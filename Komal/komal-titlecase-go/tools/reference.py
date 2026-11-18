import hashlib
import importlib.util
import platform
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'titlecase-go/environment/repo/titlecase/__init__.py'
SHA = '42f43e2de55bf003b286c6f8e8d8b2d26676a167'


def load():
    assert platform.python_version() == '3.12.8', platform.python_version()
    assert unicodedata.unidata_version == '15.0.0'
    assert importlib.util.find_spec('regex') is None
    assert digest(SOURCE) == 'a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0'
    spec = importlib.util.spec_from_file_location('original_titlecase', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.REGEX_AVAILABLE is False
    return module


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == '__main__':
    module = load()
    print(dict(commit=SHA, source_sha256=digest(SOURCE), python=platform.python_version(),
               unicode=unicodedata.unidata_version, regex_installed=module.REGEX_AVAILABLE))
