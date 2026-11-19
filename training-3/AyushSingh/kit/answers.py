#!/usr/bin/env python3
"""Run the original python-titlecase twice on a pool of titles, keep stable answers, and write inputs.txt, answers.txt, report.txt."""

from pathlib import Path
import sys


def main():
    if len(sys.argv) != 4:
        print("Usage: answers.py <python-titlecase dir> <pool.txt> <out_dir>", file=sys.stderr)
        sys.exit(1)

    py_dir = Path(sys.argv[1]).resolve()
    pool_file = Path(sys.argv[2]).resolve()
    out_dir = Path(sys.argv[3]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Import titlecase module from specified directory
    sys.path.insert(0, str(py_dir))
    try:
        from titlecase import REGEX_AVAILABLE, titlecase
    except ImportError:
        # Check if titlecase is inside a subdirectory or single file
        import importlib.util
        init_py = py_dir / "titlecase" / "__init__.py"
        if not init_py.is_file():
            init_py = py_dir / "__init__.py"
        spec = importlib.util.spec_from_file_location("titlecase", str(init_py))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        titlecase = mod.titlecase
        REGEX_AVAILABLE = getattr(mod, "REGEX_AVAILABLE", False)

    mode_str = "regex" if REGEX_AVAILABLE else "re"
    print(f"[answers.py] Using mode: {mode_str} (REGEX_AVAILABLE={REGEX_AVAILABLE})")

    with open(pool_file, "r", encoding="utf-8") as f:
        pool_lines = [line.strip("\r\n") for line in f]

    total = len(pool_lines)
    kept_inputs = []
    kept_answers = []
    dropped = 0

    for idx, line in enumerate(pool_lines):
        # Run original twice to test stability
        ans1 = titlecase(line)
        ans2 = titlecase(line)
        if ans1 == ans2:
            kept_inputs.append(line)
            kept_answers.append(ans1)
        else:
            dropped += 1

    inputs_path = out_dir / "inputs.txt"
    answers_path = out_dir / "answers.txt"
    report_path = out_dir / "report.txt"

    with open(inputs_path, "w", encoding="utf-8", newline="\n") as f:
        for inp in kept_inputs:
            f.write(inp + "\n")

    with open(answers_path, "w", encoding="utf-8", newline="\n") as f:
        for ans in kept_answers:
            f.write(ans + "\n")

    report_content = (
        f"mode: {mode_str}\n"
        f"total: {total}\n"
        f"kept: {len(kept_inputs)}\n"
        f"dropped: {dropped}\n"
    )
    with open(report_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(report_content)

    print(f"[answers.py] Finished: {len(kept_inputs)} kept, {dropped} dropped. Report written to {report_path}")


if __name__ == "__main__":
    main()
