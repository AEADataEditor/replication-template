#!/usr/bin/env python3
"""Tests for download_zenodo_draft.py. Run: python3 tools/test_download_zenodo_draft.py"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import download_zenodo_draft as dzd


class TestIsRequestUrl(unittest.TestCase):
    def test_community_request_url(self):
        self.assertTrue(dzd.is_request_url(
            'https://zenodo.org/communities/foo/requests/61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665'
        ))

    def test_me_requests_url(self):
        self.assertTrue(dzd.is_request_url(
            'https://zenodo.org/me/requests/61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665.zip'
        ))

    def test_record_url_is_not_request(self):
        self.assertFalse(dzd.is_request_url('https://zenodo.org/records/1234567'))


class TestResolveRequestToRecordId(unittest.TestCase):
    @patch('download_zenodo_draft.requests.get')
    def test_topic_record_as_bare_string(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {'topic': {'record': '18940044'}}
        )
        record_id = dzd.resolve_request_to_record_id('uuid', 'token')
        self.assertEqual(record_id, '18940044')

    @patch('download_zenodo_draft.requests.get')
    def test_topic_deposit_as_dict(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {'topic': {'deposit': {'id': '999'}}}
        )
        record_id = dzd.resolve_request_to_record_id('uuid', 'token')
        self.assertEqual(record_id, '999')

    @patch('download_zenodo_draft.requests.get')
    def test_falls_back_to_topic_link(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {'links': {'topic': 'https://zenodo.org/api/records/555'}},
        )
        record_id = dzd.resolve_request_to_record_id('uuid', 'token')
        self.assertEqual(record_id, '555')


if __name__ == '__main__':
    unittest.main()
