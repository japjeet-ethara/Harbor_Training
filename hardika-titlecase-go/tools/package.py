import argparse
import hashlib
import stat
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "hardika-titlecase-go"
MANIFEST = "SHA256SUMS"
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".exe", ".dll", ".pyc", ".pyo", ".whl", ".pyd", ".key", ".pem"}


def sources():
    for file in sorted(ROOT.rglob("*")):
        relative = file.relative_to(ROOT)
        if (set(relative.parts) & EXCLUDED_PARTS or relative.name == MANIFEST
                or relative.parts[0] == "jobs"):
            continue
        if file.is_symlink():
            raise ValueError(f"Unexpected symlink {relative}")
        if file.is_file():
            if relative.suffix in EXCLUDED_SUFFIXES or relative.name == ".env":
                raise ValueError(f"Unexpected build or credential artifact {relative}")
            yield relative.as_posix(), file.read_bytes()


def archive_member(output, name, data):
    item = ZipInfo(f"{ARCHIVE_ROOT}/{name}")
    item.create_system = 3
    mode = 0o755 if name.endswith(".sh") else 0o644
    item.external_attr = (stat.S_IFREG | mode) << 16
    output.writestr(item, data, compress_type=ZIP_DEFLATED, compresslevel=9)


def package(destination):
    files = dict(sources())
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    manifest = "".join(f"{digest}  {name}\n" for name, digest in hashes.items()).encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w") as output:
        for name, data in files.items():
            archive_member(output, name, data)
        archive_member(output, MANIFEST, manifest)

    with ZipFile(destination) as output:
        assert output.testzip() is None
        assert set(output.namelist()) == {f"{ARCHIVE_ROOT}/{name}" for name in (*files, MANIFEST)}
        assert output.read(f"{ARCHIVE_ROOT}/{MANIFEST}") == manifest
        for name, digest in hashes.items():
            assert hashlib.sha256(output.read(f"{ARCHIVE_ROOT}/{name}")).hexdigest() == digest

    print(f"Archive passed CRC and SHA-256 verification for {len(files)} files.")
    print(hashlib.sha256(destination.read_bytes()).hexdigest(), destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    package(args.output.resolve())
