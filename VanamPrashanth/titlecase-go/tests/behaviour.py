import subprocess
import sys
from pathlib import Path

try:
    from rewardkit import criterion
except ImportError:
    def criterion(func=None, **kwargs):
        if callable(func):
            return func
        def decorator(f):
            return f
        return decorator


@criterion
def behaviour(workspace: Path = Path("/workspace/repo")) -> float:
    """3. behaviour (weight 4): build the Go program, feed it tests/data/hidden_inputs.txt,
    score = share of lines that exactly match tests/data/hidden_expected.txt.
    """
    repo_dir = Path("/workspace/repo")
    if not repo_dir.exists() and workspace and Path(workspace).exists():
        repo_dir = Path(workspace)

    if not repo_dir.exists():
        return 0.0

    # Locate hidden_inputs.txt and hidden_expected.txt
    here = Path(__file__).resolve().parent
    candidates = [
        here / "data",
        here.parent / "tests" / "data",
        Path("/tests/data"),
        Path("tests/data"),
    ]
    data_dir = None
    for c in candidates:
        if (c / "hidden_inputs.txt").is_file() and (c / "hidden_expected.txt").is_file():
            data_dir = c
            break

    if not data_dir:
        return 0.0

    inputs_path = data_dir / "hidden_inputs.txt"
    expected_path = data_dir / "hidden_expected.txt"

    bin_ext = ".exe" if sys.platform == "win32" else ""
    tmp_dir = Path("/tmp") if Path("/tmp").exists() else here
    bin_path = tmp_dir / f"titlecase_test_bin{bin_ext}"
    if bin_path.exists():
        try:
            bin_path.unlink()
        except OSError:
            pass

    built = False
    # Attempt 1: Build from repo root
    try:
        res = subprocess.run(
            ["go", "build", "-o", str(bin_path), "."],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if res.returncode == 0 and bin_path.is_file():
            built = True
    except Exception:
        pass

    # Attempt 2: If root wasn't package main, locate package main in repo
    if not built:
        try:
            res = subprocess.run(
                ["go", "list", "-f", '{{if eq .Name "main"}}{{.Dir}}{{end}}', "./..."],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=60,
            )
            main_dirs = [d.strip() for d in res.stdout.splitlines() if d.strip()]
            if main_dirs:
                build_res = subprocess.run(
                    ["go", "build", "-o", str(bin_path), "."],
                    cwd=main_dirs[0],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if build_res.returncode == 0 and bin_path.is_file():
                    built = True
        except Exception:
            pass

    if not built or not bin_path.is_file():
        return 0.0

    # Run the compiled binary with hidden_inputs.txt on stdin
    try:
        input_bytes = inputs_path.read_bytes()
        proc = subprocess.run(
            [str(bin_path)],
            input=input_bytes,
            capture_output=True,
            cwd=str(repo_dir),
            timeout=180,
        )
    except Exception:
        return 0.0
    finally:
        if bin_path.exists():
            try:
                bin_path.unlink()
            except OSError:
                pass

    expected_lines = expected_path.read_text(encoding="utf-8").splitlines()
    output_lines = proc.stdout.decode("utf-8", errors="replace").splitlines()

    if not expected_lines:
        return 1.0

    matches = 0
    for i, exp in enumerate(expected_lines):
        if i < len(output_lines) and output_lines[i] == exp:
            matches += 1

    return float(matches / len(expected_lines))


if __name__ == "__main__":
    print(behaviour())
