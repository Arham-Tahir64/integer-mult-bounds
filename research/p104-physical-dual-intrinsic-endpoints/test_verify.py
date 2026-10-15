"""Behavioral controls for exported replay, source integrity and receipt claims."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('intrinsic_verify', P / 'verify.py')
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)


class ReplayTests(unittest.TestCase):
    def export(self, root):
        package = root / 'research' / P.name
        shutil.copytree(P, package, ignore=shutil.ignore_patterns('__pycache__'))
        for item in V.read_json(P / 'SOURCES.json')['files']:
            if item['usage'] == 'input':
                target = root / item['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((V.ROOT / item['path']).read_bytes())
        return package

    def test_git_free_replay_and_adapter_export(self):
        with tempfile.TemporaryDirectory(prefix='p104-intrinsic-export-') as directory:
            root = Path(directory)
            package = self.export(root)
            out = root / 'adapters.json'
            result = subprocess.run([sys.executable, '-I', '-O', '-B', str(package / 'verify.py'),
                                     '--adapters-out', str(out)], cwd=root,
                                    capture_output=True, text=True, timeout=480)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('PASS_P104_PHYSICAL_DUAL_INTRINSIC_ENDPOINTS', result.stdout)
            self.assertFalse((root / '.git').exists())
            self.assertEqual(len(json.loads(out.read_bytes())), 208)
            expected = V.read_json(P / 'RESULT.json')
            self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(), expected['adapter_records_sha256'])

    def test_live_executable_corruption_before_execution(self):
        with tempfile.TemporaryDirectory(prefix='p104-intrinsic-source-control-') as directory:
            root = Path(directory)
            package = self.export(root)
            marker = root / 'executed.txt'
            target = root / V.BASE / 'vendor/native_verify.py'
            target.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("bad")\n')
            with patch.object(V, 'ROOT', root), patch.object(V, 'P', package):
                with self.assertRaisesRegex(ValueError, 'source SHA256'):
                    V.authenticate()
            self.assertFalse(marker.exists())

    def test_retained_archive_corruption(self):
        with tempfile.TemporaryDirectory(prefix='p104-intrinsic-archive-control-') as directory:
            root = Path(directory)
            package = self.export(root)
            archive = package / 'inputs/PR2586.tar.gz'
            raw = bytearray(archive.read_bytes())
            raw[-12] ^= 1
            archive.write_bytes(raw)
            with patch.object(V, 'ROOT', root), patch.object(V, 'P', package):
                with self.assertRaisesRegex(ValueError, 'archive SHA256'):
                    V.authenticate()

    def test_typed_receipt_detects_changed_claims(self):
        result = V.read_json(P / 'RESULT.json')
        V.validate_receipt(result, result)
        for key, value in [('added_rank_mass', 1), ('added_positive_children', False),
                           ('public_roles', 357), ('predecessor_full_replay', 1), ('controls', [])]:
            bad = copy.deepcopy(result)
            bad[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'typed receipt'):
                V.validate_receipt(result, bad)

    def test_duplicate_metadata_key(self):
        with tempfile.TemporaryDirectory(prefix='p104-intrinsic-json-control-') as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{"added_rank_mass":0,"added_rank_mass":1}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                V.read_json(path)

    def test_public_cli_refuses_occupied_outputs(self):
        with tempfile.TemporaryDirectory(prefix='p104-intrinsic-output-control-') as directory:
            path = Path(directory) / 'keep.txt'
            path.write_text('unchanged')
            for option in ('--out', '--adapters-out'):
                result = subprocess.run([sys.executable, '-I', '-O', '-B', str(P / 'verify.py'), option, str(path)],
                                        capture_output=True, text=True, timeout=15)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('exclusive new output', result.stderr)
                self.assertEqual(path.read_text(), 'unchanged')


if __name__ == '__main__':
    unittest.main()
