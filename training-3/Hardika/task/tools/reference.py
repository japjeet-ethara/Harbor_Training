import importlib.metadata
import sys
import unicodedata
from pathlib import Path

import regex

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "environment" / "upstream"
PYTHON = (3, 12, 14)
REGEX = "2026.11.15"

if (
    sys.implementation.name != "cpython"
    or sys.version_info[:3] != PYTHON
    or unicodedata.unidata_version != "15.0.0"
    or importlib.metadata.version("regex") != REGEX
    or regex.DEFAULT_VERSION != regex.VERSION0
):
    raise RuntimeError("Use CPython 3.12.14 (Unicode 15.0.0) with regex 2026.11.15 (V0).")

sys.path.insert(0, str(UPSTREAM))
import titlecase as upstream

if not upstream.REGEX_AVAILABLE or Path(upstream.__file__).parent != UPSTREAM / "titlecase":
    raise RuntimeError("Expected the pinned upstream checkout using the optional regex engine.")

titlecase = upstream.titlecase


def lf_records(data):
    if data and not data.endswith(b"\n"):
        raise ValueError("Expected the dataset to end in LF")
    return data.split(b"\n")[:-1]


def record_bytes(records):
    return b"".join(item.encode("utf-8") + b"\n" for item in records)
