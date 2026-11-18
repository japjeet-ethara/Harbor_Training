import hashlib
import json
import subprocess
import sys

from reference import ROOT, lf_records, record_bytes, titlecase


def check_dataset(executable):
    sets = {}
    for split, prefix in (("visible", ""), ("hidden", "hidden_")):
        directory = ROOT / "tests/data"
        source = (directory / (prefix + "inputs.txt")).read_bytes()
        frozen = (directory / (prefix + "expected.txt")).read_bytes()
        inputs, answers = lf_records(source), lf_records(frozen)
        assert len(inputs) == len(answers) == 2000
        assert len(set(inputs)) == 2000
        expected = record_bytes(titlecase(item.decode("utf-8")) for item in inputs)
        assert expected == frozen, f"Frozen {split} answers differ from upstream"
        if executable:
            observed = subprocess.run([executable], input=source, capture_output=True,
                                      timeout=60, check=True).stdout
            assert observed == frozen, f"Go differs on the {split} split"
        sets[split] = (set(inputs), set(answers))
        print(f"{split}: 2000/2000 frozen answers match; sha256={hashlib.sha256(frozen).hexdigest()}")
    inputs, outputs = (len(left & right) for left, right in zip(sets["visible"], sets["hidden"]))
    assert inputs == 0 and outputs == 0
    print(f"cross-split input overlap={inputs}; expected-output overlap={outputs}")


EXAMPLES = (
    ("small words and title edges", "the chronicle of the coast and"),
    ("punctuated title edges", '"of tides and time to?'),
    ("uppercase initials", "J.A. AND Ν.Κ."),
    ("apostrophe and uppercase expansion", "mrs d'ßelle and o'brien's"),
    ("nested Mc and compounds", "mcand/of-to and mcand"),
    ("honorifics", "DR MR MRS MS"),
    ("inline periods and internal caps", "é.à and DeVries and a.b"),
    ("slash precedence and repeated slashes", "at/and-of folio//proof in--between"),
    ("consonants and normal capitalization", "brr and cwm with echo"),
    ("all-caps contextual lowercase", "ΛΟΓΟΣ· ΟΔΥΣΣΕΎΣ ΛΟΓΟΣ\u0301"),
    ("subphrase even inside a word", "manuscripts: inland and all"),
    ("whitespace retained", "  the\tfolio\u00a0and\u2028the  "),
    ("full Unicode uppercase mappings", "ﬃ ligatures, ß letters and ǳ"),
    ("regex Unicode word boundary", "in\u200d and of\u0301"),
    ("compatibility letters follow regex simple folding", "atlas ın and İN v."),
)


def check_examples(executable):
    titles = [source for _, source in EXAMPLES]
    answers = [titlecase(source) for source in titles]
    if executable:
        actual = subprocess.run([executable], input=record_bytes(titles), capture_output=True,
                                check=True).stdout
        assert actual == record_bytes(answers)
    for (rule, source), answer in zip(EXAMPLES, answers):
        print(json.dumps({"rule": rule, "input": source, "output": answer}, ensure_ascii=True))

    visible = lf_records((ROOT / "tests/data/inputs.txt").read_bytes())
    for index in (0, 399, 799, 1199, 1999):
        title = visible[index].decode("utf-8")
        print(json.dumps({"visible_row": index + 1, "input": title, "output": titlecase(title)},
                         ensure_ascii=True))


if __name__ == "__main__":
    candidate = sys.argv[1] if len(sys.argv) > 1 else None
    check_dataset(candidate)
    check_examples(candidate)
