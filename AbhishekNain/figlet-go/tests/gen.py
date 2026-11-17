#!/usr/bin/env python3
"""
Test dataset generator for figlet-go verification.
Generates visible and hidden test datasets using the pinned pyfiglet reference checkout.
"""

import collections
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

# Paths resolved relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REFERENCE_DIR = (REPO_ROOT.parent / "pyfiglet").resolve()
DATA_DIR = SCRIPT_DIR / "data"
VISIBLE_FILE = DATA_DIR / "visible.jsonl"
HIDDEN_FILE = DATA_DIR / "hidden.jsonl"

EXPECTED_GIT_SHA = "255827efbc09d662875dad50fa0edc1e1263bf45"
GIT_FALLBACK_PATH = r"C:\Program Files\Git\cmd\git.exe"

REQUIRED_FONTS = [
    "standard", "slant", "small", "big",
    "mini", "banner", "shadow", "script"
]
WIDTHS = [10, 20, 40, 60, 80, 120]
JUSTIFICATIONS = ["auto", "left", "center", "right"]
DIRECTIONS = ["auto", "left-to-right", "right-to-left"]

TARGET_VISIBLE_COUNT = 2000
TARGET_HIDDEN_COUNT = 2000
MAX_ATTEMPTS = 15000
SUBPROCESS_TIMEOUT_SEC = 10.0


def find_git_executable() -> str:
    """Finds git executable via shutil.which or known Windows fallback."""
    git_path = shutil.which("git")
    if git_path and os.path.isfile(git_path):
        return git_path
    if os.path.isfile(GIT_FALLBACK_PATH):
        return GIT_FALLBACK_PATH
    raise FileNotFoundError(
        f"Git executable not found in PATH or at fallback location: {GIT_FALLBACK_PATH}"
    )


def verify_reference():
    """Validates the reference directory, git commit, pyfiglet package, and font files."""
    if not REFERENCE_DIR.is_dir():
        raise RuntimeError(f"Reference directory does not exist: {REFERENCE_DIR}")

    pkg_dir = REFERENCE_DIR / "pyfiglet"
    pkg_init = pkg_dir / "__init__.py"
    if not pkg_init.is_file():
        raise RuntimeError(f"pyfiglet package not found at: {pkg_init}")

    fonts_dir = pkg_dir / "fonts"
    if not fonts_dir.is_dir():
        raise RuntimeError(f"Reference fonts directory missing: {fonts_dir}")

    for font_name in REQUIRED_FONTS:
        flf_file = fonts_dir / f"{font_name}.flf"
        if not flf_file.is_file():
            raise RuntimeError(f"Required font file missing: {flf_file}")

    git_bin = find_git_executable()
    res = subprocess.run(
        [git_bin, "-C", str(REFERENCE_DIR), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"Failed to check git HEAD in {REFERENCE_DIR}: {res.stderr.strip()}"
        )
    current_sha = res.stdout.strip()
    if current_sha != EXPECTED_GIT_SHA:
        raise RuntimeError(
            f"Reference git HEAD mismatch: expected {EXPECTED_GIT_SHA}, got {current_sha}"
        )

    # Verify import from sibling checkout, not an installed package
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    import_cmd = [
        sys.executable,
        "-c",
        "import pyfiglet; print(pyfiglet.__file__)",
    ]
    proc = subprocess.run(
        import_cmd,
        cwd=str(REFERENCE_DIR),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to import pyfiglet from reference checkout: {proc.stderr.strip()}"
        )
    imported_file = Path(proc.stdout.strip()).resolve()
    expected_file = pkg_init.resolve()
    if imported_file != expected_file:
        raise RuntimeError(
            f"pyfiglet imported from {imported_file}, expected {expected_file}"
        )


# Text sample pools for generating rich candidate text
SAMPLE_WORDS = [
    "hello", "world", "figlet", "go", "test", "Antigravity", "code", "ASCII",
    "art", "matrix", "cyber", "terminal", "123", "2026", "OK", "A", "Z",
    "build", "run", "fast", "linux", "unix", "shell", "exec", "output"
]

SAMPLE_SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "FIGlet renders ASCII art text from ordinary screen characters.",
    "Pack my box with five dozen liquor jugs.",
    "Simple is better than complex.",
    "Special cases aren't special enough to break the rules.",
    "Although practicality beats purity.",
    "Now is better than never.",
    "Hello World from Go command-line tool."
]

SAMPLE_SMUSH_PUNCTUATION = [
    "| / \\ _ [ ] { } ( ) < >",
    "[hello] (world) {test} <abc>",
    "_/_ _|_ _\\_ _<_ _>_",
    "|| // \\\\ [[ ]] {{ }} (( )) << >>",
    "|/ /| |[ [| |( (| |< <|",
    "/[ [/ /{ {/ /( (/ /< </",
    "[{ {[ [( ([ [< [<",
    "{< <{ (< <(",
    "[] ][ {} }{ () )(",
    "/\\ \\/ >< <>",
    "> <",
    "< >",
    "/\\",
    "\\/",
    "><",
    "[_]",
    "{_}",
    "(_)",
    "<_>",
    "|_|",
    "/_/",
    "\\_\\"
]

SAMPLE_SPACES = [
    "hello  world",
    "double  space",
    "   leading space",
    "trailing space   ",
    "multiple   spaces   between   words",
    "a b c  d  e   f",
    " ",
    "   "
]

SAMPLE_NEWLINES = [
    "hello\nworld",
    "line 1\nline 2\nline 3",
    "first\n\nsecond",
    "\nleading newline",
    "trailing newline\n",
    "a\nb\nc",
    "top\nbottom"
]

SAMPLE_LATIN1 = [
    "café",
    "naïve",
    "façade",
    "über",
    "groß",
    "Straße",
    "año",
    "piñata",
    "résumé",
    "Ä Ö Ü ä ö ü ß",
    "é ß ñ",
    "Voilà! Déjà vu"
]

SAMPLE_UNSUPPORTED = [
    "hello 🚀 world",
    "test 123 中文",
    "art ★ design",
    "emoji 😊 test",
    "arrow → check ✓",
    "math ∑ ∫ dx"
]

SAMPLE_DASH_TEXT = [
    "-word",
    "-hello",
    "--not-a-flag",
    "-123",
    "-f",
    "-w",
    "--test"
]


def generate_positional_arguments(rng: random.Random) -> list[str]:
    """Generates 1 to 4 positional text arguments mixing words and edge cases."""
    category = rng.choices(
        [
            "words", "sentence", "smush", "spaces",
            "newlines", "latin1", "unsupported", "dash"
        ],
        weights=[0.25, 0.15, 0.20, 0.10, 0.10, 0.10, 0.05, 0.05]
    )[0]

    if category == "words":
        count = rng.choices([1, 2, 3, 4], weights=[0.60, 0.25, 0.10, 0.05])[0]
        return [rng.choice(SAMPLE_WORDS) for _ in range(count)]
    elif category == "sentence":
        return [rng.choice(SAMPLE_SENTENCES)]
    elif category == "smush":
        return [rng.choice(SAMPLE_SMUSH_PUNCTUATION)]
    elif category == "spaces":
        return [rng.choice(SAMPLE_SPACES)]
    elif category == "newlines":
        return [rng.choice(SAMPLE_NEWLINES)]
    elif category == "latin1":
        return [rng.choice(SAMPLE_LATIN1)]
    elif category == "unsupported":
        return [rng.choice(SAMPLE_UNSUPPORTED)]
    elif category == "dash":
        return [rng.choice(SAMPLE_DASH_TEXT)]
    return [rng.choice(SAMPLE_WORDS)]


def sample_candidate_args(rng: random.Random) -> list[str]:
    """Builds a candidate CLI argument list."""
    # Special focus: meaningful coverage of narrow widths with right-to-left
    is_narrow_rtl = rng.random() < 0.20
    # Special focus: explicit direction and justification combinations
    is_explicit_comb = rng.random() < 0.20

    if is_narrow_rtl:
        width = rng.choice([10, 20])
        direction = "right-to-left"
        justify = rng.choice(JUSTIFICATIONS)
    elif is_explicit_comb:
        width = rng.choice(WIDTHS)
        direction = rng.choice(["left-to-right", "right-to-left"])
        justify = rng.choice(["left", "center", "right"])
    else:
        width = rng.choice(WIDTHS) if rng.random() < 0.85 else None
        direction = rng.choice(DIRECTIONS) if rng.random() < 0.85 else None
        justify = rng.choice(JUSTIFICATIONS) if rng.random() < 0.85 else None

    font = rng.choice(REQUIRED_FONTS) if rng.random() < 0.85 else None

    # Flags selected independently with probability 1/4
    flags = []
    for flg in ["-r", "-F", "-s", "-n"]:
        if rng.random() < 0.25:
            flags.append(flg)

    positional = generate_positional_arguments(rng)

    args = []
    if font is not None:
        args.extend(["-f", font])
    if width is not None:
        args.extend(["-w", str(width)])
    if justify is not None:
        args.extend(["-j", justify])
    if direction is not None:
        args.extend(["-D", direction])
    args.extend(flags)

    # Use -- before positional text where needed (e.g. positional arg starts with -)
    if any(p.startswith("-") for p in positional):
        args.append("--")

    args.extend(positional)
    return args


def parse_leading_options(args: list[str]) -> dict:
    """
    Parses only the leading generated options from args:
    - Consumes -f, -w, -j, -D with their values.
    - Recognizes -r, -F, -s, -n as flags.
    - Stops at -- or the first positional argument.
    - Never inspects subsequent positional text as options.
    - Applies defaults when options are omitted.
    """
    opts = {
        "font": "standard",
        "width": 80,
        "justify": "auto",
        "direction": "auto",
        "flags": set(),
    }
    val_options = {"-f": "font", "-w": "width", "-j": "justify", "-D": "direction"}
    flag_options = {"-r", "-F", "-s", "-n"}

    i = 0
    n = len(args)
    while i < n:
        arg = args[i]
        if arg == "--":
            # Explicit option terminator; positional args follow
            break
        elif arg in val_options:
            field = val_options[arg]
            if i + 1 < n:
                val = args[i + 1]
                if field == "width":
                    opts["width"] = int(val)
                else:
                    opts[field] = val
                i += 2
            else:
                break
        elif arg in flag_options:
            opts["flags"].add(arg)
            i += 1
        else:
            # First positional argument encountered; stop option parsing
            break

    return opts


def compute_dataset_coverage(records: list[dict]) -> dict:
    """Computes coverage statistics for a dataset using parse_leading_options."""
    stats = {
        "count": len(records),
        "fonts": collections.Counter(),
        "widths": collections.Counter(),
        "directions": collections.Counter(),
        "justifications": collections.Counter(),
        "flags": collections.Counter(),
        "sn_combo": 0,
        "narrow_rtl": 0,
    }
    for rec in records:
        opts = parse_leading_options(rec["args"])
        stats["fonts"][opts["font"]] += 1
        stats["widths"][opts["width"]] += 1
        stats["directions"][opts["direction"]] += 1
        stats["justifications"][opts["justify"]] += 1
        for flg in sorted(opts["flags"]):
            stats["flags"][flg] += 1
        if "-s" in opts["flags"] and "-n" in opts["flags"]:
            stats["sn_combo"] += 1
        if opts["width"] in [10, 20] and opts["direction"] == "right-to-left":
            stats["narrow_rtl"] += 1
    return stats


def run_reference_cli(args: list[str]) -> tuple[bool, str, str]:
    """
    Executes the pinned pyfiglet reference CLI.
    Captures stdout and stderr as raw bytes, decoding stdout without trimming.
    """
    cmd = [sys.executable, "-m", "pyfiglet", *args]
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REFERENCE_DIR),
            capture_output=True,
            timeout=SUBPROCESS_TIMEOUT_SEC,
            env=env,
        )
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            return False, "", f"Non-zero exit code ({proc.returncode}): {err}"
        stdout_str = proc.stdout.decode("utf-8")
        return True, stdout_str, "OK"
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {SUBPROCESS_TIMEOUT_SEC}s"
    except Exception as e:
        return False, "", f"Execution error: {e}"


def write_jsonl_file(file_path: Path, records: list[dict]):
    """Writes records deterministically as UTF-8 JSONL with LF endings and no BOM."""
    temp_path = file_path.with_suffix(".tmp")
    with open(temp_path, "wb") as f:
        for record in records:
            line_bytes = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
            f.write(line_bytes)
    temp_path.replace(file_path)


def print_coverage_block(title: str, stats: dict):
    """Prints coverage details for a single dataset."""
    print(f"\n--- {title} (Total: {stats['count']}) ---")
    print("  Fonts:")
    for k, v in sorted(stats["fonts"].items(), key=lambda x: str(x[0])):
        print(f"    {k}: {v}")
    print("  Widths:")
    for k, v in sorted(stats["widths"].items(), key=lambda x: str(x[0])):
        print(f"    {k}: {v}")
    print("  Directions:")
    for k, v in sorted(stats["directions"].items(), key=lambda x: str(x[0])):
        print(f"    {k}: {v}")
    print("  Justifications:")
    for k, v in sorted(stats["justifications"].items(), key=lambda x: str(x[0])):
        print(f"    {k}: {v}")
    print("  Flags:")
    for k, v in sorted(stats["flags"].items(), key=lambda x: str(x[0])):
        print(f"    {k}: {v}")
    print(f"  Combined -s and -n: {stats['sn_combo']}")
    print(f"  Narrow width (10, 20) + Right-to-Left: {stats['narrow_rtl']}")


def print_summary(
    visible_records: list[dict],
    hidden_records: list[dict],
    total_attempts: int,
    rejected_reasons: collections.Counter,
    sample_rejections: list[tuple[list[str], str]]
):
    visible_set = {tuple(r["args"]) for r in visible_records}
    hidden_set = {tuple(r["args"]) for r in hidden_records}
    is_disjoint = visible_set.isdisjoint(hidden_set)
    total_unique = len(visible_set | hidden_set)

    print("\n" + "=" * 60)
    print("               FIGLET TEST GENERATION SUMMARY")
    print("=" * 60)
    print(f"Total attempts: {total_attempts}")
    print(f"Visible records: {len(visible_records)}")
    print(f"Hidden records:  {len(hidden_records)}")
    print(f"Total unique args: {total_unique} / {len(visible_records) + len(hidden_records)}")
    print(f"Global disjointness (visible & hidden): {'PASS' if is_disjoint else 'FAIL'}")

    visible_stats = compute_dataset_coverage(visible_records)
    hidden_stats = compute_dataset_coverage(hidden_records)

    print_coverage_block("Visible Dataset Coverage", visible_stats)
    print_coverage_block("Hidden Dataset Coverage", hidden_stats)

    print("\n--- Rejections ---")
    total_rejected = sum(rejected_reasons.values())
    print(f"  Total rejected candidates: {total_rejected}")
    for reason, count in rejected_reasons.most_common():
        print(f"    [{count}] {reason}")

    if sample_rejections:
        print("\n--- Sample Rejected Candidates ---")
        for idx, (rej_args, reason) in enumerate(sample_rejections, 1):
            print(f"  {idx}. args: {rej_args}")
            print(f"     reason: {reason}")
    print("=" * 60 + "\n")


def generate():
    """Main generation routine: verifies environment and generates test suites."""
    print("Verifying environment and reference checkout...", flush=True)
    verify_reference()
    print("Environment verification passed.", flush=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(7)

    seen_args = set()
    visible_records: list[dict] = []
    hidden_records: list[dict] = []
    rejected_reasons = collections.Counter()
    sample_rejections: list[tuple[list[str], str]] = []

    attempts = 0
    total_rejected = 0

    print("Generating visible dataset...", flush=True)
    while len(visible_records) < TARGET_VISIBLE_COUNT and attempts < MAX_ATTEMPTS:
        attempts += 1
        args = sample_candidate_args(rng)
        args_tuple = tuple(args)
        if args_tuple in seen_args:
            continue

        success, out, reason = run_reference_cli(args)
        if not success:
            total_rejected += 1
            rejected_reasons[reason] += 1
            if "Timeout" in reason:
                print(
                    f"[Timeout] Candidate timed out after {SUBPROCESS_TIMEOUT_SEC}s with args: {args}",
                    flush=True
                )
            if len(sample_rejections) < 5:
                sample_rejections.append((args, reason))
            continue

        seen_args.add(args_tuple)
        visible_records.append({"args": args, "out": out})

        if len(visible_records) % 100 == 0:
            print(
                f"[Progress] Visible: {len(visible_records)}/{TARGET_VISIBLE_COUNT}, "
                f"Hidden: {len(hidden_records)}/{TARGET_HIDDEN_COUNT}, "
                f"Attempts: {attempts}, Rejections: {total_rejected}",
                flush=True
            )

    if len(visible_records) < TARGET_VISIBLE_COUNT:
        raise RuntimeError(
            f"Exceeded max attempts ({MAX_ATTEMPTS}) while generating visible dataset: "
            f"got {len(visible_records)} / {TARGET_VISIBLE_COUNT}"
        )

    print("Generating hidden dataset...", flush=True)
    while len(hidden_records) < TARGET_HIDDEN_COUNT and attempts < MAX_ATTEMPTS:
        attempts += 1
        args = sample_candidate_args(rng)
        args_tuple = tuple(args)
        if args_tuple in seen_args:
            continue

        success, out, reason = run_reference_cli(args)
        if not success:
            total_rejected += 1
            rejected_reasons[reason] += 1
            if "Timeout" in reason:
                print(
                    f"[Timeout] Candidate timed out after {SUBPROCESS_TIMEOUT_SEC}s with args: {args}",
                    flush=True
                )
            if len(sample_rejections) < 5:
                sample_rejections.append((args, reason))
            continue

        seen_args.add(args_tuple)
        hidden_records.append({"args": args, "out": out})

        if len(hidden_records) % 100 == 0:
            print(
                f"[Progress] Visible: {len(visible_records)}/{TARGET_VISIBLE_COUNT}, "
                f"Hidden: {len(hidden_records)}/{TARGET_HIDDEN_COUNT}, "
                f"Attempts: {attempts}, Rejections: {total_rejected}",
                flush=True
            )

    if len(hidden_records) < TARGET_HIDDEN_COUNT:
        raise RuntimeError(
            f"Exceeded max attempts ({MAX_ATTEMPTS}) while generating hidden dataset: "
            f"got {len(hidden_records)} / {TARGET_HIDDEN_COUNT}"
        )

    print("Writing visible dataset...", flush=True)
    write_jsonl_file(VISIBLE_FILE, visible_records)
    print("Writing hidden dataset...", flush=True)
    write_jsonl_file(HIDDEN_FILE, hidden_records)

    print_summary(
        visible_records,
        hidden_records,
        attempts,
        rejected_reasons,
        sample_rejections
    )


if __name__ == "__main__":
    generate()
