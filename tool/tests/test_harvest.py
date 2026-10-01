import unittest
from datetime import date

from lumen_data.aelf import AelfDay
from lumen_data.harvest import accept, candidate_dates, classify_memorial

READINGS = {"first_reading": "Galatians 1:6-12", "responsorial_psalm": "Psalm 111:1-2, 7-8, 9, 10c",
            "gospel": "Luke 10:25-37"}
WEEKDAY_INFO = {"annee": "Paire", "temps_liturgique": "ordinaire", "semaine": "27ème Semaine du Temps Ordinaire",
                "jour": "lundi", "ligne1": "lundi, 27ème Semaine du Temps Ordinaire", "ligne2": "", "ligne3": ""}


def ev(day, key, grade, **extra):
    return {"date": f"{day}T00:00:00+00:00", "event_key": key, "name": key, "grade": grade, **extra}


EVENTS = {
    date(2024, 10, 7): [ev("2024-10-07", "OrdWeekday27Monday", 0, liturgical_year="YEAR II")],
    date(2025, 10, 6): [ev("2025-10-06", "OrdWeekday27Monday", 0, liturgical_year="YEAR I")],
    date(2022, 10, 3): [ev("2022-10-03", "OrdWeekday27Monday", 0, liturgical_year="YEAR II")],
    date(2025, 10, 1): [ev("2025-10-01", "StThereseChildJesus", 3)],
    date(2023, 10, 1): [ev("2023-10-01", "OrdSunday26", 5, liturgical_year="YEAR A")],
}


def page(info=None, **masses):
    return AelfDay(info if info is not None else WEEKDAY_INFO, masses or {"day": READINGS})


class HarvestTest(unittest.TestCase):
    def test_candidates_match_key_and_cycle_newest_first(self):
        need = {"kind": "set", "set": "OrdWeekday27Monday/II"}
        self.assertEqual(candidate_dates(need, EVENTS, before=date(2026, 10, 1)), [date(2024, 10, 7), date(2022, 10, 3)])

    def test_candidates_respect_the_cutoff(self):
        need = {"kind": "set", "set": "OrdWeekday27Monday/II"}
        self.assertEqual(candidate_dates(need, EVENTS, before=date(2024, 1, 1)), [date(2022, 10, 3)])

    def test_memorial_candidates(self):
        need = {"kind": "memorial", "key": "StThereseChildJesus"}
        self.assertEqual(candidate_dates(need, EVENTS, before=date(2026, 1, 1)), [date(2025, 10, 1)])

    def test_variant_sets_use_the_date_page(self):
        need = {"kind": "set", "set": "OrdWeekday27Monday/II#vigil"}
        self.assertEqual(candidate_dates(need, EVENTS, before=date(2026, 10, 1)), [date(2024, 10, 7), date(2022, 10, 3)])

    def test_weekday_pages_must_match_week_day_and_year(self):
        need = {"kind": "set", "set": "OrdWeekday27Monday/II"}
        record = accept(need, date(2024, 10, 7), page())
        self.assertEqual(record["readings"], READINGS)
        self.assertEqual((record["date"], record["source"]), ("2024-10-07", "aelf"))
        self.assertIsNone(accept(need, date(2024, 10, 7), page({**WEEKDAY_INFO, "semaine": "28ème Semaine du Temps Ordinaire"})))
        self.assertIsNone(accept(need, date(2024, 10, 7), page({**WEEKDAY_INFO, "jour": "mardi"})))
        self.assertIsNone(accept(need, date(2024, 10, 7), page({**WEEKDAY_INFO, "annee": "Impaire"})))
        self.assertIsNone(accept(need, date(2024, 10, 7), page({**WEEKDAY_INFO, "ligne3": "Mémoire"})))
        self.assertIsNotNone(accept(need, date(2024, 10, 7), page({**WEEKDAY_INFO, "ligne3": "Mémoire facultative"})))

    def test_sunday_pages_must_match_the_cycle_and_variants_pick_their_mass(self):
        need = {"kind": "set", "set": "Christmas/A#night"}
        info = {"annee": "A", "temps_liturgique": "noel", "ligne1": "Nativité du Seigneur"}
        night = {**READINGS, "gospel": "Luke 2:1-14"}
        self.assertEqual(accept(need, date(2022, 12, 25), page(info, night=night, day=READINGS))["readings"], night)
        self.assertIsNone(accept(need, date(2022, 12, 25), page({**info, "annee": "B"}, night=night)))
        self.assertIsNone(accept(need, date(2022, 12, 25), page(info, day=READINGS)))

    def test_incomplete_pages_are_rejected(self):
        need = {"kind": "set", "set": "StMartha/"}
        self.assertIsNone(accept(need, date(2025, 7, 29), page({}, day={"gospel": "John 11:19-27"})))

    def test_memorials_keep_only_their_proper_readings(self):
        weekday = {"first_reading": "Nehemiah 8:1-4a, 5-6, 7b-12", "responsorial_psalm": "Psalm 19:8, 9, 10, 11",
                   "gospel": "Luke 10:1-12"}
        same = classify_memorial(date(2025, 10, 1), page({}, day=weekday), weekday)
        self.assertEqual(same["use"], "weekday")
        self.assertNotIn("readings", same)
        guardian = {**weekday, "responsorial_psalm": "Psalm 19:8-11", "gospel_acclamation": "Psalm 103:21",
                    "gospel": "Matthew 18:1-5, 10"}
        proper = classify_memorial(date(2025, 10, 2), page({}, day=guardian), weekday)
        self.assertEqual(proper["use"], "proper")
        self.assertEqual(proper["readings"], {"gospel_acclamation": "Psalm 103:21", "gospel": "Matthew 18:1-5, 10"})
        self.assertIsNone(classify_memorial(date(2025, 10, 2), page({}, day={"gospel": "Matthew 18:1-5"}), weekday))
