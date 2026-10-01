import unittest

from lumen_data.citations import Citation, CitationError, citation_key, parse, split_alternatives


def spans(c: Citation) -> list[tuple]:
    return [(s.start.chapter, s.start.verse, s.start.part, s.end.chapter, s.end.verse, s.end.part) for s in c.spans]


class CitationTest(unittest.TestCase):
    def test_simple_range(self):
        [c] = parse("Isaiah 5:1-7")
        self.assertEqual(c.book, "ISA")
        self.assertEqual(spans(c), [("5", 1, "", "5", 7, "")])

    def test_psalm_with_parts_and_the_word_and(self):
        [c] = parse("Psalm 51:3-4, 5-6ab, 12-13, 14 and 17")
        self.assertEqual(spans(c), [("51", 3, "", "51", 4, ""), ("51", 5, "", "51", 6, "ab"),
                                    ("51", 12, "", "51", 13, ""), ("51", 14, "", "51", 14, ""),
                                    ("51", 17, "", "51", 17, "")])

    def test_chapter_crossing_with_em_dash(self):
        [c] = parse("Isaiah 52:13—53:12")
        self.assertEqual(spans(c), [("52", 13, "", "53", 12, "")])

    def test_chapter_change_inside_a_list_carries_forward(self):
        [c] = parse("Jonah 1:1–2:2, 11")
        self.assertEqual(spans(c), [("1", 1, "", "2", 2, ""), ("2", 11, "", "2", 11, "")])

    def test_semicolon_continues_the_same_book(self):
        [c] = parse("Hebrews 4:14-16; 5:7-9")
        self.assertEqual(c.book, "HEB")
        self.assertEqual(spans(c), [("4", 14, "", "4", 16, ""), ("5", 7, "", "5", 9, "")])

    def test_semicolon_can_switch_books(self):
        first, second = parse("John 1:7; Luke 1:17")
        self.assertEqual((first.book, second.book), ("JHN", "LUK"))

    def test_prefix_and_abbreviation(self):
        [c] = parse("Cf. Ps 85:8")
        self.assertEqual((c.book, spans(c)), ("PSA", [("85", 8, "", "85", 8, "")]))

    def test_dual_psalm_numbers_use_the_hebrew_number(self):
        [c] = parse("Psalm 103 (102): 1-2, 3-4")
        self.assertEqual(spans(c)[0][:2], ("103", 1))
        [whole] = parse("Psalm 18 (19)")
        self.assertEqual(whole.chapters, ("19",))
        self.assertTrue(whole.is_whole_chapter)

    def test_whole_psalm_and_european_comma(self):
        self.assertEqual(parse("Psalm 71")[0].chapters, ("71",))
        self.assertEqual(spans(parse("Psalm 84,5")[0]), [("84", 5, "", "84", 5, "")])

    def test_spacing_variants(self):
        self.assertEqual(spans(parse("Ephesians 3: 14-19")[0]), [("3", 14, "", "3", 19, "")])
        self.assertEqual(len(parse("Exodus 15:1-2,3-4,5-6,17-18")[0].spans), 4)
        self.assertEqual(spans(parse("Tobit 13:2, 6efgh")[0])[1], ("13", 6, "efgh", "13", 6, "efgh"))

    def test_esther_lettered_chapter(self):
        [c] = parse("Esther C:12, 14-16, 23-25")
        self.assertEqual(spans(c), [("C", 12, "", "C", 12, ""), ("C", 14, "", "C", 16, ""), ("C", 23, "", "C", 25, "")])

    def test_multi_chapter_with_parts(self):
        [c] = parse("Revelation 11:19a; 12:1-6a, 10ab")
        self.assertEqual(c.book, "REV")
        self.assertEqual(spans(c), [("11", 19, "a", "11", 19, "a"), ("12", 1, "", "12", 6, "a"), ("12", 10, "ab", "12", 10, "ab")])

    def test_typo_seen_in_source_data(self):
        self.assertEqual(parse("Hewbrews 2:14-18")[0].book, "HEB")

    def test_errors(self):
        for bad in ["", "Gospel of Thomas 1:1", "5:7-9", "Psalm 23:x"]:
            with self.subTest(bad=bad), self.assertRaises(CitationError):
                parse(bad)

    def test_alternatives(self):
        self.assertEqual(split_alternatives("Luke 2:22-40|Luke 2:22-32"), ["Luke 2:22-40", "Luke 2:22-32"])

    def test_key_ignores_formatting(self):
        self.assertEqual(citation_key(parse("Sirach 3:2-6, 12-14")[0]), "SIR 3:2-6,12-14")
        self.assertEqual(citation_key(parse("Sir 3:2-6,12-14")[0]), "SIR 3:2-6,12-14")
        self.assertEqual(citation_key(parse("Sirach 27:30–28:7")[0]), "SIR 27:30-28:7")
        self.assertEqual(citation_key(parse("Psalm 71")[0]), "PSA 71")
