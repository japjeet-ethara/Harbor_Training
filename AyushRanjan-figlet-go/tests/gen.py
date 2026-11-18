#!/usr/bin/env python3
"""Generate deterministic visible and hidden pyfiglet oracle cases."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from itertools import product
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


CASE_COUNT = 2000
WORKERS = 8
CASE_TIMEOUT_SECONDS = 5
PROBE_TIMEOUT_SECONDS = 2

FONTS = ("standard", "slant", "small", "big", "mini", "banner", "shadow", "script")
WIDTHS = (10, 20, 40, 60, 80, 120)
DIRECTIONS = ("auto", "left-to-right", "right-to-left")
JUSTIFICATIONS = ("auto", "left", "center", "right")
FLAG_NAMES = ((1, "-r"), (2, "-F"), (4, "-s"), (8, "-n"))

# Hi deliberately probes a known narrow-width hang and A probes a glyph that
# does not fit in big.flf at width 10. Failures are reported, then only
# successful single-character inputs are placed in the narrow safe pool.
NARROW_PROBE_TEXTS = ("Hi", "A", "i", "0", "1", "!", "?", "x", "/")
FALLBACK_TEXTS = ("i", "0", "1", "!", "?", "x", "/")

TEXTS = (
    "Hello",
    "Harbor Practice",
    "FIGlet in Go",
    "The quick brown fox jumps over the lazy dog",
    "0123456789",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
    "!@#$%^&*()_+-=[]{};':,./<>?\\|`~",
    "[]{}()<>",
    r"/\|_",
    "same same",
    "multiple positional words",
    "  leading and trailing spaces  ",
    "tab\there",
    "line\nbreak",
    "carriage\rreturn",
    "café déjà vu",
    "Ω Ж 漢字",
    "x" * 121,
    "word " * 30,
)
SINGLE_CHAR_TEXTS = tuple(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    "!@#$%^&*()_+-=[]{};':,./<>?\\|`~"
) + ("é", "Ω", "Ж", "漢", "字")
MULTIWORD_TEXTS = ("A B", "Hi Go", "[] {}", "one two", "one two three", "same same", "FIGlet Go")

Config = tuple[str, int, str, str, int]
EVENT_COUNTS: Counter[str] = Counter()


def report_event(event: dict[str, Any]) -> None:
    """Write a machine-readable diagnostic to stderr."""
    EVENT_COUNTS[event["event"]] += 1
    print(json.dumps(event, ensure_ascii=True, sort_keys=True), file=sys.stderr, flush=True)


def normalized_text(data: bytes) -> str:
    return data.decode("utf-8").replace("\r\n", "\n")


def run_oracle(repo: Path, argv: list[str], timeout: float) -> tuple[str, str, int] | subprocess.TimeoutExpired:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pyfiglet", *argv],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as error:
        return error
    return normalized_text(result.stdout), normalized_text(result.stderr), result.returncode


def rendered_success(result: tuple[str, str, int] | subprocess.TimeoutExpired) -> bool:
    return (
        not isinstance(result, subprocess.TimeoutExpired)
        and result[2] == 0
        and result[1] == ""
        and any(char not in " \t\r\n" for char in result[0])
    )


def failure_reason(
    result: tuple[str, str, int] | subprocess.TimeoutExpired, timeout: float
) -> str:
    if isinstance(result, subprocess.TimeoutExpired):
        return f"timeout after {timeout:g}s"
    stdout, stderr, exit_code = result
    if exit_code != 0:
        return f"exit_code={exit_code}, stderr={stderr[:240]!r}"
    if stderr:
        return f"unexpected stderr={stderr[:240]!r}"
    if not any(char not in " \t\r\n" for char in stdout):
        return "CLI exited 0 but rendered no visible glyph"
    return "reference result did not satisfy success checks"


def make_rngs() -> tuple[random.Random, random.Random]:
    # The required seed anchors both independent deterministic streams.
    random.seed(7)
    visible_seed = random.getrandbits(64)
    hidden_seed = visible_seed ^ 0x9E3779B97F4A7C15
    return random.Random(visible_seed), random.Random(hidden_seed)


def core_configs(mask_shift: int) -> list[Config]:
    """Cover every font/width/direction/justification tuple once."""
    configs: list[Config] = []
    for font_index, font in enumerate(FONTS):
        for width_index, width in enumerate(WIDTHS):
            for direction_index, direction in enumerate(DIRECTIONS):
                for justify_index, justification in enumerate(JUSTIFICATIONS):
                    mask = (font_index * 3 + width_index * 5 + direction_index * 4 + justify_index + mask_shift) % 16
                    configs.append((font, width, direction, justification, mask))
    return configs


def build_config_sets(
    visible_rng: random.Random, hidden_rng: random.Random
) -> tuple[list[Config], list[Config]]:
    """Create unique, disjoint sets with complete core and font/flag coverage."""
    all_configs = list(product(FONTS, WIDTHS, DIRECTIONS, JUSTIFICATIONS, range(16)))
    visible_core = core_configs(0)
    hidden_core = core_configs(8)
    visible_core_set = set(visible_core)
    hidden_core_set = set(hidden_core)
    if visible_core_set & hidden_core_set:
        raise RuntimeError("visible and hidden core configurations overlap")

    available_for_visible = [
        config for config in all_configs if config not in visible_core_set | hidden_core_set
    ]
    visible_rng.shuffle(available_for_visible)
    visible_extra = available_for_visible[: CASE_COUNT - len(visible_core)]
    visible_set = visible_core_set | set(visible_extra)

    available_for_hidden = [
        config
        for config in all_configs
        if config not in visible_set and config not in hidden_core_set
    ]
    hidden_rng.shuffle(available_for_hidden)
    hidden_extra = available_for_hidden[: CASE_COUNT - len(hidden_core)]
    hidden_set = hidden_core_set | set(hidden_extra)

    visible_configs = visible_core + visible_extra
    hidden_configs = hidden_core + hidden_extra
    visible_rng.shuffle(visible_configs)
    hidden_rng.shuffle(hidden_configs)

    if len(visible_configs) != CASE_COUNT or len(hidden_configs) != CASE_COUNT:
        raise RuntimeError("failed to create the required case counts")
    if len(set(visible_configs)) != CASE_COUNT or len(set(hidden_configs)) != CASE_COUNT:
        raise RuntimeError("configuration selection produced duplicates")
    if visible_set & hidden_set:
        raise RuntimeError("visible and hidden configurations overlap")
    for dataset, configs in (("visible", visible_configs), ("hidden", hidden_configs)):
        font_mask_pairs = {(config[0], config[4]) for config in configs}
        if len(font_mask_pairs) != len(FONTS) * 16:
            raise RuntimeError(f"{dataset} set does not cover all font/flag pairs")
    return visible_configs, hidden_configs


def base_argv(config: Config) -> list[str]:
    font, width, direction, justification, mask = config
    argv = ["-f", font, "-w", str(width), "-D", direction, "-j", justification]
    argv.extend(flag for bit, flag in FLAG_NAMES if mask & bit)
    return argv


def probe_safe_texts(repo: Path) -> dict[tuple[str, int], tuple[str, ...]]:
    """Probe original font/width pairs and retain known renderable glyphs."""
    safe: dict[tuple[str, int], tuple[str, ...]] = {}
    failures = 0
    for font in FONTS:
        for width in WIDTHS:
            candidates = NARROW_PROBE_TEXTS if width <= 20 else ("i",)
            accepted: list[str] = []
            for text in candidates:
                argv = ["-f", font, "-w", str(width), "-D", "auto", "-j", "auto", "--", text]
                result = run_oracle(repo, argv, PROBE_TIMEOUT_SECONDS)
                if rendered_success(result):
                    if len(text) == 1:
                        accepted.append(text)
                    continue

                failures += 1
                reason = failure_reason(result, PROBE_TIMEOUT_SECONDS)
                report_event({
                    "event": "oracle_probe_rejected",
                    "font": font,
                    "width": width,
                    "text": text,
                    "argv": argv,
                    "reason": reason,
                    "action": "rejected candidate; probing the next deterministic candidate",
                })

            if not accepted:
                raise RuntimeError(f"no safe nonempty probe text for font={font}, width={width}")
            # Keep fallback order fixed, independent of completion timing.
            ordered = tuple(text for text in FALLBACK_TEXTS if text in accepted)
            safe[(font, width)] = ordered
    print(f"Probed {len(safe)} font/width pairs; rejected {failures} unsafe probe candidates", flush=True)
    return safe


def text_for_case(
    index: int,
    config: Config,
    rng: random.Random,
    safe_texts: dict[tuple[str, int], tuple[str, ...]],
) -> str:
    font, width, _, _, _ = config
    if width <= 20:
        return rng.choice(safe_texts[(font, width)])

    max_word_length = {40: 2, 60: 3, 80: 4, 120: 6}[width]
    corpus = TEXTS + SINGLE_CHAR_TEXTS
    eligible = [
        text
        for text in corpus
        if text.strip()
        and max((len(word) for word in re.split(r"\s+", text.strip()) if word), default=0)
        <= max_word_length
    ]
    if width >= 40 and index % 5 == 0:
        multiword = [
            text for text in MULTIWORD_TEXTS
            if max(len(word) for word in text.split()) <= max_word_length
        ]
        if multiword:
            return rng.choice(multiword)
    return rng.choice(eligible)


def argv_with_text(config: Config, text: str) -> list[str]:
    argv = base_argv(config)
    argv.append("--")
    if " " in text and text.strip() == text:
        argv.extend(text.split(" "))
    else:
        argv.append(text)
    return argv


def run_case(
    repo: Path,
    dataset: str,
    case_id: str,
    config: Config,
    preferred_text: str,
    safe_texts: dict[tuple[str, int], tuple[str, ...]],
) -> dict[str, Any]:
    font, width, _, _, _ = config
    fallback_order = safe_texts[(font, width)]
    attempts = [preferred_text] + [text for text in fallback_order if text != preferred_text]
    for attempt_index, text in enumerate(attempts):
        argv = argv_with_text(config, text)
        result = run_oracle(repo, argv, CASE_TIMEOUT_SECONDS)
        if rendered_success(result):
            stdout, stderr, exit_code = result
            if width <= 20 and not any(char not in " \t\r\n" for char in stdout):
                rendered_successful = False
            else:
                rendered_successful = True
            if rendered_successful:
                return {
                    "id": case_id,
                    "argv": argv,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                }

        reason = failure_reason(result, CASE_TIMEOUT_SECONDS)
        if attempt_index + 1 >= len(attempts):
            raise RuntimeError(f"no safe input after reference failure for {case_id}: {reason}")
        report_event({
            "event": "oracle_case_rejected",
            "dataset": dataset,
            "id": case_id,
            "font": font,
            "width": width,
            "argv": argv,
            "reason": reason,
            "action": f"retrying with deterministic safe candidate {attempts[attempt_index + 1]!r}",
        })

    raise RuntimeError(f"unreachable: no reference result for {case_id}")


def render_dataset(
    repo: Path,
    dataset: str,
    configs: list[Config],
    rng: random.Random,
    safe_texts: dict[tuple[str, int], tuple[str, ...]],
) -> list[dict[str, Any]]:
    cases = [
        (index, config, text_for_case(index, config, rng, safe_texts))
        for index, config in enumerate(configs)
    ]
    with ThreadPoolExecutor(max_workers=WORKERS) as workers:
        results = workers.map(
            lambda item: run_case(
                repo,
                dataset,
                f"{dataset}-{item[0] + 1:04d}",
                item[1],
                item[2],
                safe_texts,
            ),
            cases,
        )
        records = []
        for index, record in enumerate(results, start=1):
            records.append(record)
            if index % 250 == 0:
                print(f"{dataset}: generated {index}/{CASE_COUNT}", flush=True)
    return records


def serialize_dataset(records: list[dict[str, Any]]) -> bytes:
    return "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records).encode("utf-8")


def validate_reference_tree(repo: Path, parser: argparse.ArgumentParser) -> None:
    if not (repo / "pyfiglet" / "__main__.py").is_file():
        parser.error(f"{repo} does not contain pyfiglet/__main__.py")
    for font in FONTS:
        if not any((repo / "pyfiglet" / "fonts" / f"{font}.{ext}").is_file() for ext in ("flf", "tlf")):
            parser.error(f"required font {font!r} is missing from {repo / 'pyfiglet' / 'fonts'}")


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    default_repo = script_dir.parents[1] / "pyfiglet"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pyfiglet-repo",
        type=Path,
        default=default_repo,
        help="path to the checked-out original pyfiglet repository",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="regenerate in memory and compare both JSONL files without writing them",
    )
    args = parser.parse_args()
    repo = args.pyfiglet_repo.resolve()
    validate_reference_tree(repo, parser)

    visible_rng, hidden_rng = make_rngs()
    visible_configs, hidden_configs = build_config_sets(visible_rng, hidden_rng)
    safe_texts = probe_safe_texts(repo)
    visible = render_dataset(repo, "visible", visible_configs, visible_rng, safe_texts)
    hidden = render_dataset(repo, "hidden", hidden_configs, hidden_rng, safe_texts)
    outputs = {
        "visible": serialize_dataset(visible),
        "hidden": serialize_dataset(hidden),
    }
    print(
        "Reference diagnostics:",
        ", ".join(f"{event}={count}" for event, count in sorted(EVENT_COUNTS.items())) or "none",
        flush=True,
    )

    if args.verify:
        for name, regenerated in outputs.items():
            path = script_dir / f"{name}.jsonl"
            if not path.is_file():
                print(f"missing {path}", file=sys.stderr)
                return 1
            if path.read_bytes() != regenerated:
                print(f"deterministic regeneration mismatch: {path}", file=sys.stderr)
                return 1
            print(f"{name}: regenerated JSONL is byte-identical", flush=True)
        return 0

    (script_dir / "visible.jsonl").write_bytes(outputs["visible"])
    (script_dir / "hidden.jsonl").write_bytes(outputs["hidden"])
    print(f"Wrote {CASE_COUNT} visible and {CASE_COUNT} hidden cases using {repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
