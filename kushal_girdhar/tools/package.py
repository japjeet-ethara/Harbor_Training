import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path, PurePosixPath
import stat
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
TOP = "kushal-titlecase-go"
MANIFEST = "SHA256SUMS"
EXCLUDED = {".git", ".venv", "venv", "__pycache__", ".cache", ".env", "node_modules"}
BINARY = {".exe", ".dll", ".pyc", ".pyo", ".so", ".whl", ".pyd", ".a"}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def safe(name):
    path = PurePosixPath(name)
    return (
        len(path.parts) >= 1 and path.as_posix() == name and not path.is_absolute()
        and not any(p in EXCLUDED or p in (".", "..") for p in path.parts)
        and not any(ch in name for ch in "\\:\r\n\0")
        and path.suffix.lower() not in BINARY
    )


def files():
    contents = {}
    for path in sorted(ROOT.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"unexpected symlink: {path}")
        if path.is_dir():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative == MANIFEST:
            continue
        if not safe(relative):
            raise ValueError(f"unexpected staged file: {relative}")
        contents[relative] = (path, path.read_bytes())
    return contents


def build(destination):
    destination = destination.resolve()
    if destination.is_relative_to(ROOT):
        raise ValueError("use an output path outside the source tree")
    entries = files()
    manifest = "".join(f"{digest(payload)}  {name}\n" for name, (_, payload) in entries.items())
    manifest_path = ROOT / MANIFEST
    manifest_path.write_bytes(manifest.encode("utf-8"))
    entries[MANIFEST] = (manifest_path, manifest.encode("utf-8"))
    with ZipFile(destination, "x", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, (path, payload) in sorted(entries.items()):
            recorded = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            info = ZipInfo(f"{TOP}/{name}", date_time=recorded.timetuple()[:6])
            info.create_system = 3
            mode = 0o755 if name.endswith(".sh") else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(info, payload, compress_type=ZIP_DEFLATED, compresslevel=9)
    verify(destination)


def verify(source):
    with ZipFile(source) as archive:
        assert archive.testzip() is None, "ZIP CRC failure"
        names = archive.namelist()
        assert len(names) == len(set(names)), "duplicate ZIP paths"
        assert all(name.startswith(f"{TOP}/") and safe(name.split("/", 1)[1]) for name in names)
        manifest = archive.read(f"{TOP}/{MANIFEST}").decode("utf-8")
        rows = [entry.split("  ", 1) for entry in manifest.splitlines()]
        assert len(rows) == len({name for _, name in rows}), "duplicate manifest paths"
        assert set(names) == {f"{TOP}/{MANIFEST}"} | {f"{TOP}/{name}" for _, name in rows}
        for expected, name in rows:
            assert digest(archive.read(f"{TOP}/{name}")) == expected, f"SHA-256 mismatch: {name}"
        assert all(
            stat.S_ISREG(info.external_attr >> 16)
            and (not info.filename.endswith(".sh") or bool(info.external_attr & (0o111 << 16)))
            for info in archive.infolist()
        )
    print(f"ZIP CRC and {len(rows)} manifest SHA-256 checks passed")
    print(f"ZIP SHA-256 {digest(source.read_bytes())}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    (build if args.action == "build" else verify)(args.archive)


if __name__ == "__main__":
    main()
