import importlib.util
import random
import sys
from pathlib import Path


def word_token(number):
    letters = []
    for _ in range(4):
        number, remainder = divmod(number, 26)
        letters.append(chr(ord("a") + remainder))
    return "".join(reversed(letters))


def consonant_token(number):
    alphabet = "bcdfg"
    letters = []
    for _ in range(5):
        number, remainder = divmod(number, len(alphabet))
        letters.append(alphabet[remainder])
    return "".join(reversed(letters))


def write_lines(path, lines):
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(lines))
        output.write("\n")


def main():
    random.seed(1)
    if importlib.util.find_spec("regex") is not None:
        raise RuntimeError("The optional regex package must not be installed.")

    task_root = Path(__file__).resolve().parents[1]
    original_repo = task_root / "environment" / "python-titlecase"
    sys.path.insert(0, str(original_repo))
    from titlecase import titlecase
    import titlecase as titlecase_module

    print(f"titlecase regex module: {titlecase_module.regex.__name__}")

    visible = [
        f"{random.choice(['quiet', 'amber', 'gentle', 'silver', 'little'])} "
        f"{word_token(index)} past the "
        f"{random.choice(['harbor', 'garden', 'river', 'mountain', 'window'])}"
        for index in range(2000)
    ]

    hidden = [
        "the lord of the rings",
        "a tale of two cities",
        "war and peace: a new beginning",
        "mcdonald and mcdowell",
        "dr smith and mr jones",
        "iPhone and eBay",
        "o'neill and l'amour",
        "J. R. R. TOLKIEN",
        "rock/roll and state-of-the-art",
        "NASA AND FBI",
        "rhythm myths",
        "...hello, WORLD",
        "url https://example.com/a-b",
        "contact qa-42@example.com about NASA",
        "a small word at the start",
        "a small word at the end",
        "café déjà vu",
        "words with digits 42 and 007",
        "",
    ]

    hard_case_templates = [
        lambda token, upper, number: f"a {token} story of old cities",
        lambda token, upper, number: f"{token} tale of the",
        lambda token, upper, number: f"{token} and peace: a new beginning",
        lambda token, upper, number: f"mc{token} and mcdowell",
        lambda token, upper, number: f"dr {token} and mr jones",
        lambda token, upper, number: f"iPhone and eBay {token}",
        lambda token, upper, number: f"o'neill and l'{token}",
        lambda token, upper, number: f"J. R. R. {upper}",
        lambda token, upper, number: f"rock/{token}",
        lambda token, upper, number: f"state-{token}-of-the-art",
        lambda token, upper, number: f"NASA AND {upper}",
        lambda token, upper, number: f"the {consonant_token(number)}",
        lambda token, upper, number: f"...{token}, the world",
        lambda token, upper, number: (
            f"visit https://example.com/{token} and email qa-{number}@example.com"
        ),
    ]
    for index in range(1981):
        token = word_token(index)
        category = index % len(hard_case_templates)
        hidden.append(
            hard_case_templates[category](token, token.upper(), index // len(hard_case_templates))
        )

    hidden = list(dict.fromkeys(hidden))
    hidden = [line for line in hidden if line]
    hidden.append("")
    random.shuffle(hidden)
    hidden = [line for line in hidden if line]
    hidden.insert(len(hidden) // 2, "")

    if len(visible) != 2000 or len(hidden) != 2000:
        raise RuntimeError(
            f"Expected 2000 lines in each input set; got {len(visible)} visible "
            f"and {len(hidden)} hidden."
        )
    if len(set(visible)) != len(visible) or len(set(hidden)) != len(hidden):
        raise RuntimeError("Input lines must be unique within each set.")
    if set(visible).intersection(hidden):
        raise RuntimeError("Visible and hidden input sets must not overlap.")
    if any("\n" in line or "\r" in line for line in visible + hidden):
        raise RuntimeError("An input line contains a newline.")

    data_dir = task_root / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    write_lines(data_dir / "inputs.txt", visible)
    write_lines(data_dir / "expected.txt", [titlecase(line) for line in visible])
    write_lines(data_dir / "hidden_inputs.txt", hidden)
    write_lines(data_dir / "hidden_expected.txt", [titlecase(line) for line in hidden])

    print(f"visible inputs: {len(visible)}")
    print(f"hidden inputs: {len(hidden)}")
    print(f"hidden hard cases: {len(hidden) - 1} non-empty lines")


if __name__ == "__main__":
    main()
