import unittest

from lumen_data.books import BOOKS, BY_ID, all_aliases, find_book, normalize_name


class BooksTest(unittest.TestCase):
    def test_has_73_unique_books_in_douay_order(self):
        self.assertEqual(len(BOOKS), 73)
        self.assertEqual(len({b.id for b in BOOKS}), 73)
        self.assertEqual((BOOKS[0].id, BOOKS[-1].id), ("GEN", "REV"))
        self.assertEqual([b.id for b in BOOKS[15:19]], ["NEH", "TOB", "JDT", "EST"])

    def test_modern_names_win_over_douay_names(self):
        self.assertEqual(find_book("1 Kings").id, "1KI")
        self.assertEqual(find_book("3 Kings").id, "1KI")
        self.assertEqual(find_book("1 Samuel").id, "1SA")

    def test_lectionary_and_usccb_abbreviations(self):
        cases = {"Is": "ISA", "Ps": "PSA", "Psalm": "PSA", "1 Kgs": "1KI", "Jn": "JHN", "Sir": "SIR",
                 "Ecclesiasticus": "SIR", "Rv": "REV", "Hewbrews": "HEB", "Jl": "JOL", "Phil": "PHP",
                 "II Corinthians": "2CO", "1Cor": "1CO", "Song of Songs": "SNG", "Isaias": "ISA",
                 "1 Sm": "1SA", "Neh": "NEH", "2 Esdras": "NEH", "Tb": "TOB"}
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(find_book(name).id, expected)

    def test_unknown_name(self):
        self.assertIsNone(find_book("Gospel of Thomas"))

    def test_normalize(self):
        self.assertEqual(normalize_name("  II  Cor. "), "2 cor")
        self.assertEqual(normalize_name("1Kgs"), "1 kgs")

    def test_aliases_exclude_names_owned_by_other_books(self):
        self.assertNotIn("1 kings", all_aliases(BY_ID["1SA"]))
        self.assertIn("1 kings", all_aliases(BY_ID["1KI"]))
        self.assertIn("psalm", all_aliases(BY_ID["PSA"]))
        self.assertIn("isaias", all_aliases(BY_ID["ISA"]))
