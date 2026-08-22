#!/usr/bin/env python3
"""Tests for jira_update_deposit_size.py. Run: python3 tools/test_jira_update_deposit_size.py"""
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_update_deposit_size as juds


def _make_zip(path, file_sizes):
    """Create a ZIP at path whose members have the given uncompressed sizes (bytes)."""
    with zipfile.ZipFile(path, "w") as zf:
        for name, size in file_sizes.items():
            zf.writestr(name, b"x" * size)


class TestComputeDepositSizeBytes(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.cwd = self.root / "cwd"
        self.project_dir = self.cwd / "12345"
        self.project_dir.mkdir(parents=True)

    def test_single_inner_zip_wins_over_envelope(self):
        _make_zip(self.cwd / "12345.zip", {"a.txt": 100})  # envelope, should be ignored
        _make_zip(self.project_dir / "data.zip", {"b.txt": 10, "c.txt": 20})

        size, source = juds.compute_deposit_size_bytes(str(self.project_dir), cwd=str(self.cwd))

        self.assertEqual(size, 30)
        self.assertIn("single inner ZIP", source)

    def test_envelope_zip_used_when_no_single_inner_zip(self):
        _make_zip(self.cwd / "12345.zip", {"a.txt": 100, "b.txt": 50})

        size, source = juds.compute_deposit_size_bytes(str(self.project_dir), cwd=str(self.cwd))

        self.assertEqual(size, 150)
        self.assertIn("envelope ZIP", source)

    def test_envelope_ignored_when_multiple_inner_zips(self):
        _make_zip(self.cwd / "12345.zip", {"a.txt": 999})
        _make_zip(self.project_dir / "part1.zip", {"x.txt": 5})
        _make_zip(self.project_dir / "part2.zip", {"y.txt": 7})

        size, source = juds.compute_deposit_size_bytes(str(self.project_dir), cwd=str(self.cwd))

        self.assertEqual(size, 999)
        self.assertIn("envelope ZIP", source)

    def test_on_disk_size_when_no_zip_anywhere(self):
        (self.project_dir / "data.csv").write_bytes(b"x" * 42)
        sub = self.project_dir / "sub"
        sub.mkdir()
        (sub / "more.csv").write_bytes(b"y" * 8)

        size, source = juds.compute_deposit_size_bytes(str(self.project_dir), cwd=str(self.cwd))

        self.assertEqual(size, 50)
        self.assertIn("on-disk size", source)


class TestNormalizeIssueKey(unittest.TestCase):
    def test_bare_number_gets_prefixed(self):
        self.assertEqual(juds.normalize_issue_key("9603"), "AEAREP-9603")

    def test_prefixed_key_is_uppercased(self):
        self.assertEqual(juds.normalize_issue_key("train-2000"), "TRAIN-2000")


class TestResolveFieldId(unittest.TestCase):
    def test_finds_field_by_name(self):
        jira = MagicMock()
        jira.fields.return_value = [
            {"id": "customfield_10028", "name": "Software used"},
            {"id": "customfield_10099", "name": "Deposit size"},
        ]

        self.assertEqual(juds.resolve_field_id(jira, "Deposit size"), "customfield_10099")

    def test_returns_none_when_not_found(self):
        jira = MagicMock()
        jira.fields.return_value = [{"id": "customfield_10028", "name": "Software used"}]

        self.assertIsNone(juds.resolve_field_id(jira, "Deposit size"))


class TestUpdateDepositSizeField(unittest.TestCase):
    def test_overwrites_unconditionally(self):
        jira = MagicMock()
        jira.fields.return_value = [{"id": "customfield_10099", "name": "Deposit size"}]
        issue = MagicMock()
        jira.issue.return_value = issue

        juds.update_deposit_size_field(jira, "AEAREP-1", 12.34)

        issue.update.assert_called_once_with(fields={"customfield_10099": 12.34})

    def test_raises_when_field_missing(self):
        jira = MagicMock()
        jira.fields.return_value = []

        with self.assertRaises(RuntimeError):
            juds.update_deposit_size_field(jira, "AEAREP-1", 12.34)


class TestMain(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project_dir = Path(self._tmp.name) / "12345"
        self.project_dir.mkdir()
        (self.project_dir / "data.csv").write_bytes(b"x" * (2 * juds.BYTES_PER_MB))

    def test_dry_run_without_yes_returns_0_and_makes_no_jira_call(self):
        rc = juds.main([str(1), str(self.project_dir)])
        self.assertEqual(rc, 0)

    def test_missing_project_dir_returns_1(self):
        rc = juds.main(["1", str(self.project_dir / "does-not-exist")])
        self.assertEqual(rc, 1)

    def test_yes_without_credentials_returns_1(self):
        env = dict(os.environ)
        os.environ.pop("JIRA_USERNAME", None)
        os.environ.pop("JIRA_API_KEY", None)
        try:
            rc = juds.main(["1", str(self.project_dir), "--yes"])
        finally:
            os.environ.clear()
            os.environ.update(env)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
