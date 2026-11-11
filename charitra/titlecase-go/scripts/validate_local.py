#!/usr/bin/env python3
"""Validate the trusted reference solution locally against frozen fixtures.

This is NOT a Harbor trial and does not invoke the security-isolated verifier.
Only the supplied reference Go source is compiled and executed. Do not use this
helper to run an untrusted submission on your workstation.

Usage, from any directory:
    python3 scripts/validate_local.py
    python3 scripts/validate_local.py --go /path/to/go --report evidence/local-validation.json

The default report path is relative to this task's root. An explicitly supplied
relative --report path is relative to the current working directory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

TASK_ROOT = Path(__file__).resolve().parents[1]
CASE_COUNT = 2000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def records(payload: bytes, label: str) -> list[bytes]:
    """Split ASCII LF only, preserving NUL, Unicode separators and blank titles."""
    if not payload.endswith(b"\n"):
        raise ValueError(f"{label}: expected a final LF")
    return payload.split(b"\n")[:-1]


def json_objects(payload: bytes) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    text = payload.decode("utf-8")
    result = []
    while text.strip():
        text = text.lstrip()
        item, end = decoder.raw_decode(text)
        if not isinstance(item, dict):
            raise ValueError("Go tool emitted an unexpected JSON value")
        result.append(item)
        text = text[end:]
    return result


def run(command: list[str], cwd: Path, env: dict[str, str], *,
        stdin: bytes | None = None, timeout: int = 180) -> subprocess.CompletedProcess:
    proc = subprocess.run(command, cwd=cwd, env=env, input=stdin,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout, check=False)
    if proc.returncode != 0:
        error = proc.stderr.decode("utf-8", errors="replace")[:3000].strip()
        raise RuntimeError(f"{Path(command[0]).name} exited {proc.returncode}: {error}")
    return proc


def load_fixtures() -> tuple[dict[str, bytes], dict[str, Any]]:
    data_dir = TASK_ROOT / "tests" / "data"
    manifest_payload = (data_dir / "manifest.json").read_bytes()
    manifest = json.loads(manifest_payload)
    fixtures = {}
    metadata: dict[str, Any] = {
        "manifest_sha256": sha256(manifest_payload),
        "reference": manifest["reference"],
        "upstream": manifest["upstream"],
        "files": {},
    }
    for name in ("inputs.txt", "expected.txt", "hidden_inputs.txt", "hidden_expected.txt"):
        payload = (data_dir / name).read_bytes()
        payload.decode("utf-8", errors="strict")
        lines = records(payload, name)
        spec = manifest["files"][name]
        if len(lines) != CASE_COUNT or spec["records"] != CASE_COUNT:
            raise ValueError(f"{name}: expected exactly {CASE_COUNT} records")
        if len(payload) != spec["bytes"] or sha256(payload) != spec["sha256"]:
            raise ValueError(f"{name}: bytes or SHA-256 differ from the frozen manifest")
        if b"\r" in payload:
            raise ValueError(f"{name}: embedded CR is outside the stated protocol")
        fixtures[name] = payload
        metadata["files"][name] = {
            "records": len(lines), "bytes": len(payload), "sha256": sha256(payload),
        }
    public = records(fixtures["inputs.txt"], "public inputs")
    hidden = records(fixtures["hidden_inputs.txt"], "hidden inputs")
    if set(public) & set(hidden):
        raise ValueError("Public and hidden input corpora overlap")
    metadata["public_hidden_inputs_disjoint"] = True
    return fixtures, metadata


def audit_dependencies(module: dict[str, Any], root: list[dict[str, Any]],
                       packages: list[dict[str, Any]]) -> dict[str, Any]:
    if module.get("Require"):
        raise ValueError("The solution declares a third-party module requirement")
    if len(root) != 1 or root[0].get("Name") != "main":
        raise ValueError("The solution root must be one executable main package")
    if not (root[0].get("Module") or {}).get("Main"):
        raise ValueError("The executable must belong to the local main Go module")
    if not packages:
        raise ValueError("Go did not report any packages")
    own_packages = []
    for package in packages:
        if package.get("Standard") is True:
            continue
        if (package.get("Module") or {}).get("Main") is not True:
            raise ValueError(f"Nonstandard dependency: {package.get('ImportPath')}")
        own_packages.append(package["ImportPath"])
    return {
        "stdlib_only": True,
        "package_count": len(packages),
        "local_module_packages": sorted(own_packages),
        "third_party_module_requirements": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--go", default="go", help="Go executable name or path (default: go)")
    parser.add_argument("--report", type=Path,
                        default=TASK_ROOT / "evidence" / "local-validation.json")
    args = parser.parse_args()
    report: dict[str, Any] = {
        "schema_version": 1,
        "validation_kind": "local_reference_solution_validation",
        "actual_harbor_run": False,
        "status": "running",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Trusted reference solution compiled in a temporary directory; frozen public and hidden fixtures",
        "limitations": [
            "Not a Docker or Harbor trial; no Harbor reward or trajectory is produced.",
            "Does not exercise the separate verifier container or Worker security boundary.",
            "Finite fixtures demonstrate tested parity, not equality for every possible input.",
        ],
    }
    exit_code = 0
    try:
        resolved_go = shutil.which(args.go)
        if resolved_go is None:
            raise FileNotFoundError(f"Go executable not found: {args.go}")
        go = str(Path(resolved_go).resolve())
        fixtures, report["fixtures"] = load_fixtures()
        with tempfile.TemporaryDirectory(prefix="titlecase-local-") as scratch:
            temp = Path(scratch)
            candidate_root = temp / "repo"
            candidate_root.mkdir()
            solution = TASK_ROOT / "solution"
            source_files = [solution / "go.mod"] + sorted(
                path for path in solution.glob("*.go") if not path.name.endswith("_test.go")
            )
            if len(source_files) < 2:
                raise ValueError("Missing reference Go module or source files")
            report["solution_files"] = {}
            for source in source_files:
                if source.is_symlink() or not source.is_file():
                    raise ValueError(f"Expected an ordinary reference source file: {source.name}")
                payload = source.read_bytes()
                (candidate_root / source.name).write_bytes(payload)
                report["solution_files"][source.name] = sha256(payload)
            # Never copy Python tooling, fixtures, answer sheets, .git, binaries,
            # or caches into the compilation directory.
            env = os.environ.copy()
            for name in ("GOROOT", "GOFLAGS", "GOWORK", "GOENV", "GOPROXY", "GOSUMDB",
                         "GOVCS", "GOTOOLCHAIN", "GOCACHE", "GOMODCACHE", "GOPATH", "CGO_ENABLED"):
                env.pop(name, None)
            env.update({
                "GOENV": "off", "GOWORK": "off", "GOFLAGS": "-mod=readonly",
                "GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off",
                "GOVCS": "*:off", "CGO_ENABLED": "0",
                "GOCACHE": str(temp / "go-build-cache"),
                "GOMODCACHE": str(temp / "go-module-cache"),
                "GOPATH": str(temp / "go-workspace"),
            })
            report["go_version"] = run([go, "version"], candidate_root, env).stdout.decode().strip()
            report["host_python"] = sys.version.split()[0]
            module = json.loads(run([go, "mod", "edit", "-json"], candidate_root, env).stdout)
            root = json_objects(run([go, "list", "-buildvcs=false", "-json", "."], candidate_root, env).stdout)
            packages = json_objects(run([go, "list", "-buildvcs=false", "-deps", "-json", "./..."], candidate_root, env).stdout)
            report["dependency_audit"] = audit_dependencies(module, root, packages)
            run([go, "build", "-buildvcs=false", "./..."], candidate_root, env)
            binary = temp / ("titlecase-candidate.exe" if os.name == "nt" else "titlecase-candidate")
            run([go, "build", "-buildvcs=false", "-o", str(binary), "."], candidate_root, env)
            report["build_passed"] = True
            report["copied_runtime_source_has_no_python_files"] = not any(candidate_root.rglob("*.py"))
            report["corpora"] = {}
            for label, input_name, expected_name in (
                ("public", "inputs.txt", "expected.txt"),
                ("hidden", "hidden_inputs.txt", "hidden_expected.txt"),
            ):
                payload = fixtures[input_name]
                expected = fixtures[expected_name]
                expected_records = records(expected, expected_name)
                result = run([str(binary)], candidate_root, env, stdin=payload, timeout=60)
                actual_records = records(result.stdout, f"{label} actual output")
                matches = sum(left == right for left, right in zip(actual_records, expected_records))
                exact = result.stdout == expected
                report["corpora"][label] = {
                    "input_records": CASE_COUNT,
                    "input_nul_bytes": payload.count(b"\0"),
                    "output_records": len(actual_records),
                    "matched_records": matches,
                    "local_match_fraction": matches / CASE_COUNT,
                    "exact_output_bytes": exact,
                    "output_sha256": sha256(result.stdout),
                }
                if not exact or len(actual_records) != CASE_COUNT or matches != CASE_COUNT:
                    raise AssertionError(f"{label}: expected 2000/2000 matches and identical complete output bytes")
                # The frozen final records are nonempty, so removing just the
                # last LF preserves the same sequence of input records.
                if payload.endswith(b"\n\n"):
                    raise ValueError(f"{label}: choose a nonempty final record for the unterminated-input check")
                without_final_lf = run([str(binary)], candidate_root, env,
                                       stdin=payload[:-1], timeout=60)
                if without_final_lf.stdout != expected:
                    raise AssertionError(f"{label}: unterminated final input record changed output bytes")
                report["corpora"][label]["unterminated_final_record_passed"] = True
                print(f"LOCAL {label}: {matches}/{CASE_COUNT} records match exactly")
            empty = run([str(binary)], candidate_root, env, stdin=b"", timeout=10)
            if empty.stdout != b"":
                raise AssertionError("Empty input must produce empty output")
            report["empty_input_stream_passed"] = True
            report["total_frozen_records"] = 2 * CASE_COUNT
            report["status"] = "passed"
    except (OSError, ValueError, KeyError, TypeError, AssertionError, RuntimeError,
            subprocess.SubprocessError) as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(f"LOCAL validation failed: {exc}", file=sys.stderr)
        exit_code = 1
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Local validation report: {args.report}")
    print("This result is local validation, not a Harbor trial or reward.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
