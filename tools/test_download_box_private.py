#!/usr/bin/env python3
"""Tests for download_box_private.py. Run: python3 tools/test_download_box_private.py"""
import argparse
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import download_box_private as dbp


class TestParseArgumentsTargetFolderId(unittest.TestCase):
    def _parse(self, argv):
        with patch.object(sys, "argv", ["download_box_private.py"] + argv):
            return dbp.parse_arguments()

    def test_target_folder_id_defaults_to_none(self):
        args = self._parse([
            "1234",
            "--box-folder-id", "999",
            "--box-key-id", "key",
            "--box-enterprise-id", "ent",
        ])
        self.assertIsNone(args.target_folder_id)

    def test_target_folder_id_is_captured(self):
        args = self._parse([
            "--target-folder-id", "555666",
            "--box-folder-id", "999",
            "--box-key-id", "key",
            "--box-enterprise-id", "ent",
        ])
        self.assertEqual(args.target_folder_id, "555666")

    def test_target_folder_id_makes_subfolder_optional(self):
        # No positional subfolder, no cwd/git-remote match expected to be needed
        # because --target-folder-id makes the subfolder argument moot.
        args = self._parse([
            "--target-folder-id", "555666",
            "--box-folder-id", "999",
            "--box-key-id", "key",
            "--box-enterprise-id", "ent",
        ])
        self.assertEqual(args.target_folder_id, "555666")
        self.assertIsNone(args.subfolder)


class TestResolveTargetFolderId(unittest.TestCase):
    """resolve_target_folder_id() centralizes the direct-ID vs search decision."""

    def test_direct_id_skips_search(self):
        client = MagicMock()
        result = dbp.resolve_target_folder_id(client, target_folder_id="555666", box_folder_id="999", subfolder=None)
        self.assertEqual(result, "555666")
        client.folder.assert_not_called()

    def test_search_used_when_no_target_folder_id(self):
        client = MagicMock()
        folder_items = MagicMock()
        item = MagicMock(type="folder", id="42")
        item.name = "aearep-1234"
        folder_items.get_items.return_value = [item]
        client.folder.return_value = folder_items

        result = dbp.resolve_target_folder_id(client, target_folder_id=None, box_folder_id="999", subfolder="1234")

        self.assertEqual(result, "42")

    def test_search_raises_when_subfolder_not_found(self):
        client = MagicMock()
        folder_items = MagicMock()
        item = MagicMock(type="folder", id="42")
        item.name = "aearep-0000"
        folder_items.get_items.return_value = [item]
        client.folder.return_value = folder_items

        with self.assertRaises(SystemExit):
            dbp.resolve_target_folder_id(client, target_folder_id=None, box_folder_id="999", subfolder="1234")

    def test_prints_box_folder_id_marker(self):
        client = MagicMock()
        buf = io.StringIO()
        with redirect_stdout(buf):
            dbp.resolve_target_folder_id(client, target_folder_id="555666", box_folder_id="999", subfolder=None)
        self.assertIn("BOX_FOLDER_ID=555666", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
