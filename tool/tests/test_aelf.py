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
        self.assertEqual(set(day.masses), {"vigil", "day"})
        self.assertEqual(day.masses["vigil"]["gospel"], "Matthew 1:1-25|Matthew 1:18-25")
        self.assertEqual(list(day.masses["day"]), ["first_reading", "responsorial_psalm", "second_reading",
                                                    "gospel_acclamation", "gospel"])
        self.assertEqual(day.masses["day"]["gospel_acclamation"], "John 1:14")
        self.assertEqual(day.masses["day"]["responsorial_psalm"], "Psalm 98:1, 2-3ab, 3cd-4, 5-6")
        self.assertEqual(day.info["annee"], "C")
