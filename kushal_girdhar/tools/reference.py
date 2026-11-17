import re
import sys
import unicodedata
from pathlib import Path

COMMIT = "42f43e2de55bf003b286c6f8e8d8b2d26676a167"
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "environment" / "repo"


def load():
    if sys.implementation.name != "cpython" or sys.version_info[:3] != (3, 12, 14):
        raise RuntimeError("use CPython 3.12.14")
    if unicodedata.unidata_version != "15.0.0":
        raise RuntimeError("expected Unicode 15.0.0")
    sys.path.insert(0, str(SOURCE))
    import titlecase

    if titlecase.REGEX_AVAILABLE or titlecase.regex is not re:
        raise RuntimeError("use a clean Python environment without the optional regex package")
    if Path(titlecase.__file__).resolve().parent != SOURCE / "titlecase":
        raise RuntimeError("the imported module is outside the pinned source")
    return titlecase.titlecase


def describe():
    return {
        "python": sys.version,
        "unicode": unicodedata.unidata_version,
        "regex": "stdlib re; optional regex unavailable",
        "upstream_commit": COMMIT,
    }


def framed(records):
    return b"".join(record.encode("utf-8") + b"\n" for record in records)
