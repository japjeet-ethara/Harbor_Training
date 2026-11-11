"""Trusted grader. Candidate compilation/execution happens only inside Worker.

Do not execute evaluate() on a workstation. /tests and its hidden fixtures are
baked into the separate verifier image. The Worker copies public submission
files to a fresh UID's scratch directory and cannot access the original
submission, hidden answers, the grader, or verifier logs.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any

from rewardkit import Worker, WorkerError, WorkerSetupError

TESTS = Path("/tests")
PRIVATE = Path("/run/titlecase-grader")
LOGS = Path("/logs/verifier")
WORKSPACE = Path("/workspace/repo")
CASE_COUNT = 2000
BUILD_TIMEOUT = 180.0
EXECUTION_TIMEOUT = 30.0
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
_LOCK = threading.Lock()
_CACHE: dict[str, dict[str, float]] = {}

# Never inherit task-controlled HOME, GOFLAGS, GOENV, PATH, proxy, or toolchain
# settings. No compiler hooks, external module fetches, or CGO are enabled.
WORKER_ENV = {
    "PATH": "/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin",
    "GOTOOLCHAIN": "local",
    "GOENV": "off",
    "GOWORK": "off",
    "GOFLAGS": "-mod=readonly",
    "GOPROXY": "off",
    "GOSUMDB": "off",
    "GOVCS": "*:off",
    "CGO_ENABLED": "0",
}
BUILD_SCRIPT = """set -eu
cd repo
export GOCACHE="$HOME/.cache/go-build"
export GOMODCACHE="$HOME/go/pkg/mod"
mkdir -p "$GOCACHE" "$GOMODCACHE"
/usr/local/go/bin/go mod edit -json > ../module.json
/usr/local/go/bin/go list -json . > ../root.json
/usr/local/go/bin/go list -deps -json ./... > ../deps.json
/usr/local/go/bin/go build ./...
/usr/local/go/bin/go build -o ../candidate .
"""


class GraderInfrastructureError(RuntimeError):
    """The grader or immutable fixtures are broken; no reward should be emitted."""


def lf_records(data: bytes) -> list[bytes]:
    """Split only ASCII LF; preserve spaces, CR, empty records and all UTF-8 bytes."""
    if not data:
        return []
    if not data.endswith(b"\n"):
        raise ValueError("missing final LF")
    return data.split(b"\n")[:-1]


def score_records(actual: bytes, expected: list[bytes]) -> tuple[float, int, int, str]:
    """Missing/extra records or an unterminated output invalidate the whole run."""
    if not expected:
        raise GraderInfrastructureError("The hidden answer set is empty")
    try:
        records = lf_records(actual)
    except ValueError:
        count = actual.count(b"\n") + bool(actual)
        return 0.0, 0, count, "missing_final_lf"
    if len(records) != len(expected):
        return 0.0, 0, len(records), "wrong_record_count"
    matches = sum(left == right for left, right in zip(records, expected, strict=True))
    return matches / len(expected), matches, len(records), "compared"


def json_objects(data: bytes) -> list[dict[str, Any]]:
    """Decode the adjacent JSON objects written by the official go list command."""
    decoder = json.JSONDecoder()
    rest = data.decode("utf-8")
    objects: list[dict[str, Any]] = []
    while rest:
        rest = rest.lstrip()
        if not rest:
            break
        value, end = decoder.raw_decode(rest)
        if not isinstance(value, dict):
            raise ValueError("go list emitted a non-object")
        objects.append(value)
        rest = rest[end:]
    return objects


def audit_go_metadata(files: dict[str, bytes] | Any) -> tuple[bool, str, int]:
    """Audit imports as well as go.mod; offline mode alone cannot reject vendoring."""
    try:
        module = json.loads(files["module.json"])
        roots = json_objects(files["root.json"])
        deps = json_objects(files["deps.json"])
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise GraderInfrastructureError("Unexpected Go toolchain metadata") from exc
    if not isinstance(module, dict) or not roots or not deps:
        raise GraderInfrastructureError("Empty or malformed Go toolchain metadata")
    if module.get("Require"):
        return False, "external_module_requirement", len(deps)
    if len(roots) != 1 or roots[0].get("Name") != "main":
        return False, "root_package_is_not_main", len(deps)
    root_module = roots[0].get("Module") or {}
    if root_module.get("Main") is not True:
        return False, "root_package_is_not_main_module", len(deps)
    for package in deps:
        if package.get("Standard") is True:
            continue
        dependency_module = package.get("Module") or {}
        if dependency_module.get("Main") is not True:
            return False, "non_standard_library_dependency", len(deps)
    return True, "passed", len(deps)


def load_fixtures(base: Path = TESTS) -> tuple[bytes, list[bytes], dict[str, str]]:
    """Validate immutable golden files before assessing a submission."""
    try:
        manifest_bytes = (base / "data/manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        decoded: dict[str, list[bytes]] = {}
        raw: dict[str, bytes] = {}
        hashes: dict[str, str] = {}
        for name in ("inputs.txt", "expected.txt", "hidden_inputs.txt", "hidden_expected.txt"):
            payload = (base / "data" / name).read_bytes()
            payload.decode("utf-8", errors="strict")
            records = lf_records(payload)
            item = manifest["files"][name]
            digest = hashlib.sha256(payload).hexdigest()
            if len(records) != CASE_COUNT or item["records"] != CASE_COUNT:
                raise ValueError(f"{name}: expected {CASE_COUNT} records")
            if digest != item["sha256"] or len(payload) != item["bytes"]:
                raise ValueError(f"{name}: manifest checksum or byte length differs")
            if b"\r" in payload:
                raise ValueError(f"{name}: CR is excluded from fixture records")
            raw[name], decoded[name], hashes[name] = payload, records, digest
        if set(decoded["inputs.txt"]) & set(decoded["hidden_inputs.txt"]):
            raise ValueError("Public and hidden inputs overlap")
        hashes["manifest.json"] = hashlib.sha256(manifest_bytes).hexdigest()
        return raw["hidden_inputs.txt"], decoded["hidden_expected.txt"], hashes
    except (OSError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise GraderInfrastructureError(f"Invalid frozen fixtures: {exc}") from exc


def has_python_files(workspace: Path) -> bool:
    def walk_error(exc: OSError) -> None:
        raise exc

    for _, _, files in os.walk(workspace, followlinks=False, onerror=walk_error):
        if any(name.endswith(".py") for name in files):
            return True
    return False


def make_worker(workspace: Path) -> Worker:
    return Worker(
        private_paths=(TESTS, LOGS, PRIVATE, workspace),
        env=WORKER_ENV,
        max_output_bytes=MAX_OUTPUT_BYTES,
    )


def write_report(report: dict[str, Any]) -> None:
    # Trusted file only; do not include candidate output or hidden answer text.
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "grade-details.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _evaluate(workspace: Path) -> dict[str, float]:
    if workspace != WORKSPACE or not (TESTS / ".container-verifier").is_file():
        raise GraderInfrastructureError("Use Harbor's dedicated Docker verifier image")
    if os.geteuid() != 0:
        raise GraderInfrastructureError("The trusted verifier must run as container root")
    hidden_input, expected, hashes = load_fixtures()
    scores = {"build": 0.0, "no_python": 0.0, "behaviour": 0.0}
    report: dict[str, Any] = {
        "schema_version": 1,
        "hidden_records": len(expected),
        "fixture_sha256": hashes,
        "build_status": "not_started",
        "behaviour_status": "not_run",
        "matched_records": 0,
        "output_records": 0,
        "python_files_present": None,
        "isolation": "rewardkit.Worker/fresh-uid",
        "scores": scores,
    }
    if workspace.is_symlink() or not workspace.is_dir():
        report["build_status"] = "missing_or_linked_submission_directory"
        write_report(report)
        return scores
    try:
        python_present = has_python_files(workspace)
    except OSError:
        report["build_status"] = "unreadable_submission_tree"
        write_report(report)
        return scores
    report["python_files_present"] = python_present
    worker = make_worker(workspace)
    try:
        build = worker.run(
            BUILD_SCRIPT,
            files=[workspace],
            outputs=["module.json", "root.json", "deps.json", "candidate"],
            timeout_sec=BUILD_TIMEOUT,
        )
    except WorkerSetupError:
        # A failed boundary or cleanup is infrastructure failure, never a score.
        raise
    except WorkerError:
        report["build_status"] = "copy_timeout_or_output_limit"
        write_report(report)
        return scores
    if build.returncode != 0:
        report.update(build_status="command_failed", build_returncode=build.returncode)
        write_report(report)
        return scores
    build_ok, reason, dependency_count = audit_go_metadata(build.files)
    report.update(build_status=reason, dependency_packages=dependency_count)
    if not build_ok:
        write_report(report)
        return scores
    if not build.files.get("candidate"):
        report["build_status"] = "missing_root_executable"
        write_report(report)
        return scores
    scores["build"] = 1.0
    scores["no_python"] = float(not python_present)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    PRIVATE.chmod(0o700)
    candidate = PRIVATE / "candidate"
    candidate.write_bytes(build.files["candidate"])
    candidate.chmod(0o755)
    try:
        try:
            execution = worker.run(
                "set -eu\ncd repo\nexec ../candidate\n",
                files=[workspace, candidate],
                stdin=hidden_input,
                timeout_sec=EXECUTION_TIMEOUT,
            )
        except WorkerSetupError:
            raise
        except WorkerError:
            report["behaviour_status"] = "copy_timeout_or_output_limit"
        else:
            report["behaviour_returncode"] = execution.returncode
            if execution.returncode != 0:
                report["behaviour_status"] = "command_failed"
            else:
                score, matches, count, status = score_records(execution.stdout, expected)
                scores["behaviour"] = score
                report.update(
                    matched_records=matches, output_records=count, behaviour_status=status
                )
    finally:
        candidate.unlink(missing_ok=True)
    write_report(report)
    return scores


def evaluate(workspace: Path) -> dict[str, float]:
    """All three criteria use one immutable observation, even if called in parallel."""
    key = str(workspace)
    with _LOCK:
        if key not in _CACHE:
            try:
                _CACHE[key] = _evaluate(workspace)
            except (WorkerSetupError, GraderInfrastructureError) as exc:
                # Deliberately leave reward.json absent. RewardKit/Harbor propagate
                # this as an errored trial, so it cannot be mistaken for a zero.
                write_report({"schema_version": 1, "infrastructure_error": type(exc).__name__,
                              "message": str(exc)})
                raise
        return _CACHE[key].copy()
