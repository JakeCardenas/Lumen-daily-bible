import unittest

from lumen_data.bible import DouayIndex
from lumen_data.citations import parse
from lumen_data.versification import (DouayPassage, MissingOverride, TvtmsMap, VersificationError, Versifier,
                                      format_passage, psalm_hebrew_to_douay)

NAMES = {"ISA": "Isaias", "PSA": "Psalms", "EST": "Esther", "SIR": "Ecclesiasticus", "MAT": "Matthew", "MRK": "Mark"}
CHAPTERS = {"ISA": 66, "PSA": 150, "EST": 16, "SIR": 51, "MAT": 28, "MRK": 16}
LENGTHS = {"ISA": {9: 21, 63: 19, 64: 12}, "PSA": {22: 6, 114: 9, 115: 10, 146: 11, 147: 9},
           "EST": {13: 18, 14: 19}, "MAT": {5: 48}}
DOUAY = DouayIndex({"books": [
    {"id": book, "name": NAMES[book],
     "chapters": [[f"{book} {c}:{v}" for v in range(1, LENGTHS.get(book, {}).get(c, 30) + 1)]
                  for c in range(1, count + 1)]}
    for book, count in CHAPTERS.items()]})

HEADER = ("#DataStart(Expanded)\nSourceType\tSourceRef\tStandardRef\tAction\tNoteMarker\t"
          "Reversification Note\tVersification Note\tAncient Versions\tTests\n")


def row(types, source, hebrew, latin, greek):
    return (f"{types}\t{source}\t{source}\tKeep verse\tx\tx\tx\t"
            f"(Hebrew={hebrew} • Latin={latin} • Greek={greek})\tTest\n")


TVTMS = HEADER + "".join([
    row("Latin", "Isa.9:1", "8:23", "9:1", "8:23"),
    *[row("Latin", f"Isa.9:{v + 1}", f"9:{v}", f"9:{v + 1}", f"9:{v}") for v in range(1, 21)],
    row("Latin", "Isa.63:19", "63:19", "63:19", "63:19"),
    row("Latin", "Isa.64:1", "63:19", "64:1", "63:19"),
    *[row("Latin", f"Isa.64:{v + 1}", f"64:{v}", f"64:{v + 1}", f"64:{v}") for v in range(1, 12)],
    row("Eng-KJV+Hebrew", "Psa.147:12", "147:12", "147:12", "147:1"),
    row("Greek+Latin", "Psa.147:1", "147:12", "147:1", "147:1"),
    row("Latin", "Mrk.8:39", "", "8:39", "9:1"),
    *[row("Latin", f"Mrk.9:{v - 1}", "", f"9:{v - 1}", f"9:{v}") for v in range(2, 11)],
]) + "#DataEnd(Expanded)\n"


class VersificationTest(unittest.TestCase):
    def setUp(self):
        overrides = {"SIR 3:2-6,12-14": {"ranges": [[3, 3, 3, 7], [3, 14, 3, 16]], "reviewed": "test"}}
        self.versifier = Versifier(DOUAY, TvtmsMap.parse(TVTMS), overrides=overrides)

    def convert(self, text) -> DouayPassage:
        [citation] = parse(text)
        return self.versifier.convert(citation)

    def test_tvtms_only_uses_rows_describing_latin_bibles(self):
        tvtms = TvtmsMap.parse(TVTMS)
        self.assertEqual(tvtms.latin_for("Psa", 147, 12), [(147, 1)])
        self.assertEqual(tvtms.latin_for("Isa", 63, 19), [(63, 19), (64, 1)])
        self.assertIsNone(tvtms.latin_for("Isa", 1, 1))

    def test_isaiah_nine_shifts_by_one_verse(self):
        passage = self.convert("Isaiah 9:1-6")
        self.assertEqual(passage.ranges, ((9, 2, 9, 7),))
        self.assertTrue(passage.differs)
        self.assertFalse(passage.partial)
        self.assertEqual(format_passage(passage, DOUAY), "Isaias 9:2-7")

    def test_verse_parts_choose_the_half_of_a_split_verse(self):
        passage = self.convert("Isaiah 63:16b-17, 19b; 64:2-7")
        self.assertEqual(passage.ranges, ((63, 16, 63, 17), (64, 1, 64, 1), (64, 3, 64, 8)))
        self.assertTrue(passage.partial)

    def test_psalms_without_tvtms_rows_use_the_psalter_rule(self):
        self.assertEqual(self.convert("Psalm 23:1-3a, 3b-4").ranges, ((22, 1, 22, 4),))
        self.assertEqual(self.convert("Psalm 116:12-13, 15-16bc, 17-18").ranges, ((115, 3, 115, 4), (115, 6, 115, 9)))
        self.assertEqual(self.convert("Psalm 147:12-13").ranges, ((147, 1, 147, 2),))

    def test_psalter_rule(self):
        cases = {(23, 1): (22, 1), (10, 1): (9, 22), (116, 9): (114, 9), (116, 10): (115, 1), (115, 1): (113, 9),
                 (147, 3): (146, 3), (147, 12): (147, 1), (150, 6): (150, 6), (51, 3): (50, 3), (9, 5): (9, 5)}
        for hebrew, douay in cases.items():
            with self.subTest(hebrew=hebrew):
                self.assertEqual(psalm_hebrew_to_douay(*hebrew), douay)

    def test_new_testament_numbers_are_unchanged(self):
        passage = self.convert("Matthew 5:1-12a")
        self.assertEqual(passage.ranges, ((5, 1, 5, 12),))
        self.assertFalse(passage.differs)
        self.assertTrue(passage.partial)

    def test_new_testament_follows_tvtms_where_the_vulgate_differs(self):
        versifier = Versifier(DOUAY, TvtmsMap.parse(TVTMS), TvtmsMap.parse(TVTMS, "Greek"))
        [citation] = parse("Mark 9:2-10")
        passage = versifier.convert(citation)
        self.assertEqual(passage.ranges, ((9, 1, 9, 9),))
        self.assertTrue(passage.differs)

    def test_reviewed_douay_joins_shift_the_verses_that_follow(self):
        # As in 1 Thessalonians 4: Douay-Rheims joins verses 11 and 12, so 13 onward is one lower.
        joins = {"MAT": {"5": [[12, 12, 11], [13, 48, 12]]}}
        versifier = Versifier(DOUAY, TvtmsMap.parse(TVTMS), TvtmsMap.parse(TVTMS, "Greek"), douay_joins=joins)
        [citation] = parse("Matthew 5:12-14, 48")
        passage = versifier.convert(citation)
        self.assertEqual(passage.ranges, ((5, 11, 5, 13), (5, 47, 5, 47)))
        self.assertTrue(passage.differs)
        [unchanged] = parse("Matthew 5:1-11")
        self.assertEqual(versifier.convert(unchanged).ranges, ((5, 1, 5, 11),))

    def test_esther_additions(self):
        self.assertEqual(self.convert("Esther C:12, 14-16, 23-25").ranges, ((14, 1, 14, 1), (14, 3, 14, 5), (14, 12, 14, 14)))

    def test_greek_numbered_books_need_a_reviewed_override(self):
        self.assertEqual(self.convert("Sirach 3:2-6, 12-14").ranges, ((3, 3, 3, 7), (3, 14, 3, 16)))
        with self.assertRaises(MissingOverride) as caught:
            self.convert("Sirach 27:30-28:7")
        self.assertEqual(caught.exception.key, "SIR 27:30-28:7")
        self.assertEqual(caught.exception.proposal["ranges"], [[27, 30, 28, 7]])
        self.assertEqual(caught.exception.proposal["first_verse"], "SIR 27:30")

    def test_a_verse_missing_from_douay_rheims_is_an_error(self):
        with self.assertRaises(VersificationError):
            self.convert("Isaiah 9:30")

    def test_repeated_psalm_verses_are_merged(self):
        self.assertEqual(self.convert("Psalm 96:1-2, 2-3").ranges, ((95, 1, 95, 3),))

    def test_format_multiple_ranges(self):
        passage = self.convert("Psalm 116:12-13, 15-16bc, 17-18")
        self.assertEqual(format_passage(passage, DOUAY), "Psalm 115:3-4, 6-9")
