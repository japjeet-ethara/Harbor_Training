"""Harbor Verifier — Step 5 Reward Tests for Titlecase in Go.

Implements Harbor Reward Kit programmatic criteria with weighted-mean aggregation.
Each function below is registered as a criterion via @rk.criterion and then
explicitly re-registered at the bottom with the required weight by calling the
factory (rk.build, rk.no_python, rk.behaviour).  This is the correct Reward Kit
0.2.* pattern: decoration creates the factory; calling it sets weight + registers
in the current session.

Three checks:
  1. build      (weight 1): `go build ./...` in /workspace/repo passes → 1, else 0.
  2. no_python  (weight 1): no .py files anywhere under /workspace/repo AND build
                             passes → 1, else 0.
  3. behaviour  (weight 4): build the Go program, feed it hidden_inputs.txt via
                             stdin, score = number of output lines that exactly match
                             the corresponding line in hidden_expected.txt divided by
                             the total number of expected lines (2000).  Extra output
                             lines beyond the expected count do not raise the score;
                             missing output lines lower it.

Final reward = (build + no_python + 4 × behaviour) / 6
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

try:
    import rewardkit as rk
    _HAS_RK = True
except (ImportError, ModuleNotFoundError, AttributeError):
    _HAS_RK = False

    # Lightweight stand-in used only when the file is run directly on the host.
    # In the real verifier container rewardkit is always present, so this branch
    # is never reached there.
    class _FallbackRewardKit:
        def criterion(self, fn=None, **kwargs):
            # @rk.criterion or @rk.criterion(description='...'): return fn unchanged
            # so that the decorated name is still callable in __main__.
            if fn is not None:
                return fn

            def decorator(func):
                return func

            return decorator

        def __getattr__(self, name: str):
            # rk.build(weight=1.0) etc. → no-op
            return lambda *args, **kwargs: None

    rk = _FallbackRewardKit()


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _repo_dir(workspace: Path) -> Path | None:
    """Return the repository directory, or None if it cannot be located."""
    candidate = Path("/workspace/repo")
    if candidate.exists():
        return candidate
    if workspace and workspace.exists():
        return workspace
    return None


def _find_go_main_target(repo: Path) -> str | None:
    """Return the Go package target that contains 'package main', or None."""
    _PATTERN = re.compile(r"^\s*package\s+main\b", re.MULTILINE)

    # Prefer the repository root so that cmd/ subdirectories don't win over root.
    for go_file in sorted(repo.glob("*.go")):
        try:
            if _PATTERN.search(go_file.read_text(encoding="utf-8", errors="ignore")):
                return "."
        except OSError:
            pass

    # Fall back to any subdirectory.
    for go_file in sorted(repo.rglob("*.go")):
        try:
            if _PATTERN.search(go_file.read_text(encoding="utf-8", errors="ignore")):
                rel = go_file.parent.relative_to(repo)
                return "./" + str(rel).replace("\\", "/")
        except OSError:
            pass

    return None


# ---------------------------------------------------------------------------
# Logic functions — defined independently so they can be called directly
# (e.g. from __main__ or tests) even when @rk.criterion replaces the name
# with a _CriterionHandle that raises TypeError on direct invocation.
# ---------------------------------------------------------------------------

def _do_build(workspace: Path) -> float:
    """Run `go build ./...` in /workspace/repo.  Return 1.0 on success, 0.0 otherwise."""
    repo = _repo_dir(workspace)
    if repo is None:
        return 0.0

    env = {**os.environ, "CGO_ENABLED": "0"}
    try:
        proc = subprocess.run(
            ["go", "build", "./..."],
            cwd=str(repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return 1.0 if proc.returncode == 0 else 0.0
    except Exception:
        return 0.0


def _do_no_python(workspace: Path) -> float:
    """Return 1.0 iff no .py files exist under /workspace/repo AND build passes."""
    repo = _repo_dir(workspace)
    if repo is None:
        return 0.0

    try:
        py_files = list(repo.rglob("*.py"))
    except OSError:
        return 0.0

    if py_files:
        return 0.0

    # Build must also pass for this check to award a point.
    return _do_build(workspace)


def _do_behaviour(workspace: Path) -> float:
    """Score = matched lines / total expected lines (0.0–1.0, continuous).

    Builds the Go binary from /workspace/repo, feeds hidden_inputs.txt through
    stdin, and compares each output line to the corresponding line in
    hidden_expected.txt.  The denominator is always the number of expected lines
    (2000) so that:

    * Extra output lines beyond position 1999 do not raise the score — only the
      first 2000 output lines are compared.
    * Missing output lines (fewer than 2000) are treated as non-matching — the
      denominator stays at 2000.

    This prevents any game-able edge case from inflating the score above its
    true value.
    """
    repo = _repo_dir(workspace)
    if repo is None:
        return 0.0

    hidden_inputs = Path("/tests/data/hidden_inputs.txt")
    if not hidden_inputs.exists():
        hidden_inputs = Path(__file__).resolve().parent / "data" / "hidden_inputs.txt"

    hidden_expected = Path("/tests/data/hidden_expected.txt")
    if not hidden_expected.exists():
        hidden_expected = Path(__file__).resolve().parent / "data" / "hidden_expected.txt"

    if not hidden_inputs.is_file() or not hidden_expected.is_file():
        return 0.0

    main_target = _find_go_main_target(repo)
    if main_target is None:
        return 0.0

    env = {**os.environ, "CGO_ENABLED": "0"}

    with tempfile.TemporaryDirectory() as tmp_dir:
        bin_name = "titlecase_bin.exe" if sys.platform == "win32" else "titlecase_bin"
        bin_path = Path(tmp_dir) / bin_name

        try:
            build_proc = subprocess.run(
                ["go", "build", "-o", str(bin_path), main_target],
                cwd=str(repo),
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if build_proc.returncode != 0:
                return 0.0
        except Exception:
            return 0.0

        try:
            expected_lines = hidden_expected.read_text(encoding="utf-8").splitlines()
        except OSError:
            return 0.0

        total_expected = len(expected_lines)
        if total_expected == 0:
            return 0.0

        try:
            with open(hidden_inputs, "rb") as f_in:
                run_proc = subprocess.run(
                    [str(bin_path)],
                    stdin=f_in,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(repo),
                    env=env,
                    timeout=120,
                )
            if run_proc.returncode != 0:
                return 0.0

            actual_lines = run_proc.stdout.decode("utf-8", errors="replace").splitlines()

            # Compare exactly total_expected positions.
            # actual_lines[i] is "" (non-matching) when i >= len(actual_lines).
            # Extra actual lines beyond total_expected are never compared.
            matches = sum(
                1
                for i in range(total_expected)
                if i < len(actual_lines) and actual_lines[i] == expected_lines[i]
            )
            return float(matches) / float(total_expected)

        except Exception:
            return 0.0


# ---------------------------------------------------------------------------
# Reward Kit criterion registrations
# ---------------------------------------------------------------------------
# @rk.criterion(description='...') replaces each decorated name with a
# _CriterionHandle instance (raises TypeError on direct call) AND registers a
# factory in the global _factory_registry.  The module-level calls
# rk.build(weight=N) then invoke that factory, which registers the criterion in
# the current Session at the specified weight.  The auto-registration that fires
# at decoration time (weight=1.0) is replaced by the explicit call below.

@rk.criterion(description="Check 1: `go build ./...` in /workspace/repo passes")
def build(workspace: Path) -> float:
    return _do_build(workspace)


@rk.criterion(description="Check 2: No .py files under /workspace/repo AND build passes")
def no_python(workspace: Path) -> float:
    return _do_no_python(workspace)


@rk.criterion(description="Check 3: Behaviour — proportion of hidden lines matched (0.0–1.0)")
def behaviour(workspace: Path) -> float:
    return _do_behaviour(workspace)


# Explicit weight registration — these calls REPLACE the auto weight=1.0 entries.
rk.build(weight=1.0)
rk.no_python(weight=1.0)
rk.behaviour(weight=4.0)


# ---------------------------------------------------------------------------
# Local smoke-test  (python tests/test_outputs.py)
# ---------------------------------------------------------------------------
# Calls the _do_* functions directly — bypasses _CriterionHandle — so this
# block works both on the host (rk = fallback) and in the container (rk = real).

if __name__ == "__main__":
    _repo = _repo_dir(Path("/workspace/repo"))
    if _repo is None:
        # Try to find a local fallback for host-side inspection only.
        _candidate = Path(__file__).resolve().parent.parent / "environment" / "python-titlecase"
        _repo = _candidate if _candidate.exists() else Path(__file__).resolve().parent.parent

    _b   = _do_build(_repo)
    _np  = _do_no_python(_repo)
    _beh = _do_behaviour(_repo)
    _reward = round((_b * 1.0 + _np * 1.0 + _beh * 4.0) / 6.0, 4)

    print("=== Harbor Reward Kit — local smoke test ===")
    print(f"Check 1  build      (wt 1): {_b:.4f}")
    print(f"Check 2  no_python  (wt 1): {_np:.4f}")
    print(f"Check 3  behaviour  (wt 4): {_beh:.4f}")
    print(f"Weighted mean  (1+1+4)/6  : {_reward:.4f}")
    print()
    print("Expected scores:")
    print("  nothing done  → 0.0000")
    print("  build only    → 0.1667  (1/6)")
    print("  perfect       → 1.0000")
