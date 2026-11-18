import datetime
import hashlib
import json
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parents[1] / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)
ARCHIVE = OUT / 'komal-titlecase-go.zip'
PREFIX = 'komal-titlecase-go/'
SKIP_PARTS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', 'node_modules'}
SKIP_SUFFIXES = {'.pyc', '.pyo', '.exe', '.dll', '.so', '.whl'}
excluded = []
included = []
for path in sorted(ROOT.rglob('*')):
    if not path.is_file():
        continue
    relative = path.relative_to(ROOT)
    if path.name in ('SHA256SUMS.json', 'packaging-report.json'):
        continue
    reason = None
    if any(p in SKIP_PARTS for p in relative.parts):
        reason = 'cache or environment'
    elif 'artifacts' in relative.parts and path.name != 'manifest.json':
        reason = 'redundant Harbor-collected candidate artifact'
    elif path.suffix.lower() in SKIP_SUFFIXES:
        reason = 'binary or package cache'
    elif path.name in ('.env', 'credentials', 'credentials.json') or path.suffix == '.pem':
        reason = 'credential path'
    if reason:
        excluded.append(dict(path=relative.as_posix(), reason=reason))
        continue
    data = path.read_bytes()
    assert not data.startswith(b'\x7fELF') and not data.startswith(b'MZ'), relative
    for pattern in [rb'sk-[a-zA-Z0-9_-]{32,}', rb'gh[pousr]_[a-zA-Z0-9]{30,}', rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----']:
        assert not re.search(pattern, data), 'Potential credential in ' + str(relative)
    if path.suffix == '.sh':
        assert b'\r' not in data, relative
        assert data.startswith(b'#!/'), relative
    included.append((relative.as_posix(), data))
required = ['README.md', 'NOTES.md', 'ACCEPTANCE.md', 'VALIDATION.md', 'PATTERN_ENGINE.md', 'DATASET.md',
            'GRADING.md', 'WINDOWS_WSL.md', 'LICENSE', 'ATTRIBUTION.md',
            'titlecase-go/tests/data/inputs.txt', 'titlecase-go/tests/data/expected.txt',
            'titlecase-go/tests/data/hidden_inputs.txt', 'titlecase-go/tests/data/hidden_expected.txt',
            'evidence/screenshots/oracle.jpg', 'evidence/screenshots/nop.jpg', 'evidence/screenshots/replay-cheat.jpg']
names = {name for name, _ in included}
assert all(name in names for name in required)
hashes = {name: hashlib.sha256(data).hexdigest() for name,data in included}
manifest = json.dumps(hashes, indent=2, sort_keys=True).encode() + b'\n'
report = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              payload_files=len(included), crc_integrity='verified by ZipFile.testzip during packaging',
              extracted_bytes='verified against every payload SHA-256 during packaging',
              scripts={name:'0755' for name,data in included if name.endswith('.sh')},
              non_scripts_mode='0644', credentials_scan='no configured credential signatures found',
              excluded=excluded,
              notes='Collected candidate trees omitted; raw Harbor logs, rewards, configs and manifests retained. No binaries redistributed.')
report_data = json.dumps(report, indent=2, sort_keys=True).encode() + b'\n'
included += [('SHA256SUMS.json', manifest), ('packaging-report.json', report_data)]
with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name, data in included:
        info = zipfile.ZipInfo(PREFIX + name, (2026, 11, 18, 0, 0, 0))
        info.create_system = 3
        mode = 0o755 if name.endswith('.sh') else 0o644
        info.external_attr = (stat.S_IFREG | mode) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, data)
with zipfile.ZipFile(ARCHIVE) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(set(archive.namelist()))
    with tempfile.TemporaryDirectory() as temp:
        archive.extractall(temp)
        for name, expected in hashes.items():
            assert hashlib.sha256((Path(temp) / PREFIX / name).read_bytes()).hexdigest() == expected, name
        for info in archive.infolist():
            if info.filename.endswith('.sh'):
                assert stat.S_IMODE(info.external_attr >> 16) == 0o755
digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
(OUT / 'komal-titlecase-go.zip.sha256').write_text(digest + '  komal-titlecase-go.zip\n', encoding='ascii')
result = dict(archive=ARCHIVE.name, sha256=digest, bytes=ARCHIVE.stat().st_size,
              files=len(included), excluded_files=len(excluded), integrity=True,
              extracted_hashes_match=True, executable_modes_verified=True)
(OUT / 'archive-verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
