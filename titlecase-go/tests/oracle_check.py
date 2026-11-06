"""Build and check titlecase datasets against the bundled Python oracle.

The oracle is python-titlecase with the third-party ``regex`` module importable,
which is the Unicode-property path required by instruction.md. Expected strings
are produced by calling ``titlecase()``; they are not hand-written.

Usage:
    python tests/oracle_check.py --write
    python tests/oracle_check.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_REPO = ROOT / "environment" / "python-titlecase"
VISIBLE_PATHS = (
    ROOT / "tests" / "data" / "visible.json",
    ROOT / "environment" / "visible_cases.json",
)
HIDDEN_PATH = ROOT / "tests" / "data" / "hidden.json"


def load_oracle():
    try:
        import regex  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "The regex module is required so the oracle uses Unicode properties."
        ) from exc
    sys.path.insert(0, str(PY_REPO))
    from titlecase import create_wordlist_filter_from_file, titlecase
    from titlecase.tests import TEST_DATA

    return titlecase, create_wordlist_filter_from_file, TEST_DATA


def _case(
    case_id,
    text,
    *,
    use_default=False,
    small_first_last=True,
    preserve_blank_lines=False,
    normalise_space_characters=False,
    callback=None,
):
    return {
        "id": case_id,
        "text": text,
        "use_default": use_default,
        "small_first_last": small_first_last,
        "preserve_blank_lines": preserve_blank_lines,
        "normalise_space_characters": normalise_space_characters,
        "callback": callback,
    }


def visible_inputs():
    return [
        _case("empty", "", use_default=True),
        _case("a-thing", "a thing", use_default=True),
        _case("readme-lower", "this is a test", use_default=True),
        _case("readme-upper", "THIS IS A TEST", use_default=True),
        _case("readme-internal-caps", "this is a TEST", use_default=True),
        _case("small-v-and-vs", "this v that vs. the rest", use_default=True),
        _case(
            "small-word-at-end",
            "Small word at end is nothing to be afraid of",
            use_default=True,
        ),
        _case("slash-and-or", "a title and/or string", use_default=True),
        _case(
            "hyphen-and-slash",
            "a-b end-to-end two-not-three/three-by-four/five-and",
            use_default=True,
        ),
        _case(
            "em-dash-all-caps",
            "EPISODE 7 — THE FORCE AWAKENS",
            use_default=True,
        ),
        _case(
            "initials",
            "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
            use_default=True,
        ),
        _case("oreilly", "my name is o'reilly", use_default=True),
        _case("mc-name", "Mr McTavish went to MacDonalds", use_default=True),
        _case(
            "consonant-acronym",
            "Words with all consonants like cnn are acronyms",
            use_default=True,
        ),
        _case(
            "domains",
            "this is just an example.com and this is http://foo.com",
            use_default=True,
        ),
        _case(
            "blank-lines-default",
            "Line number one\n\nand Line three\n",
            use_default=True,
        ),
        _case(
            "blank-lines-preserve",
            "Line number one\n\nand Line three\n",
            preserve_blank_lines=True,
        ),
        _case("tabs-kept", "text\twith\ttabs"),
        _case(
            "tabs-normalised",
            "text\twith\ttabs",
            normalise_space_characters=True,
        ),
        _case("unicode-nino", "EL NIÑO A ARRIVÉ HIER", use_default=True),
        _case(
            "subphrase-colon",
            "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
            use_default=True,
        ),
        _case(
            "callback-abbreviations",
            "a simple tcp and udp wrapper",
            callback={"kind": "upper_if", "words": ["TCP", "UDP"]},
        ),
        _case(
            "wordlist-all-caps",
            "SENDING UDP PACKETS OVER PPPOE WORKS GREAT",
            callback={"kind": "wordlist", "lines": ["UDP", "PPPoE"]},
        ),
        _case(
            "explicit-defaults",
            "a thing",
            small_first_last=True,
            preserve_blank_lines=False,
            normalise_space_characters=False,
        ),
    ]


def hidden_inputs(test_data):
    cases = []
    for index, (text, _expected) in enumerate(test_data, start=1):
        cases.append(_case(f"py-{index:03d}", text, use_default=True))
    cases.extend(
        [
            _case("leading-space", " a thing"),
            _case("crlf-collapse", "alpha\r\nbeta"),
            _case("crlf-preserve", "alpha\r\nbeta", preserve_blank_lines=True),
            _case("double-space", "a  thing"),
            _case(
                "double-space-normalise",
                "a  thing",
                normalise_space_characters=True,
            ),
            _case("double-slash", "foo//bar"),
            _case("all-caps-at-and-t", "AT&T ROCKS THE WORLD"),
            _case("honorific-tails", "DR AND MRS SMITH"),
            _case("mc-internal-capital", "mCfoo is here"),
            _case("mc-short-lower", "mca today"),
            _case("colon-before-domain", "see: example.com"),
            _case("subphrase-a-dot-b", "see: a.b later"),
            _case("middle-the-kept", "see THE cat"),
            _case("mc-piece-is-all-caps", "keep MCFOO please"),
            _case("unicode-internal-capital", "the niÑO case"),
            _case("digit-after-dot", "see a.1 today"),
            _case("figure-dash-subphrase", "Word \u2012 a Trick"),
            _case("horizontal-bar-subphrase", "Word \u2015 a Trick"),
            _case("of-two-trailing-puncts", "Nothing to be afraid of?!"),
            _case("single-vs-dot", "vs."),
            _case("lower-q-and-a", "q&a session"),
            _case(
                "wordlist-last-wins",
                "SENDING PPPOE",
                callback={"kind": "wordlist", "lines": ["PPPoE", "PpPoE"]},
            ),
            _case(
                "wordlist-missing-file",
                "SENDING PPPOE",
                callback={
                    "kind": "wordlist_missing",
                    "path": "/no/such/titlecase-wordlist.txt",
                },
            ),
            _case(
                "callback-empty-is-unhandled",
                "a thing",
                callback={"kind": "always_empty"},
            ),
            _case(
                "callback-keeps-first-small-word",
                "a thing",
                callback={"kind": "exact", "match": "a", "value": "a"},
            ),
            _case(
                "callback-then-subphrase",
                ": a",
                callback={"kind": "exact", "match": "a", "value": "a"},
            ),
            _case(
                "recursive-all-caps-flag",
                "keep MCFOO please",
                callback={"kind": "echo_all_caps"},
            ),
            _case(
                "slash-recomputes-all-caps",
                "see http/FOO now",
                callback={"kind": "echo_all_caps"},
            ),
            _case("hyphen-without-end-caps", "a-b", small_first_last=False),
            _case("apostrophe-d", "d'artagnan rode"),
            _case("only-newlines", "\n\n"),
            _case("only-newlines-preserve", "\n\n", preserve_blank_lines=True),
            _case("trailing-spaces", "a  "),
            _case("empty-slash-piece", "a/"),
            _case("em-dash-inside-token", "end—to—end"),
            _case("first-word-andromeda", "andromeda rises"),
            _case("vs-at-end", "battle vs."),
            _case("small-first-last-off", "the end", small_first_last=False),
            _case(
                "nbsp-kept",
                "text\u00a0with\u00a0nonbreaking\u00a0spaces",
            ),
            _case(
                "nbsp-normalised",
                "text\u00a0with\u00a0nonbreaking\u00a0spaces",
                normalise_space_characters=True,
            ),
            _case(
                "callback-upper-all",
                "crème brûlée",
                callback={"kind": "upper_all"},
            ),
            _case("form-feed-separator", "text\fwith\ffeed"),
            _case("line-separator-not-a-break", "text\u2028with"),
        ]
    )
    return cases


def make_callback(spec, create_wordlist_filter_from_file):
    if not spec:
        return None, None
    kind = spec["kind"]
    if kind == "upper_if":
        words = {word.upper() for word in spec["words"]}

        def upper_if(word, all_caps=False):
            if word.upper() in words:
                return word.upper()
            return None

        return upper_if, None
    if kind == "upper_all":
        return lambda word, all_caps=False: word.upper(), None
    if kind == "always_empty":
        return lambda word, all_caps=False: "", None
    if kind == "exact":
        match = spec["match"]
        value = spec["value"]

        def exact(word, all_caps=False, match=match, value=value):
            if word == match:
                return value
            return None

        return exact, None
    if kind == "echo_all_caps":

        def echo(word, all_caps=False):
            if all_caps:
                return "ALL"
            return None

        return echo, None
    if kind == "wordlist":
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8", newline="\n"
        )
        for line in spec["lines"]:
            handle.write(line + "\n")
        handle.close()
        return create_wordlist_filter_from_file(handle.name), handle.name
    if kind == "wordlist_missing":
        return create_wordlist_filter_from_file(spec["path"]), None
    raise ValueError(f"unknown callback kind {kind!r}")


def run_case(case, titlecase, create_wordlist_filter_from_file):
    if case["use_default"]:
        return titlecase(case["text"])
    callback, cleanup = make_callback(
        case["callback"], create_wordlist_filter_from_file
    )
    try:
        return titlecase(
            case["text"],
            callback=callback,
            small_first_last=case["small_first_last"],
            preserve_blank_lines=case["preserve_blank_lines"],
            normalise_space_characters=case["normalise_space_characters"],
        )
    finally:
        if cleanup:
            os.remove(cleanup)


def attach_expected(cases, titlecase, create_wordlist_filter_from_file):
    filled = []
    for case in cases:
        item = dict(case)
        item["expected"] = run_case(item, titlecase, create_wordlist_filter_from_file)
        filled.append(item)
    return filled


def dump(path, cases):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cases": cases}
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_datasets():
    titlecase, create_wordlist, test_data = load_oracle()
    visible = attach_expected(visible_inputs(), titlecase, create_wordlist)
    hidden = attach_expected(hidden_inputs(test_data), titlecase, create_wordlist)
    visible_ids = {case["id"] for case in visible}
    hidden_ids = {case["id"] for case in hidden}
    overlap = visible_ids & hidden_ids
    if overlap:
        raise SystemExit(f"duplicate ids: {sorted(overlap)}")
    for path in VISIBLE_PATHS:
        dump(path, visible)
    dump(HIDDEN_PATH, hidden)
    print(f"visible {len(visible)}")
    print(f"hidden {len(hidden)}")
    print(f"total {len(visible) + len(hidden)}")


def check_datasets():
    titlecase, create_wordlist, _test_data = load_oracle()
    visible = json.loads(VISIBLE_PATHS[0].read_text(encoding="utf-8"))["cases"]
    hidden = json.loads(HIDDEN_PATH.read_text(encoding="utf-8"))["cases"]
    other_visible = json.loads(VISIBLE_PATHS[1].read_text(encoding="utf-8"))["cases"]
    if visible != other_visible:
        raise SystemExit("environment/visible_cases.json drifted from tests/data/visible.json")
    failures = []
    for case in visible + hidden:
        actual = run_case(case, titlecase, create_wordlist)
        if actual != case["expected"]:
            failures.append(case["id"])
    if failures:
        raise SystemExit("oracle mismatch: " + ", ".join(failures))
    print(f"ok visible={len(visible)} hidden={len(hidden)} total={len(visible) + len(hidden)}")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_datasets()
    else:
        check_datasets()


if __name__ == "__main__":
    main()
