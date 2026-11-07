"""Run /app/titlecase and compare it with python-titlecase 2.4.1.

Expected bytes were produced by titlecase() and cmd() from that package
with the optional regex module available. These tests do not import it.
"""

import os
import subprocess
from pathlib import Path

import pytest

BINARY = "/app/titlecase"


def run_titlecase(args, *, stdin=None, home):
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [BINARY, *args],
        input=stdin,
        capture_output=True,
        env=env,
        check=False,
    )


def make_home(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    return home


def test_binary_exists_and_is_executable():
    binary = Path(BINARY)
    assert binary.is_file()
    assert os.access(binary, os.X_OK)


def test_positional_arguments(tmp_path):
    result = run_titlecase(
        ["make", "me", "a", "title"],
        home=make_home(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout == b"Make Me a Title"


def test_stdin_preserves_the_input_newline(tmp_path):
    result = run_titlecase(
        [],
        stdin=b"Can pipe and/or whatever else\n",
        home=make_home(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout == b"Can Pipe and/or Whatever Else\n"


def test_stdin_without_a_newline_does_not_add_one(tmp_path):
    result = run_titlecase(
        [],
        stdin=b"a thing",
        home=make_home(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout == b"A Thing"


def test_empty_stdin(tmp_path):
    result = run_titlecase([], stdin=b"", home=make_home(tmp_path))
    assert result.returncode == 0
    assert result.stdout == b""


def test_input_and_output_files(tmp_path):
    home = make_home(tmp_path)
    source = tmp_path / "input.txt"
    destination = tmp_path / "output.txt"
    source.write_bytes(b"this is a test\n")

    result = run_titlecase(
        ["-f", str(source), "-o", str(destination)],
        home=home,
    )

    assert result.returncode == 0
    assert result.stdout == b""
    assert destination.read_bytes() == b"This Is a Test\n"


def test_long_input_and_output_options(tmp_path):
    home = make_home(tmp_path)
    source = tmp_path / "input.txt"
    destination = tmp_path / "output.txt"
    source.write_bytes("El Niño".encode())

    result = run_titlecase(
        ["--input-file", str(source), "--output-file", str(destination)],
        home=home,
    )

    assert result.returncode == 0
    assert result.stdout == b""
    assert destination.read_bytes() == "El Niño".encode()


def test_dash_reads_stdin_and_writes_stdout(tmp_path):
    result = run_titlecase(
        ["-f", "-", "-o", "-"],
        stdin=b"this is a TEST",
        home=make_home(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout == b"This Is a TEST"


def test_positional_text_cannot_be_combined_with_input_file(tmp_path):
    home = make_home(tmp_path)
    source = tmp_path / "input.txt"
    destination = tmp_path / "output.txt"
    source.write_bytes(b"this is a test")

    result = run_titlecase(
        ["-f", str(source), "-o", str(destination), "extra"],
        home=home,
    )

    assert result.returncode != 0
    assert result.stdout == b""
    assert not destination.exists()


def test_abbreviated_preserve_option_is_rejected(tmp_path):
    result = run_titlecase(
        ["--preserve"],
        stdin=b"Line one\n\nLine two\n",
        home=make_home(tmp_path),
    )
    assert result.returncode != 0
    assert result.stdout == b""


def test_unknown_option_is_rejected(tmp_path):
    result = run_titlecase(
        ["--not-an-option"],
        stdin=b"a thing",
        home=make_home(tmp_path),
    )
    assert result.returncode != 0
    assert result.stdout == b""


def test_explicit_wordlist(tmp_path):
    home = make_home(tmp_path)
    wordlist = tmp_path / "acronyms.txt"
    wordlist.write_bytes(b"TCP\nUDP\nPPPoE\n")

    mixed = run_titlecase(
        ["-w", str(wordlist)],
        stdin=b"a simple tcp and udp wrapper",
        home=home,
    )
    shouting = run_titlecase(
        ["-w", str(wordlist)],
        stdin=b"SENDING UDP PACKETS OVER PPPOE WORKS GREAT",
        home=home,
    )

    assert mixed.returncode == 0
    assert mixed.stdout == b"A Simple TCP and UDP Wrapper"
    assert shouting.returncode == 0
    assert shouting.stdout == b"Sending UDP Packets Over PPPoE Works Great"


def test_wordlist_ignores_blank_lines_and_surrounding_space(tmp_path):
    home = make_home(tmp_path)
    wordlist = tmp_path / "acronyms.txt"
    wordlist.write_bytes(b"\n  TCP  \n\n")

    result = run_titlecase(
        ["-w", str(wordlist)],
        stdin=b"tcp rocks",
        home=home,
    )

    assert result.returncode == 0
    assert result.stdout == b"TCP Rocks"


def test_later_wordlist_entry_wins(tmp_path):
    home = make_home(tmp_path)
    wordlist = tmp_path / "acronyms.txt"
    wordlist.write_bytes(b"Udp\nUDP\n")

    result = run_titlecase(
        ["-w", str(wordlist)],
        stdin=b"udp packets",
        home=home,
    )

    assert result.returncode == 0
    assert result.stdout == b"UDP Packets"


def test_wordlist_matches_the_whole_token(tmp_path):
    home = make_home(tmp_path)
    wordlist = tmp_path / "acronyms.txt"
    wordlist.write_bytes(b"TCP\n")

    result = run_titlecase(
        ["-w", str(wordlist)],
        stdin=b"see tcp, today",
        home=home,
    )

    assert result.returncode == 0
    assert result.stdout == b"See Tcp, Today"


def test_wordlist_result_stays_immutable_at_line_edge(tmp_path):
    home = make_home(tmp_path)
    wordlist = tmp_path / "acronyms.txt"
    wordlist.write_bytes(b"a\n")

    result = run_titlecase(
        ["-w", str(wordlist)],
        stdin=b"a thing",
        home=home,
    )

    assert result.returncode == 0
    assert result.stdout == b"a Thing"


def test_default_wordlist_in_home(tmp_path):
    home = make_home(tmp_path)
    (home / ".titlecase.txt").write_bytes(b"UDP\n")

    result = run_titlecase(
        [],
        stdin=b"a simple tcp and udp wrapper",
        home=home,
    )

    assert result.returncode == 0
    assert result.stdout == b"A Simple TCP and UDP Wrapper"


def test_explicit_wordlist_is_used_instead_of_home_file(tmp_path):
    home = make_home(tmp_path)
    (home / ".titlecase.txt").write_bytes(b"udp\n")
    wordlist = tmp_path / "acronyms.txt"
    wordlist.write_bytes(b"UDP\n")

    result = run_titlecase(
        ["-w", str(wordlist)],
        stdin=b"udp",
        home=home,
    )

    assert result.returncode == 0
    assert result.stdout == b"UDP"


def test_missing_wordlist_file_is_not_an_error(tmp_path):
    missing = tmp_path / "missing.txt"

    result = run_titlecase(
        ["-w", str(missing)],
        stdin=b"a simple tcp and udp wrapper",
        home=make_home(tmp_path),
    )

    assert result.returncode == 0
    assert result.stdout == b"A Simple TCP and Udp Wrapper"


def test_blank_lines_are_collapsed_by_default(tmp_path):
    result = run_titlecase(
        [],
        stdin=b"Line number one\n\nand Line three\n",
        home=make_home(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout == b"Line Number One\nAnd Line Three\n"


def test_preserve_blank_lines(tmp_path):
    result = run_titlecase(
        ["--preserve-blank-lines"],
        stdin=b"Line number one\n\nand Line three\n",
        home=make_home(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout == b"Line Number One\n\nAnd Line Three\n"


def test_preserve_blank_lines_keeps_a_complex_run(tmp_path):
    source = b"\n\nLeading blank\n\n\nMulti-blank\n\n\n\n\nTrailing Blank\n\n"
    expected = b"\n\nLeading Blank\n\n\nMulti-Blank\n\n\n\n\nTrailing Blank\n\n"

    result = run_titlecase(
        ["--preserve-blank-lines"],
        stdin=source,
        home=make_home(tmp_path),
    )

    assert result.returncode == 0
    assert result.stdout == expected


def test_carriage_return_newlines_with_and_without_preserve(tmp_path):
    home = make_home(tmp_path)
    source = b"Line one\r\n\r\nLine two"

    collapsed = run_titlecase([], stdin=source, home=home)
    preserved = run_titlecase(
        ["--preserve-blank-lines"],
        stdin=source,
        home=home,
    )

    assert collapsed.returncode == 0
    assert collapsed.stdout == b"Line One\nLine Two"
    assert preserved.returncode == 0
    assert preserved.stdout == b"Line One\n\n\n\nLine Two"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("text\twith\ttabs", "Text\tWith\tTabs"),
        ("text\u00a0with\u00a0nonbreaking\u00a0spaces", "Text\u00a0With\u00a0Nonbreaking\u00a0Spaces"),
        ("a  thing", "A  Thing"),
        (" a thing", " a Thing"),
    ],
)
def test_whitespace_is_preserved(text, expected, tmp_path):
    result = run_titlecase(
        [],
        stdin=text.encode(),
        home=make_home(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout == expected.encode()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("this is a test", "This Is a Test"),
        ("THIS IS A TEST", "This Is a Test"),
        ("this is a TEST", "This Is a TEST"),
        ("the cat sat on a mat", "The Cat Sat on a Mat"),
        ("this v that", "This v That"),
        ("this v. that", "This v. That"),
        ("this vs that", "This vs That"),
        ("this vs. that", "This vs. That"),
        ("this is THE test", "This Is THE Test"),
        ("hello, the world", "Hello, the World"),
        ("Mr. and Mrs. Person", "Mr. And Mrs. Person"),
        (
            "Starting Sub-Phrase With a Small Word: a Trick, Perhaps?",
            "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?",
        ),
        (
            "Snakes on a Plane - The TV Edit - The Famous Line",
            "Snakes on a Plane - The TV Edit - The Famous Line",
        ),
        ("EPISODE 7 — THE FORCE AWAKENS", "Episode 7 — The Force Awakens"),
        ("my name is o'reilly", "My Name Is O'Reilly"),
        ("l'grange", "l'Grange"),
        ("l'GranGe", "l'GranGe"),
        ("o'grange's", "O'Grange's"),
        ("l’grange", "L’grange"),
        ("mctavish", "McTavish"),
        ("MCFOO-BAR", "McFoo-Bar"),
        ("mc", "Mc"),
        ("macdonalds", "Macdonalds"),
        ("Mr mr Mrs Ms Mss Dr dr", "Mr Mr Mrs Ms MSS Dr Dr"),
        ("this is just an example.com", "This Is Just an example.com"),
        ("this is http://foo.com", "This Is http://foo.com"),
        ("http://localhost", "Http://localhost"),
        ("iTunes should be unmolested", "iTunes Should Be Unmolested"),
        (
            "WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM",
            "Washington, D.C. Should Be Fixed but Might Be a Problem",
        ),
        ("word/word", "Word/Word"),
        ("a title and/or string", "A Title and/or String"),
        ("end-to-end", "End-to-End"),
        ("a-b", "A-B"),
        (
            "a-b end-to-end two-not-three/three-by-four/five-and",
            "A-B End-to-End Two-Not-Three/Three-by-Four/Five-And",
        ),
        (
            "Words with all consonants like cnn are acronyms",
            "Words With All Consonants Like CNN Are Acronyms",
        ),
        ("a simple tcp and udp wrapper", "A Simple TCP and Udp Wrapper"),
        ("st and cnn", "St and CNN"),
        ("FOO BAR 5TH ST", "Foo Bar 5th St"),
        ("34th 3rd 2nd", "34th 3rd 2nd"),
        ("«word", "«word"),
        (
            "'by the Way, small word at the start but within quotes.'",
            "'By the Way, Small Word at the Start but Within Quotes.'",
        ),
        (
            "Small word at end is nothing to be afraid of",
            "Small Word at End Is Nothing to Be Afraid Of",
        ),
        ('"Nothing to Be Afraid of?"', '"Nothing to Be Afraid Of?"'),
        (
            "Q&A with steve jobs: 'that's what happens in technology'",
            "Q&A With Steve Jobs: 'That's What Happens in Technology'",
        ),
        ("What is AT&T's problem?", "What Is AT&T's Problem?"),
        ("EL NIÑO A ARRIVÉ HIER", "El Niño a Arrivé Hier"),
        ("El Niño", "El Niño"),
        ("ÝÆ ÑØ", "Ýæ Ñø"),
        ("“YOUNG AND RESTLESS”", "“Young and Restless”"),
    ],
)
def test_titlecase_rules(text, expected, tmp_path):
    result = run_titlecase(
        [],
        stdin=text.encode(),
        home=make_home(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout == expected.encode()
