"""Exact-source and rejection controls for the batched Git transport."""
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("batched_research_package", ROOT / "scripts/research_package.py")
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class SourceBlobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        package.git(self.root, "init", "-q")
        self.files = {"binary.bin": bytes(range(256)) + b"\0\nend\n",
                      "empty.txt": b"", "literal [1].txt": b"brackets",
                      "literal 1.txt": b"different", "-leading-option": b"option",
                      "caf\u00e9.txt": b"non-ascii path"}
        for name, data in self.files.items():
            (self.root / name).write_bytes(data)
        package.git(self.root, "add", ".")
        package.git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "maintenance.auto=false", "-c", "gc.auto=0", "commit", "-qm", "fixture")
        self.base = package.git(self.root, "rev-parse", "HEAD").decode().strip()

    def test_exact_bytes_literal_paths_and_duplicate_requests(self):
        names = [*self.files, "binary.bin"]
        with package.source_blobs(self.root, self.base, names) as read:
            for name in names:
                obj, payload = read(name)
                self.assertEqual(payload, self.files[name])
                self.assertEqual(obj, package.git(self.root, "rev-parse", self.base + ":" + name).decode().strip())
                self.assertEqual(payload, package.git(self.root, "show", self.base + ":" + name))

    def test_fresh_readers_follow_new_base_but_preserve_old_base(self):
        with package.source_blobs(self.root, self.base, ["binary.bin"]) as read:
            old = read("binary.bin")
        (self.root / "binary.bin").write_bytes(b"new bytes")
        package.git(self.root, "add", "binary.bin")
        package.git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "maintenance.auto=false", "-c", "gc.auto=0", "commit", "-qm", "new base")
        new_base = package.git(self.root, "rev-parse", "HEAD").decode().strip()
        with package.source_blobs(self.root, new_base, ["binary.bin"]) as read:
            self.assertEqual(read("binary.bin")[1], b"new bytes")
        with package.source_blobs(self.root, self.base, ["binary.bin"]) as read:
            self.assertEqual(read("binary.bin"), old)

    def test_missing_wildcard_and_directory_do_not_substitute_sources(self):
        for name in ("missing.txt", "literal *.txt", "."):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "missing source blob"):
                with package.source_blobs(self.root, self.base, [name]):
                    self.fail("invalid source accepted")

    def test_two_processes_regardless_of_inventory_length(self):
        run, popen = subprocess.run, subprocess.Popen
        with patch.object(package.subprocess, "run", wraps=run) as calls, \
             patch.object(package.subprocess, "Popen", wraps=popen) as processes:
            with package.source_blobs(self.root, self.base, list(self.files) * 8) as read:
                for name in list(self.files) * 8:
                    self.assertEqual(read(name)[1], self.files[name])
            self.assertEqual(calls.call_count, 1)
            self.assertEqual(processes.call_count, 2)  # ls-tree's run plus cat-file

    def protocol_fixture(self, output, code=0):
        obj = b"a" * 40
        tree = b"100644 blob " + obj + b"\tinput\0"
        class Process:
            def __init__(self, *args, **kwargs):
                self.args = ["git", "cat-file", "--batch"]
                self.stdin, self.stdout = io.BytesIO(), io.BytesIO(output)
                self.code, self.killed = None, False
            def poll(self):
                return self.code
            def kill(self):
                self.killed = True
                self.code = -9
            def wait(self):
                if self.code is None:
                    self.code = code
                return self.code
        return tree, Process

    def test_protocol_corruption_is_rejected_and_child_closed(self):
        obj = b"a" * 40
        bad = [b"", obj + b" missing\n", b"b" * 40 + b" blob 1\nx\n",
               obj + b" tree 1\nx\n", obj + b" blob -1\n", obj + b" blob 2\nx",
               obj + b" blob 1\nx!", obj + b" blob 1 extra\nx\n"]
        for output in bad:
            tree, factory = self.protocol_fixture(output)
            child = factory()
            with self.subTest(output=output), patch.object(package, "git", return_value=tree), \
                 patch.object(package.subprocess, "Popen", return_value=child):
                with self.assertRaises(ValueError):
                    with package.source_blobs(self.root, self.base, ["input"]) as read:
                        read("input")
                self.assertTrue(child.killed)
                self.assertTrue(child.stdin.closed and child.stdout.closed)

    def test_nonzero_git_exit_is_rejected_after_valid_payload(self):
        tree, factory = self.protocol_fixture(b"a" * 40 + b" blob 1\nx\n", code=3)
        child = factory()
        with patch.object(package, "git", return_value=tree), \
             patch.object(package.subprocess, "Popen", return_value=child):
            with self.assertRaises(subprocess.CalledProcessError):
                with package.source_blobs(self.root, self.base, ["input"]) as read:
                    self.assertEqual(read("input")[1], b"x")
        self.assertTrue(child.stdin.closed and child.stdout.closed)

    def test_caller_failure_terminates_batch(self):
        popen = subprocess.Popen
        children = []
        def capture(*args, **kwargs):
            child = popen(*args, **kwargs)
            if args[0][1:3] == ["cat-file", "--batch"]:
                children.append(child)
            return child
        with patch.object(package.subprocess, "Popen", side_effect=capture):
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                with package.source_blobs(self.root, self.base, ["binary.bin"]) as read:
                    read("binary.bin")
                    raise ValueError("SHA mismatch")
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())
        self.assertTrue(children[0].stdin.closed and children[0].stdout.closed)


if __name__ == "__main__":
    unittest.main()
