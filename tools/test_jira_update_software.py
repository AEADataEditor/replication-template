#!/usr/bin/env python3
"""Tests for jira_update_software.py. Run: python3 tools/test_jira_update_software.py"""
import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_update_software as jus


class TestLoadCsvLookup(unittest.TestCase):
    def test_loads_real_extension_table(self):
        lookup = jus.load_csv_lookup(jus.DEFAULT_EXT_LOOKUP)
        self.assertEqual(lookup["do"], "Stata")
        self.assertEqual(lookup["ado"], "Stata")
        self.assertEqual(lookup["py"], "Python")
        self.assertNotIn("sh", lookup)
        self.assertNotIn("toml", lookup)

    def test_loads_real_filename_table(self):
        lookup = jus.load_csv_lookup(jus.DEFAULT_NAME_LOOKUP)
        self.assertEqual(lookup["project.toml"], "Julia")
        self.assertEqual(lookup["manifest.toml"], "Julia")


class TestDetectIpynbLanguage(unittest.TestCase):
    def _write_notebook(self, metadata):
        fd, path = tempfile.mkstemp(suffix=".ipynb")
        with os.fdopen(fd, "w") as f:
            json.dump({"metadata": metadata, "cells": []}, f)
        return path

    def test_kernelspec_language(self):
        path = self._write_notebook({"kernelspec": {"language": "python"}})
        try:
            self.assertEqual(jus.detect_ipynb_language(path), "Python")
        finally:
            os.remove(path)

    def test_language_info_fallback(self):
        path = self._write_notebook({"language_info": {"name": "julia"}})
        try:
            self.assertEqual(jus.detect_ipynb_language(path), "Julia")
        finally:
            os.remove(path)

    def test_r_kernel(self):
        path = self._write_notebook({"kernelspec": {"language": "R"}})
        try:
            self.assertEqual(jus.detect_ipynb_language(path), "R")
        finally:
            os.remove(path)

    def test_unrecognized_language_returns_none(self):
        path = self._write_notebook({"kernelspec": {"language": "brainfuck"}})
        try:
            self.assertIsNone(jus.detect_ipynb_language(path))
        finally:
            os.remove(path)

    def test_missing_file_returns_none(self):
        self.assertIsNone(jus.detect_ipynb_language("/nonexistent/path.ipynb"))

    def test_malformed_json_returns_none(self):
        fd, path = tempfile.mkstemp(suffix=".ipynb")
        with os.fdopen(fd, "w") as f:
            f.write("not valid json{")
        try:
            self.assertIsNone(jus.detect_ipynb_language(path))
        finally:
            os.remove(path)


class TestResolveSoftware(unittest.TestCase):
    def setUp(self):
        self.ext_lookup = {"do": "Stata", "ado": "Stata", "py": "Python", "r": "R"}
        self.name_lookup = {"project.toml": "Julia", "manifest.toml": "Julia"}

    def test_basic_extension_mapping(self):
        found, unmatched = jus.resolve_software(
            ["./code/main.do", "./code/clean.py"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, {"Stata", "Python"})
        self.assertEqual(unmatched, {})

    def test_filename_override_beats_extension(self):
        found, unmatched = jus.resolve_software(
            ["./Project.toml"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, {"Julia"})

    def test_excluded_extension_is_unmatched(self):
        found, unmatched = jus.resolve_software(
            ["./run.sh"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, set())
        self.assertEqual(unmatched, {"sh": 1})

    def test_dedup_across_files(self):
        found, unmatched = jus.resolve_software(
            ["./a.do", "./b.do", "./c.ado"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, {"Stata"})

    def test_ipynb_without_project_dir_is_unmatched(self):
        found, unmatched = jus.resolve_software(
            ["./notebook.ipynb"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, set())
        self.assertEqual(unmatched, {"ipynb": 1})

    def test_ipynb_with_project_dir_resolves_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            nb_path = Path(tmp) / "notebook.ipynb"
            nb_path.write_text(json.dumps({"metadata": {"kernelspec": {"language": "python"}}}))
            found, unmatched = jus.resolve_software(
                ["notebook.ipynb"], tmp, self.ext_lookup, self.name_lookup
            )
            self.assertEqual(found, {"Python"})
            self.assertEqual(unmatched, {})

    def test_no_extension_uses_basename_as_unmatched_key(self):
        found, unmatched = jus.resolve_software(
            ["./makefile"], None, self.ext_lookup, self.name_lookup
        )
        self.assertEqual(found, set())
        self.assertEqual(unmatched, {"makefile": 1})


class TestReadMetadataFilenames(unittest.TestCase):
    def test_reads_filenames_skipping_header(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "lines"])
            writer.writerow(["./code/main.do", "120"])
            writer.writerow(["./code/clean.py", "45"])
        try:
            self.assertEqual(
                jus.read_metadata_filenames(path),
                ["./code/main.do", "./code/clean.py"],
            )
        finally:
            os.remove(path)


from unittest.mock import MagicMock


class TestNormalizeIssueKey(unittest.TestCase):
    def test_bare_number_gets_prefixed(self):
        self.assertEqual(jus.normalize_issue_key("9603"), "AEAREP-9603")

    def test_prefixed_key_is_uppercased(self):
        self.assertEqual(jus.normalize_issue_key("train-2000"), "TRAIN-2000")

    def test_already_correct_key_unchanged(self):
        self.assertEqual(jus.normalize_issue_key("AEAREP-9603"), "AEAREP-9603")


class TestUpdateSoftwareField(unittest.TestCase):
    def _mock_issue(self, current_labels):
        issue = MagicMock()
        setattr(issue.fields, jus.SOFTWARE_FIELD, current_labels)
        return issue

    def test_adds_new_software_to_empty_field(self):
        jira = MagicMock()
        issue = self._mock_issue([])
        jira.issue.return_value = issue

        updated, final_set, added = jus.update_software_field(jira, "AEAREP-1", {"Stata"})

        self.assertTrue(updated)
        self.assertEqual(final_set, {"Stata"})
        self.assertEqual(added, {"Stata"})
        issue.update.assert_called_once_with(fields={jus.SOFTWARE_FIELD: ["Stata"]})

    def test_unions_with_existing_and_dedupes(self):
        jira = MagicMock()
        issue = self._mock_issue(["Stata"])
        jira.issue.return_value = issue

        updated, final_set, added = jus.update_software_field(jira, "AEAREP-1", {"Stata", "Python"})

        self.assertTrue(updated)
        self.assertEqual(final_set, {"Stata", "Python"})
        self.assertEqual(added, {"Python"})
        issue.update.assert_called_once_with(fields={jus.SOFTWARE_FIELD: ["Python", "Stata"]})

    def test_no_update_when_nothing_new(self):
        jira = MagicMock()
        issue = self._mock_issue(["Stata", "Python"])
        jira.issue.return_value = issue

        updated, final_set, added = jus.update_software_field(jira, "AEAREP-1", {"Stata"})

        self.assertFalse(updated)
        self.assertEqual(added, set())
        issue.update.assert_not_called()


class TestMain(unittest.TestCase):
    def _write_metadata(self, rows):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "lines"])
            for row in rows:
                writer.writerow(row)
        return path

    def test_dry_run_without_yes_returns_0_and_makes_no_jira_call(self):
        path = self._write_metadata([["./code/main.do", "10"]])
        try:
            rc = jus.main([ "AEAREP-1", path])
            self.assertEqual(rc, 0)
        finally:
            os.remove(path)

    def test_missing_metadata_csv_returns_1(self):
        rc = jus.main(["AEAREP-1", "/nonexistent/metadata.csv"])
        self.assertEqual(rc, 1)

    def test_yes_without_credentials_returns_1(self):
        path = self._write_metadata([["./code/main.do", "10"]])
        old_user = os.environ.pop("JIRA_USERNAME", None)
        old_key = os.environ.pop("JIRA_API_KEY", None)
        try:
            rc = jus.main(["AEAREP-1", path, "--yes"])
            self.assertEqual(rc, 1)
        finally:
            os.remove(path)
            if old_user is not None:
                os.environ["JIRA_USERNAME"] = old_user
            if old_key is not None:
                os.environ["JIRA_API_KEY"] = old_key

    def test_no_software_detected_returns_0(self):
        path = self._write_metadata([["./config.yaml", "5"]])
        try:
            rc = jus.main(["AEAREP-1", path])
            self.assertEqual(rc, 0)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
