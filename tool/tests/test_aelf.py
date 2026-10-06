import unittest
from datetime import date

from lumen_data.aelf import URL, parse_day, to_citation
from lumen_data.citations import CitationError, parse


class AelfReferenceTest(unittest.TestCase):
    def test_converts_french_references_to_lectionary_citations(self):
        cases = {
            "Ga 1, 6-12": "Galatians 1:6-12",
            "Ne 8, 1-4a.5-6.7b-12": "Nehemiah 8:1-4a, 5-6, 7b-12",
            "Ex 33, 7-11 ; 34, 5b-9.28": "Exodus 33:7-11; 34:5b-9, 28",
            "1 Jn 3, 22 – 4, 6": "1 John 3:22-4:6",
            "2 Co  5, 6-10": "2 Corinthians 5:6-10",
            "Mt 18, 1-5.10": "Matthew 18:1-5, 10",
            "Sg 2, 12": "Wisdom 2:12",
            "Ct 2, 8-14": "Song of Songs 2:8-14",
        }
        for ref, expected in cases.items():
            with self.subTest(ref=ref):
                self.assertEqual(to_citation(ref), expected)
                parse(expected)

    def test_psalms_use_the_hebrew_number_and_may_omit_the_book(self):
        self.assertEqual(to_citation("Ps 110 (111), 1-2, 7-8, 9.10c"), "Psalm 111:1-2, 7-8, 9, 10c")
        self.assertEqual(to_citation("Ps 18b (19), 8, 9"), "Psalm 19:8, 9")
        self.assertEqual(to_citation("91 (92), 2-3, 13-14", default_book="PSA"), "Psalm 92:2-3, 13-14")
        self.assertEqual(to_citation("2, 7bc-8, 10-11", default_book="PSA"), "Psalm 2:7bc-8, 10-11")

    def test_a_lone_psalm_number_is_the_greek_number(self):
        self.assertEqual(to_citation("Ps 96, 1-2, 4-5, 6.9"), "Psalm 97:1-2, 4-5, 6, 9")
        self.assertEqual(to_citation("Ps 83, 3, 4, 5-6, 11"), "Psalm 84:3, 4, 5-6, 11")
        self.assertEqual(to_citation("Ps 149, 1-2, 3-4, 5-6a.9b"), "Psalm 149:1-2, 3-4, 5-6a, 9b")
        self.assertEqual(to_citation("Ps 9a, 2-3, 6.16, 8-9"), "Psalm 9:2-3, 6, 16, 8-9")
        self.assertEqual(to_citation("Ps 9b, 1-2"), "Psalm 10:1-2")
        self.assertEqual(to_citation("Ps 9A,\xa08-9,\xa010-11"), "Psalm 9:8-9, 10-11")
        self.assertEqual(to_citation("Ps 116, 1, 2"), "Psalm 117:1, 2")
        for ambiguous in ("Ps 9, 2-3", "Ps 113, 1-2", "Ps 114, 1-2", "Ps 147, 12-13"):
            with self.subTest(ref=ambiguous), self.assertRaises(CitationError):
                to_citation(ambiguous)

    def test_single_chapter_books_may_omit_the_chapter(self):
        self.assertEqual(to_citation("Phm  7-20"), "Philemon 1:7-20")
        self.assertEqual(to_citation("Phm 9b-10.12-17"), "Philemon 1:9b-10, 12-17")
        self.assertEqual(to_citation("2 Jn 1a.\xa04-9"), "2 John 1:1a, 4-9")
        self.assertEqual(to_citation("Jude 17.20b-25"), "Jude 1:17, 20b-25")
        self.assertEqual(to_citation("Phm 1, 7-20"), "Philemon 1:7-20")

    def test_a_dash_between_chapters_starts_a_new_chapter_mid_list(self):
        self.assertEqual(to_citation("Ga 4, 22-24.26-27.31 – 5, 1"), "Galatians 4:22-24, 26-27, 31-5:1")
        self.assertEqual(to_citation("Nb 13, 1-2a.25 – 14, 1.26-29.34-35"), "Numbers 13:1-2a, 25-14:1, 26-29, 34-35")
        self.assertEqual(to_citation("Ap 20, 1-4.11 – 21, 2"), "Revelation 20:1-4, 11-21:2")
        self.assertEqual(to_citation("2 Co 3, 15 – 4, 1.3-6"), "2 Corinthians 3:15-4:1, 3-6")
        for citation in ("Galatians 4:22-24, 26-27, 31-5:1", "Numbers 13:1-2a, 25-14:1, 26-29, 34-35"):
            parse(citation)

    def test_a_new_book_after_a_semicolon(self):
        self.assertEqual(to_citation("1 S 3, 9 ; Jn 6, 68c"), "1 Samuel 3:9; John 6:68c")
        self.assertEqual([c.book for c in parse("1 Samuel 3:9; John 6:68c")], ["1SA", "JHN"])

    def test_tolerates_aelf_formatting_quirks(self):
        cases = {
            "Jr 31, 10, 11,-12ab, 13": "Jeremiah 31:10, 11-12ab, 13",
            "Mt 14,\xa013-21 (Années B et C 2025)": "Matthew 14:13-21",
            "Mt 14,\xa022-36           [Année A 2023]": "Matthew 14:22-36",
            "Dn 13, 41c-62 (lecture brève)": "Daniel 13:41c-62",
            "Cantique Tb 13, 2, 3-4ab, 4cde, 7, 8ab, 8 cde": "Tobit 13:2, 3-4ab, 4cde, 7, 8ab, 8cde",
            "[CANTIQUE] Lc 1, 46b- 47, 48-49, 50.53, 54-55": "Luke 1:46b-47, 48-49, 50, 53, 54-55",
            "Stabat Mater. Jn 19, 25-27": "John 19:25-27",
            "Jean 6, 37-40": "John 6:37-40",
            "Ps18 (19),\xa02-3,\xa04-5ab": "Psalm 19:2-3, 4-5ab",
            "Ps 79 (80),\xa02a.c.3bc,\xa015-16a,\xa018-19": "Psalm 80:2a, 2c, 3bc, 15-16a, 18-19",
            "Ps  77 (78),\xa03-4a.c,\xa034-35": "Psalm 78:3-4a, 4c, 34-35",
            "Ph 2 6-11": "Philippians 2:6-11",
            "115 (116b), 12-13, 15-16ac": "Psalm 116:12-13, 15-16ac",
        }
        for ref, expected in cases.items():
            with self.subTest(ref=ref):
                self.assertEqual(to_citation(ref, default_book="PSA" if ref[0].isdigit() else None), expected)
                parse(expected)
        self.assertEqual(to_citation("86 (87), 1-2, 3 et 5, 6-7", default_book="PSA"), "Psalm 87:1-2, 3, 5, 6-7")

    def test_acclamation_prefix_and_unknown_books(self):
        self.assertEqual(to_citation("cf. Jn 15, 16"), "John 15:16")
        with self.assertRaises(CitationError):
            to_citation("Xy 1, 2")

    def test_url(self):
        self.assertEqual(URL.format(d=date(2025, 10, 2)), "https://api.aelf.org/v1/messes/2025-10-02/romain")


class AelfDayTest(unittest.TestCase):
    PAYLOAD = {
        "informations": {"annee": "C", "jour": None, "semaine": None, "temps_liturgique": "noel",
                         "ligne1": "Nativité du Seigneur", "ligne2": "", "ligne3": ""},
        "messes": [
            {"nom": "Messe de la veille au soir", "lectures": [
                {"type": "lecture_1", "ref": "Is 62, 1-5"},
                {"type": "psaume", "ref": "Ps 88 (89), 4-5, 16-17, 27.29"},
                {"type": "lecture_2", "ref": "Ac 13, 16-17.22-25"},
                {"type": "evangile", "ref": "Mt 1, 1-25", "ref_verset": ""},
                {"type": "evangile", "ref": "Mt 1, 18-25"}]},
            {"nom": "Messe du jour", "lectures": [
                {"type": "lecture_1", "ref": "Is 52, 7-10"},
                {"type": "psaume", "ref": "Ps 97 (98), 1, 2-3ab, 3cd-4, 5-6"},
                {"type": "lecture_2", "ref": "He 1, 1-6"},
                {"type": "evangile", "ref": "Jn 1, 1-18", "ref_verset": "cf. Jn 1, 14"}]},
            {"nom": "Messe de la procession", "lectures": [{"type": "evangile", "ref": "Mt 21, 1-11"}]},
        ],
    }

    def test_parses_masses_by_variant_in_reading_order(self):
        day = parse_day(self.PAYLOAD)
        self.assertEqual(set(day.masses), {"vigil", "day", "messe de la procession"})
        self.assertEqual(day.masses["vigil"]["gospel"], "Matthew 1:1-25|Matthew 1:18-25")
        self.assertEqual(list(day.masses["day"]), ["first_reading", "responsorial_psalm", "second_reading",
                                                    "gospel_acclamation", "gospel"])
        self.assertEqual(day.masses["day"]["gospel_acclamation"], "John 1:14")
        self.assertEqual(day.masses["day"]["responsorial_psalm"], "Psalm 98:1, 2-3ab, 3cd-4, 5-6")
        self.assertEqual(day.info["annee"], "C")

    def test_canticles_answer_the_psalm_and_repeated_readings_are_alternatives(self):
        day = parse_day({"informations": {}, "messes": [{"nom": "Messe du jour", "lectures": [
            {"type": "lecture_1", "ref": "Ez 16, 1-15.60.63"},
            {"type": "lecture_1", "ref": "Ez 16, 59-63"},
            {"type": "cantique", "ref": "Is 12, 2, 4bcde-5a, 5bc-6"},
            {"type": "sequence", "ref": ""},
            {"type": "evangile", "ref": "Mt 19, 3-12"}]}]})
        self.assertEqual(day.masses["day"], {"first_reading": "Ezekiel 16:1-15, 60, 63|Ezekiel 16:59-63",
                                             "responsorial_psalm": "Isaiah 12:2, 4bcde-5a, 5bc-6",
                                             "gospel": "Matthew 19:3-12"})

    def test_palm_sunday_procession_gospel_joins_the_mass_of_the_passion(self):
        day = parse_day({"informations": {}, "messes": [
            {"nom": "Procession des Rameaux", "lectures": [{"type": "evangile", "ref": "Mc  11, 1-10"},
                                                           {"type": "evangile", "ref": "Jn  12, 12-16"}]},
            {"nom": "Messe de la Passion", "lectures": [
                {"type": "lecture_1", "ref": "Is 50, 4-7"},
                {"type": "psaume", "ref": "21 (22), 8-9, 17-18a, 19-20, 22c-24a"},
                {"type": "lecture_2", "ref": "Ph 2, 6-11"},
                {"type": "evangile", "ref": "Mc 14, 1 – 15, 47"}]}]})
        self.assertEqual(set(day.masses), {"day"})
        self.assertEqual(list(day.masses["day"])[0], "palm_gospel")
        self.assertEqual(day.masses["day"]["palm_gospel"], "Mark 11:1-10|John 12:12-16")
        self.assertEqual(day.masses["day"]["gospel"], "Mark 14:1-15:47")

    def test_unrecognised_mass_names_are_kept(self):
        day = parse_day({"informations": {}, "messes": [{"nom": "Messe du matin", "lectures": [
            {"type": "lecture_1", "ref": "Sg 1, 13-15 ; 2, 23-24"}]}]})
        self.assertEqual(day.masses, {"messe du matin": {"first_reading": "Wisdom 1:13-15; 2:23-24"}})

    def test_a_mass_with_an_unreadable_reference_is_left_empty(self):
        day = parse_day({"informations": {}, "messes": [{"nom": "Messe du jour", "lectures": [
            {"type": "lecture_1", "ref": "Is 50, 4-7"}, {"type": "lecture_2", "ref": "Xy 2, 6-11"}]}]})
        self.assertEqual(day.masses, {"day": {}})
