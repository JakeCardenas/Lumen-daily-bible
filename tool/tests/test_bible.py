import unittest

from lumen_data.bible import BibleFormatError, DouayIndex, build_bible, parse_vpl

SAMPLE = """﻿GEN 1:1 In the beginning God created heaven, and earth.
GEN 1:2 And the earth was void and empty.
PSA 9:1 Unto the end.
PSA 9:3 I will give praise to thee.
JOH 3:16 For God so loved the world.
"""


class BibleTest(unittest.TestCase):
    def test_parse_maps_vpl_codes_to_app_ids(self):
        verses = parse_vpl(SAMPLE)
        self.assertEqual(verses["GEN"][1][2], "And the earth was void and empty.")
        self.assertEqual(verses["JHN"][3][16], "For God so loved the world.")

    def test_unknown_book_code_is_an_error(self):
        with self.assertRaises(BibleFormatError):
            parse_vpl("XYZ 1:1 text")

    def test_build_records_gaps_names_and_aliases(self):
        bible, gaps = build_bible(parse_vpl(SAMPLE), require_all=False)
        books = {b["id"]: b for b in bible["books"]}
        self.assertEqual(books["PSA"]["chapters"][8], ["Unto the end.", None, "I will give praise to thee."])
        self.assertIn("PSA 9:2", gaps)
        self.assertEqual(books["JHN"]["name"], "John")
        self.assertIn("jn", books["JHN"]["aliases"])
        self.assertEqual([b["id"] for b in bible["books"]], ["GEN", "PSA", "JHN"])

    def test_build_requires_every_book_by_default(self):
        with self.assertRaises(BibleFormatError):
            build_bible(parse_vpl(SAMPLE))

    def test_index_lookups(self):
        bible, _ = build_bible(parse_vpl(SAMPLE), require_all=False)
        index = DouayIndex(bible)
        self.assertTrue(index.has("GEN", 1, 1))
        self.assertFalse(index.has("PSA", 9, 2))
        self.assertEqual(index.chapter_len("PSA", 9), 3)
        self.assertEqual(index.chapter_len("PSA", 200), 0)
        self.assertEqual(index.name("GEN"), "Genesis")
