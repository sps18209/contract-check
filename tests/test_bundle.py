import subprocess
import sys
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from scripts.build_skill import build


class BundleTest(unittest.TestCase):
    def test_extracted_bundle_runs_without_repository(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / 'contract-check.skill'
            build(output)
            with ZipFile(output) as archive:
                archive.extractall(Path(d) / 'release')
            folder = Path(d) / 'release' / 'contract-check'
            self.assertTrue((folder / 'SKILL.md').exists())
            manifest = json.loads((folder / 'edition-manifest.json').read_text())
            self.assertIn('lawyer review pending', manifest['release_status'])
            self.assertIn('scripts/contract_check/core.py', manifest['files'])
            source = folder / 'sample.txt'
            source.write_text('1. Fees\n\nPayment is due.', encoding='utf-8')
            command = [sys.executable, str(folder / 'scripts' / 'contract_check_cli.py')]
            result = subprocess.run(command + ['ingest', str(source), str(folder / 'project.json')],
                                    cwd=d, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((folder / 'project.json').exists())
