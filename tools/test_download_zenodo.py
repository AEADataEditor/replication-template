#!/usr/bin/env python3
"""Tests for download_zenodo.py. Run: python3 tools/test_download_zenodo.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import download_zenodo as dz


class TestClassifyUrl(unittest.TestCase):
    def test_community_request_url(self):
        kind, ident = dz.classify_url(
            'https://zenodo.org/communities/foo/requests/61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665'
        )
        self.assertEqual(kind, 'request')
        self.assertEqual(ident, '61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665')

    def test_me_requests_url(self):
        kind, ident = dz.classify_url(
            'https://zenodo.org/me/requests/61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665.zip'
        )
        self.assertEqual(kind, 'request')
        self.assertEqual(ident, '61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665')

    def test_deposit_url(self):
        kind, ident = dz.classify_url('https://zenodo.org/deposit/1234567')
        self.assertEqual(kind, 'draft')
        self.assertEqual(ident, '1234567')

    def test_record_url(self):
        kind, ident = dz.classify_url('https://zenodo.org/records/1234567')
        self.assertEqual(kind, 'public')
        self.assertEqual(ident, '1234567')

    def test_bare_id(self):
        kind, ident = dz.classify_url('1234567')
        self.assertEqual(kind, 'public')
        self.assertEqual(ident, '1234567')

    def test_unparseable_raises(self):
        with self.assertRaises(SystemExit):
            dz.classify_url('https://zenodo.org/nonsense/path')


if __name__ == '__main__':
    unittest.main()
