"""Build a self-contained skill archive from the repository source tree."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'contract_check'
SKILL = ROOT / 'skill'
WRAPPER = '''#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_check.cli import main
raise SystemExit(main())
'''


def _write(archive, path, content):
    info = ZipInfo(path, (2026, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, content)


def build(output, edition_year=None):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_relative_to(ROOT):
        raise ValueError('write archives outside the source tree')
    files = []
    for base, target in [(SKILL, ''), (PACKAGE, 'scripts/contract_check/')]:
        for path in sorted(base.rglob('*')):
            if path.is_file() and path.suffix not in ('.pyc',) and '__pycache__' not in path.parts:
                files.append((path, 'contract-check/' + target + path.relative_to(base).as_posix()))
    manifest = {'name': 'contract-check', 'edition_year': edition_year or date.today().year,
                'release_status': 'development; lawyer review pending',
                'files': {}}
    with ZipFile(output, 'w') as archive:
        for path, target in files:
            content = path.read_bytes()
            _write(archive, target, content)
            manifest['files'][target.removeprefix('contract-check/')] = hashlib.sha256(content).hexdigest()
        _write(archive, 'contract-check/scripts/contract_check_cli.py', WRAPPER.encode())
        manifest['files']['scripts/contract_check_cli.py'] = hashlib.sha256(WRAPPER.encode()).hexdigest()
        _write(archive, 'contract-check/edition-manifest.json', (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode())
    return [target for _, target in files] + ['contract-check/scripts/contract_check_cli.py', 'contract-check/edition-manifest.json']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output')
    parser.add_argument('--edition-year', type=int)
    args = parser.parse_args()
    print('\n'.join(build(args.output, args.edition_year)))
