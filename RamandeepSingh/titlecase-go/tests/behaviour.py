"""
Criterion 3: behaviour (weight 4)
Build the Go program, feed it tests/data/hidden_inputs.txt via stdin,
and compare its output line by line against tests/data/hidden_expected.txt.
Score the fraction of lines that match exactly (between 0.0 and 1.0).
"""

import os
import subprocess
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(fn):
        return fn


@criterion
def check_behaviour(workspace: Path) -> float:
    try:
        # Locate hidden inputs and hidden expected outputs
        data_dir = Path(__file__).resolve().parent / "data"
        hidden_inputs_path = data_dir / "hidden_inputs.txt"
        hidden_expected_path = data_dir / "hidden_expected.txt"

        if not hidden_inputs_path.exists() or not hidden_expected_path.exists():
            return 0.0

        with open(hidden_expected_path, "r", encoding="utf-8") as f:
            expected_lines = f.read().splitlines()

        if not expected_lines:
            return 0.0

        with open(hidden_inputs_path, "rb") as f:
            input_bytes = f.read()

        # Build Go binary to a temporary path inside /tmp (or OS tempdir)
        import tempfile
        tmp_dir = Path(tempfile.gettempdir())
        bin_path = tmp_dir / "_titlecase_eval_bin"
        if bin_path.exists():
            try:
                bin_path.unlink()
            except Exception:
                pass

        build_res = subprocess.run(
            ["go", "build", "-o", str(bin_path), "."],
            cwd=str(workspace),
            capture_output=True,
            timeout=120,
        )
        if build_res.returncode != 0 or not bin_path.exists():
            return 0.0

        # Execute the Go binary with hidden inputs fed to stdin
        try:
            run_res = subprocess.run(
                [str(bin_path)],
                input=input_bytes,
                capture_output=True,
                timeout=120,
            )
        finally:
            if bin_path.exists():
                try:
                    bin_path.unlink()
                except Exception:
                    pass

        if run_res.returncode != 0:
            return 0.0

        actual_output = run_res.stdout.decode("utf-8", errors="replace")
        actual_lines = actual_output.splitlines()

        # Score line-by-line exact matches against expected outputs
        total = len(expected_lines)
        matches = 0
        for i in range(total):
            if i < len(actual_lines) and actual_lines[i] == expected_lines[i]:
                matches += 1

        return float(matches) / float(total)
    except Exception:
        return 0.0


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace/repo")
    print(check_behaviour(target))
