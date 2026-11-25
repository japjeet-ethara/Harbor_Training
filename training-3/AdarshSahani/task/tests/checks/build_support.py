"""Secure source staging and bounded unprivileged Go builds for the verifier."""

from __future__ import annotations

import fnmatch
import logging
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path, PurePosixPath

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from process_supervisor import (
    SupervisorError,
    run_supervised_process,
    terminate_process_group,
)


LOGGER = logging.getLogger(__name__)
NOBODY_UID = 65534
NOBODY_GID = 65534
BUILD_TIMEOUT_SEC = 180
BUILD_CPU_LIMIT_SEC = 120
BUILD_FILE_LIMIT_BYTES = 512 << 20
TERMINATE_GRACE_SEC = 0.5
MAX_SOURCE_DEPTH = 64
MAX_SOURCE_ENTRIES = 20_000
MAX_SOURCE_FILE_BYTES = 32 << 20
MAX_STAGED_BYTES = 256 << 20
_DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
_FILE_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


def _limit_build_process() -> None:
    """Bound build subprocess resources; the container caps aggregate memory/disk."""
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (BUILD_CPU_LIMIT_SEC, BUILD_CPU_LIMIT_SEC))
    resource.setrlimit(resource.RLIMIT_FSIZE, (BUILD_FILE_LIMIT_BYTES, BUILD_FILE_LIMIT_BYTES))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _go_build_commands(output_directory: Path, output_binary: Path | None,
                       packages: list[str]) -> list[list[str]]:
    # `go build -o <directory> ./...` only emits executable packages and can
    # skip compiling libraries. Build each listed package to a private output
    # file so malformed non-root packages cannot pass the build gate.
    commands = [
        ["go", "build", "-o", str(output_directory / f"package-{index}"), package]
        for index, package in enumerate(packages)
    ]
    if output_binary is not None:
        # The task requires every package to build. Behavior also needs a root
        # executable, so compile that package only after the full check passes.
        commands.append(["go", "build", "-o", str(output_binary), "."])
    return commands


def _safe_relative_path(path: PurePosixPath) -> bool:
    return not path.is_absolute() and bool(path.parts) and all(part not in {"", ".", ".."} for part in path.parts)


def _open_directory_at(parent_fd: int, name: str, expected: os.stat_result | None = None) -> int:
    """Open one directory component without following a symlink."""
    try:
        descriptor = os.open(name, _DIR_FLAGS, dir_fd=parent_fd)
    except OSError as exc:
        raise ValueError(f"unsafe or changed source directory: {name}") from exc
    info = os.fstat(descriptor)
    if not stat.S_ISDIR(info.st_mode) or (
        expected is not None and (info.st_dev, info.st_ino) != (expected.st_dev, expected.st_ino)
    ):
        os.close(descriptor)
        raise ValueError(f"source directory changed during staging: {name}")
    return descriptor


def _mount_id(descriptor: int) -> int:
    """Read Linux's mount ID for an already-open descriptor (including bind mounts)."""
    try:
        for line in Path(f"/proc/self/fdinfo/{descriptor}").read_text(encoding="ascii").splitlines():
            if line.startswith("mnt_id:"):
                return int(line.partition(":")[2].strip())
    except (OSError, ValueError) as exc:
        raise ValueError("cannot verify source mount identity") from exc
    raise ValueError("source descriptor has no verifiable mount identity")


def _same_file_snapshot(actual: os.stat_result, expected: os.stat_result) -> bool:
    return (
        actual.st_dev == expected.st_dev
        and actual.st_ino == expected.st_ino
        and actual.st_mode == expected.st_mode
        and actual.st_nlink == expected.st_nlink
        and actual.st_size == expected.st_size
        and actual.st_mtime_ns == expected.st_mtime_ns
        and actual.st_ctime_ns == expected.st_ctime_ns
    )


def _open_regular_file(root_fd: int, relative: PurePosixPath,
                       entry_info: dict[PurePosixPath, os.stat_result]) -> int:
    """Open a regular file beneath root_fd, rejecting symlinks in every component."""
    if not _safe_relative_path(relative):
        raise ValueError(f"unsafe source path: {relative}")
    parent_fd = os.dup(root_fd)
    root_device = os.fstat(root_fd).st_dev
    try:
        root_mount = _mount_id(root_fd)
        parent = PurePosixPath(".")
        for component in relative.parts[:-1]:
            parent = parent / component
            child_fd = _open_directory_at(parent_fd, component, entry_info[parent])
            try:
                if os.fstat(child_fd).st_dev != root_device or _mount_id(child_fd) != root_mount:
                    raise ValueError(f"mounted source directory is not allowed: {relative}")
            except BaseException:
                os.close(child_fd)
                raise
            os.close(parent_fd)
            parent_fd = child_fd
        try:
            file_fd = os.open(relative.parts[-1], _FILE_FLAGS, dir_fd=parent_fd)
        except OSError as exc:
            raise ValueError(f"unsafe or changed source file: {relative}") from exc
        try:
            opened_info = os.fstat(file_fd)
            if not stat.S_ISREG(opened_info.st_mode):
                raise ValueError(f"source is not a regular file: {relative}")
            if (opened_info.st_nlink != 1 or opened_info.st_dev != root_device
                    or _mount_id(file_fd) != root_mount):
                raise ValueError(f"linked or mounted source file is not allowed: {relative}")
            if not _same_file_snapshot(opened_info, entry_info[relative]):
                raise ValueError(f"source file changed during staging: {relative}")
        except BaseException:
            os.close(file_fd)
            raise
        return file_fd
    finally:
        os.close(parent_fd)


def _inventory_source(root_fd: int) -> tuple[
        set[PurePosixPath], set[PurePosixPath], dict[PurePosixPath, os.stat_result]]:
    """Bounded iterative inventory; fail closed on links and special files."""
    files: set[PurePosixPath] = set()
    directories: set[PurePosixPath] = {PurePosixPath(".")}
    entry_info: dict[PurePosixPath, os.stat_result] = {PurePosixPath("."): os.fstat(root_fd)}
    root_device = os.fstat(root_fd).st_dev
    root_mount = _mount_id(root_fd)
    entry_count = 0

    root_copy = os.dup(root_fd)
    try:
        root_iterator = os.scandir(root_copy)
    except BaseException:
        os.close(root_copy)
        raise
    pending: list[tuple[int, PurePosixPath, os.ScandirIterator]] = [
        (root_copy, PurePosixPath("."), root_iterator)
    ]
    try:
        while pending:
            directory_fd, prefix, iterator = pending[-1]
            try:
                item = next(iterator)
            except StopIteration:
                iterator.close()
                os.close(directory_fd)
                pending.pop()
                continue

            name = item.name
            if not prefix.parts and name == ".git":
                continue
            entry_count += 1
            if entry_count > MAX_SOURCE_ENTRIES:
                raise ValueError("submitted source exceeds the entry-count limit")
            relative = PurePosixPath(name) if not prefix.parts else prefix / name
            depth = len(relative.parts)
            if depth > MAX_SOURCE_DEPTH:
                raise ValueError(f"submitted source exceeds the directory-depth limit: {relative}")
            entry = item.stat(follow_symlinks=False)
            if stat.S_ISLNK(entry.st_mode):
                raise ValueError(f"symlink in submitted source tree: {relative}")
            if entry.st_dev != root_device:
                raise ValueError(f"mounted filesystem in submitted source tree: {relative}")
            if stat.S_ISDIR(entry.st_mode):
                child_fd = _open_directory_at(directory_fd, name, entry)
                try:
                    if os.fstat(child_fd).st_dev != root_device or _mount_id(child_fd) != root_mount:
                        raise ValueError(f"mounted source directory is not allowed: {relative}")
                    child_iterator = os.scandir(child_fd)
                except BaseException:
                    os.close(child_fd)
                    raise
                directories.add(relative)
                entry_info[relative] = entry
                pending.append((child_fd, relative, child_iterator))
            elif stat.S_ISREG(entry.st_mode):
                if entry.st_nlink != 1:
                    raise ValueError(f"hard-linked source file is not allowed: {relative}")
                if entry.st_size > MAX_SOURCE_FILE_BYTES:
                    raise ValueError(f"source file exceeds the individual-size limit: {relative}")
                files.add(relative)
                entry_info[relative] = entry
            else:
                raise ValueError(f"unsupported file type in submitted source tree: {relative}")
    except BaseException:
        for pending_fd, _pending_path, iterator in pending:
            try:
                iterator.close()
            except OSError:
                pass
            try:
                os.close(pending_fd)
            except OSError:
                pass
        raise
    return files, directories, entry_info


def _open_workspace_root(source: Path) -> tuple[Path, int]:
    """Resolve and open the workspace while refusing symlinked path components."""
    absolute = Path(os.path.abspath(source))
    canonical = Path(os.path.realpath(absolute))
    if canonical != absolute:
        raise ValueError("submitted workspace path contains a symlink component")
    descriptor = os.open(absolute.anchor, _DIR_FLAGS)
    try:
        for component in absolute.parts[1:]:
            child_fd = _open_directory_at(descriptor, component)
            os.close(descriptor)
            descriptor = child_fd
        return canonical, descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _copy_one(root_fd: int, relative: PurePosixPath, destination: Path,
              entry_info: dict[PurePosixPath, os.stat_result], staged_bytes: int) -> int:
    """Copy a bounded snapshot from a securely opened descriptor."""
    expected = entry_info[relative]
    if expected.st_size > MAX_SOURCE_FILE_BYTES:
        raise ValueError(f"source file exceeds the individual-size limit: {relative}")
    if staged_bytes + expected.st_size > MAX_STAGED_BYTES:
        raise ValueError("submitted Go sources exceed the aggregate staging limit")
    source_fd = _open_regular_file(root_fd, relative, entry_info)
    target = destination.joinpath(*relative.parts)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with os.fdopen(source_fd, "rb") as source_file, target.open("wb") as target_file:
            copied = 0
            while copied < expected.st_size:
                chunk = source_file.read(min(1 << 20, expected.st_size - copied))
                if not chunk:
                    raise ValueError(f"source file shortened during staging: {relative}")
                target_file.write(chunk)
                copied += len(chunk)
            if source_file.read(1):
                raise ValueError(f"source file grew during staging: {relative}")
            if not _same_file_snapshot(os.fstat(source_file.fileno()), expected):
                raise ValueError(f"source file changed during staging: {relative}")
        target.chmod(0o444)
        return expected.st_size
    except BaseException:
        try:
            os.close(source_fd)
        except OSError:
            pass
        try:
            target.unlink()
        except OSError:
            pass
        raise


def _path_pattern_matches(pattern: str, candidate: PurePosixPath) -> bool:
    pattern_parts = PurePosixPath(pattern).parts
    return len(pattern_parts) == len(candidate.parts) and all(
        fnmatch.fnmatchcase(part, pattern_part)
        for pattern_part, part in zip(pattern_parts, candidate.parts)
    )


def _visible_embed_path(path: PurePosixPath, *, include_hidden: bool) -> bool:
    return include_hidden or not any(part.startswith((".", "_")) for part in path.parts)


def _embed_files(destination: Path, files: set[PurePosixPath],
                 directories: set[PurePosixPath], go_files: list[PurePosixPath]) -> set[PurePosixPath]:
    """Expand embed patterns only against the already validated in-tree inventory."""
    selected: set[PurePosixPath] = set()
    directive = re.compile(r"^\s*//go:embed\s+(.+?)\s*$")
    for go_file in go_files:
        staged_go_file = destination.joinpath(*go_file.parts)
        for line in staged_go_file.read_text(encoding="utf-8").splitlines():
            match = directive.match(line)
            if not match:
                continue
            try:
                patterns = shlex.split(match.group(1), comments=False, posix=True)
            except ValueError as exc:
                raise ValueError(f"invalid go:embed directive in {go_file}") from exc
            for raw_pattern in patterns:
                pattern = raw_pattern.strip("`")
                include_hidden = pattern.startswith("all:")
                if include_hidden:
                    pattern = pattern[4:]
                if "\\" in pattern:
                    raise ValueError(f"invalid go:embed path in {go_file}")
                embed_path = PurePosixPath(pattern)
                if embed_path.is_absolute() or ".." in embed_path.parts:
                    raise ValueError(f"unsafe go:embed path in {go_file}")

                package_dir = go_file.parent
                candidates = files | directories
                matches: list[PurePosixPath] = []
                for item in candidates:
                    try:
                        relative_item = item.relative_to(package_dir)
                    except ValueError:
                        continue
                    if _path_pattern_matches(pattern, relative_item):
                        matches.append(item)
                if not matches:
                    raise ValueError(f"go:embed pattern matched no submitted source path in {go_file}")
                for matched in matches:
                    if matched in files:
                        selected.add(matched)
                    else:
                        for file_path in files:
                            try:
                                beneath = file_path.relative_to(matched)
                            except ValueError:
                                continue
                            if _visible_embed_path(beneath, include_hidden=include_hidden):
                                selected.add(file_path)
    return selected


def copy_go_sources(source: Path, destination: Path) -> None:
    """Copy only Go build inputs after a no-symlink descriptor-based walk."""
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ValueError("secure source staging requires POSIX O_NOFOLLOW and O_DIRECTORY")
    canonical_root, root_fd = _open_workspace_root(source)
    try:
        files, directories, entry_info = _inventory_source(root_fd)
        go_files = sorted(path for path in files if path.suffix == ".go")
        if not go_files:
            raise ValueError("no Go source files found")

        selected = {
            path for path in files
            if path.name in {"go.mod", "go.sum"} or path.suffix in {".go", ".syso", ".s"}
        }
        selected.update(path for path in files if "vendor" in path.parts)
        destination.mkdir(parents=True, exist_ok=True)
        staged_bytes = 0
        for relative in sorted(selected, key=lambda path: path.as_posix()):
            staged_bytes += _copy_one(root_fd, relative, destination, entry_info, staged_bytes)

        embeds = _embed_files(destination, files, directories, go_files)
        for relative in sorted(embeds - selected, key=lambda path: path.as_posix()):
            staged_bytes += _copy_one(root_fd, relative, destination, entry_info, staged_bytes)

        for current, _dirs, _names in os.walk(destination, topdown=False):
            Path(current).chmod(0o555)
    finally:
        os.close(root_fd)


def run_unprivileged_go_build(source: Path, *, output_binary: Path | None = None,
                              timeout: int = BUILD_TIMEOUT_SEC) -> bool:
    """Validate all packages and optionally build the root executable as nobody."""
    if os.name != "posix" or os.geteuid() != 0:
        LOGGER.error("unprivileged Go build requires a root verifier on POSIX")
        return False
    try:
        with tempfile.TemporaryDirectory(prefix="titlecase-build-") as temporary:
            root = Path(temporary)
            staged = root / "src"
            writable = root / "work"
            cache = writable / "gocache"
            modcache = writable / "gomodcache"
            outdir = writable / "out"
            copy_go_sources(source, staged)
            for directory in (cache, modcache, outdir):
                directory.mkdir(parents=True, exist_ok=True)
                os.chown(directory, NOBODY_UID, NOBODY_GID)
                directory.chmod(0o700)
            os.chmod(root, 0o755)
            env = {
                "PATH": "/usr/local/go/bin:/usr/bin:/bin",
                "HOME": str(writable),
                "GOCACHE": str(cache),
                "GOMODCACHE": str(modcache),
                "GOPATH": str(writable / "gopath"),
                "GOPROXY": "off",
                "GOSUMDB": "off",
                "GOTOOLCHAIN": "local",
                "GOWORK": "off",
                "CGO_ENABLED": "0",
                "GOMEMLIMIT": "1GiB",
                "GOFLAGS": "-buildvcs=false",
                "LANG": "C.UTF-8",
            }
            go_mod = staged / "go.mod"
            if go_mod.is_file():
                module_text = go_mod.read_text(encoding="utf-8")
                go_version = re.search(r"(?m)^go\s+(\d+)\.(\d+)", module_text)
                vendor_default = bool(
                    (staged / "vendor").is_dir()
                    and go_version
                    and tuple(map(int, go_version.groups())) >= (1, 14)
                )
                env["GOFLAGS"] += " -mod=vendor" if vendor_default else " -mod=readonly"
            deadline = time.monotonic() + timeout
            package_listing = writable / "packages.txt"
            with package_listing.open("wb") as listing:
                remaining = max(0.0, deadline - time.monotonic())
                returncode = run_supervised_process(
                    ["go", "list", "-f", "{{if .GoFiles}}{{.ImportPath}}{{end}}", "./..."],
                    timeout=remaining, cwd=staged, env=env,
                    stdin=subprocess.DEVNULL, stdout=listing, stderr=subprocess.DEVNULL,
                    user=NOBODY_UID, group=NOBODY_GID, extra_groups=(),
                    preexec_fn=_limit_build_process,
                )
            if returncode != 0:
                LOGGER.error("Go package discovery failed with exit status %s", returncode)
                return False
            packages = [
                line for line in package_listing.read_text(encoding="utf-8").splitlines()
                if line
            ]
            if not packages or len(packages) > MAX_SOURCE_ENTRIES:
                LOGGER.error("Go package discovery returned an invalid package count")
                return False
            commands = _go_build_commands(
                outdir, outdir / "candidate" if output_binary is not None else None,
                packages,
            )
            for args in commands:
                remaining = max(0.0, deadline - time.monotonic())
                returncode = run_supervised_process(
                    args, timeout=remaining,
                    cwd=staged, env=env, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    user=NOBODY_UID, group=NOBODY_GID, extra_groups=(),
                    preexec_fn=_limit_build_process,
                )
                if returncode is None:
                    LOGGER.error("Go build timed out after %s seconds", timeout)
                    return False
                if returncode != 0:
                    LOGGER.error("Go build failed with exit status %s", returncode)
                    return False
            if output_binary is not None:
                built = outdir / "candidate"
                if not built.is_file():
                    LOGGER.error("Go build succeeded without producing the candidate binary")
                    return False
                shutil.copyfile(built, output_binary)
                output_binary.chmod(0o755)
            return True
    except (OSError, ValueError, subprocess.SubprocessError, SupervisorError) as exc:
        LOGGER.error("Go build staging failed: %s", exc)
        return False
