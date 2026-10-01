import unittest
from datetime import date

from lumen_data.harvest import accept, candidate_dates
from lumen_data.usccb import UsccbDay

READINGS = {"first_reading": "Galatians 1:6-12", "responsorial_psalm": "Psalm 111:1b-2, 7-8, 9, 10c",
            "gospel_acclamation": "John 13:34", "gospel": "Luke 10:25-37"}


def ev(day, key, grade, **extra):
    return {"date": f"{day}T00:00:00+00:00", "event_key": key, "name": key, "grade": grade, **extra}


EVENTS = {
    date(2024, 10, 7): [ev("2024-10-07", "OrdWeekday27Monday", 0, liturgical_year="YEAR II")],
    date(2025, 10, 6): [ev("2025-10-06", "OrdWeekday27Monday", 0, liturgical_year="YEAR I")],
    date(2022, 10, 3): [ev("2022-10-03", "OrdWeekday27Monday", 0, liturgical_year="YEAR II")],
    date(2025, 10, 1): [ev("2025-10-01", "StThereseChildJesus", 3)],
    date(2023, 10, 1): [ev("2023-10-01", "OrdSunday26", 5, liturgical_year="YEAR A")],
}


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

    def test_vigil_night_and_dawn_masses_are_not_harvested_automatically(self):
        need = {"kind": "set", "set": "Christmas/A#night"}
        self.assertEqual(candidate_dates(need, EVENTS, before=date(2026, 1, 1)), [])

    def test_other_variants_use_the_date_page(self):
        need = {"kind": "set", "set": "OrdWeekday27Monday/II#schema_one"}
        self.assertEqual(candidate_dates(need, EVENTS, before=date(2026, 10, 1)), [date(2024, 10, 7), date(2022, 10, 3)])

    def test_weekday_pages_must_carry_the_expected_lectionary_number(self):
        need = {"kind": "set", "set": "OrdWeekday27Monday/II"}
        record = accept(need, date(2024, 10, 7), UsccbDay("Monday", 461, READINGS))
        self.assertEqual(record["readings"], READINGS)
        self.assertEqual(record["date"], "2024-10-07")
        self.assertIsNone(accept(need, date(2024, 10, 7), UsccbDay("A memorial", 650, READINGS)))

    def test_incomplete_pages_are_rejected(self):
        need = {"kind": "set", "set": "StMartha/"}
        self.assertIsNone(accept(need, date(2025, 7, 29), UsccbDay("x", 607, {"gospel": "John 11:19-27"})))

    def test_memorial_classification(self):
        need = {"kind": "memorial", "key": "StThereseChildJesus"}
        self.assertEqual(accept(need, date(2025, 10, 1), UsccbDay("x", 455, READINGS))["use"], "weekday")
        proper = accept(need, date(2025, 10, 1), UsccbDay("x", 650, READINGS))
        self.assertEqual((proper["use"], proper["readings"]), ("proper", READINGS))
        self.assertIsNone(accept(need, date(2025, 10, 1), UsccbDay("x", None, READINGS)))
