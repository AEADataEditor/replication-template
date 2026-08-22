#!/usr/bin/env python3
"""Tests for jira_get_info.py. Run: python3 tools/test_jira_get_info.py"""
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_get_info as jgi


class TestGetBoxFolderId(unittest.TestCase):
    FIELD_MAP = {"Restricted data Box Folder ID": "customfield_99999"}

    def _issue(self, value):
        issue = MagicMock()
        setattr(issue.fields, "customfield_99999", value)
        return issue

    def test_returns_stripped_value_when_present(self):
        issue = self._issue("  123456  ")
        self.assertEqual(jgi.get_box_folder_id(issue, self.FIELD_MAP), "123456")

    def test_returns_empty_string_when_none(self):
        issue = self._issue(None)
        self.assertEqual(jgi.get_box_folder_id(issue, self.FIELD_MAP), "")

    def test_returns_empty_string_when_blank(self):
        issue = self._issue("   ")
        self.assertEqual(jgi.get_box_folder_id(issue, self.FIELD_MAP), "")

    def test_returns_empty_string_when_field_unmapped(self):
        issue = self._issue("123456")
        self.assertEqual(jgi.get_box_folder_id(issue, {}), "")


class TestKeywordRouting(unittest.TestCase):
    def test_boxfolderid_keyword_is_routed(self):
        field_map = TestGetBoxFolderId.FIELD_MAP
        issue = MagicMock()
        setattr(issue.fields, "customfield_99999", "654321")

        jira = MagicMock()
        jira.issue.return_value = issue
        jira.fields.return_value = [
            {"name": "Restricted data Box Folder ID", "id": "customfield_99999"}
        ]

        with unittest.mock.patch.object(jgi, "get_jira_client", return_value=jira):
            result = jgi.get_info_from_jira("AEAREP-1", "boxfolderid")

        self.assertEqual(result, "654321")


if __name__ == "__main__":
    unittest.main()
