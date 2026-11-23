"""Behaviour criterion over the frozen 100,000-title hidden exam.

The score is the fraction of lines matching the reference byte for byte, but a
submission only keeps that score when it clears the shared structural audit,
a minimum overall accuracy and a minimum edge-case accuracy. Below the
thresholds the partial credit is reduced sharply so a weak or naive port cannot
collect most of the reward, and a rule violation scores zero outright.
"""

import importlib.util
import re
from pathlib import Path

from rewardkit import criterion

_SPEC = importlib.util.spec_from_file_location(
    "tc_common", Path(__file__).with_name("_common.py")
)
_common = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_common)

BIN = Path("/tmp/tc_behaviour_bin")

OVERALL_FLOOR = 0.98
EDGE_FLOOR = 0.95
BELOW_FLOOR_FACTOR = 0.10

HONORIFIC = re.compile(r"(?i)\b(?:mr|mrs|ms|dr)\b")
MC_MAC = re.compile(r"(?i)\b(?:mc|mac)\w+")
SUB_PHRASE = re.compile(r"[:.;?!\-\u2012\u2013\u2014\u2015] ")
INLINE_PERIOD = re.compile(r"\w\.\w")
VERSION = re.compile(r"\d+\.\d+")
ALLCAPS = re.compile(r"\b[A-Z]{2,}\b")
CONSONANTS = re.compile(r"(?i)\b[bcdfghjklmnpqrstvwxz]{3,}\b")


def _is_edge(line: bytes) -> bool:
    text = line.decode("utf-8", "replace")
    if any(ord(char) > 127 for char in text):
        return True
    if "\t" in text or "\u00a0" in text:
        return True
    if "'" in text or "\u2018" in text:
        return True
    if HONORIFIC.search(text) or MC_MAC.search(text):
        return True
    if ALLCAPS.search(text) or CONSONANTS.search(text):
        return True
    if INLINE_PERIOD.search(text) or VERSION.search(text):
        return True
    if "/" in text or "-" in text or "_" in text:
        return True
    return SUB_PHRASE.search(text) is not None


@criterion(description="fraction of hidden inputs matching Python titlecase() byte for byte")
def behaviour(workspace: Path) -> float:
    result = _common.exam(workspace, BIN)
    if result is None:
        return 0.0
    stdout, inputs, expected, _ = result

    expected_lines = _common._lines(expected)
    actual_lines = _common._lines(stdout)
    input_lines = _common._lines(inputs)
    if not expected_lines:
        return 0.0

    hits = 0
    edge_hits = 0
    edge_total = 0
    for index, expected_line in enumerate(expected_lines):
        matched = index < len(actual_lines) and actual_lines[index] == expected_line
        if matched:
            hits += 1
        edge = index < len(input_lines) and _is_edge(input_lines[index])
        if edge:
            edge_total += 1
            if matched:
                edge_hits += 1

    overall = hits / len(expected_lines)
    edge = edge_hits / edge_total if edge_total else overall
    if overall < OVERALL_FLOOR or edge < EDGE_FLOOR:
        return round(overall * BELOW_FLOOR_FACTOR, 6)
    return overall
