"""Candidate snapshots preserve inputs and reject unsupported filesystem entries."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from temporal_contract_analyzer import candidate_files as files
from temporal_contract_analyzer.core import EvidenceError


class CandidateFileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root/'source'
        self.source.mkdir()

    def test_snapshot_roundtrip_preserves_bytes_modes_tests_and_docs(self):
        for name, raw in {'run.sh': b'#!/bin/sh\n', 'test.py': b'assert True\n',
                          'README.md': b'candidate documentation\n'}.items():
            (self.source/name).write_bytes(raw)
        (self.source/'run.sh').chmod(0o755)
        captured, skipped = files.capture(self.source)
        self.assertEqual(skipped, [])
        modes = files.file_modes(self.source, captured)
        target = self.root/'copy'
        files.write_files(target, captured, modes)
        restored, _ = files.capture(target)
        self.assertEqual(restored, captured)
        self.assertEqual(files.inventory(restored), files.inventory(captured))
        self.assertEqual(files.file_modes(target, restored), modes)
        self.assertEqual(modes['run.sh'], 0o755)
        with self.assertRaises(FileExistsError):
            files.write_files(target, captured, modes)

    def test_hidden_and_dependency_trees_are_excluded(self):
        (self.source/'.env').write_text('synthetic fixture')
        (self.source/'node_modules').mkdir()
        (self.source/'node_modules/dependency.js').write_text('ignored')
        (self.source/'main.py').write_text('value = 1\n')
        captured, skipped = files.capture(self.source)
        self.assertEqual(set(captured), {'main.py'})
        self.assertEqual(skipped, ['.env', 'node_modules/'])

    def test_symlink_files_and_directories_are_rejected(self):
        outside = self.root/'outside'
        outside.mkdir()
        for target in (outside, self.root/'absent'):
            link = self.source/'escape'
            link.symlink_to(target)
            with self.assertRaises(EvidenceError):
                files.capture(self.source)
            link.unlink()

    def test_byte_bound_rejects_incomplete_candidate(self):
        (self.source/'main.py').write_bytes(b'12345')
        with patch.object(files, 'LIMIT', 4), self.assertRaises(EvidenceError):
            files.capture(self.source)
