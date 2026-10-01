import unittest
from datetime import date

from lumen_data.bible import DouayIndex
from lumen_data.lectionary import (CalendarBuilder, advent_start, is_complete, ord_weekday_lectionary_number,
                                   primary_event, rank_label, sunday_cycle, validate)
from lumen_data.versification import TvtmsMap, Versifier

WEEKDAY = {"first_reading": "Galatians 1:6-12", "responsorial_psalm": "Psalm 111:1b-2, 7-8",
           "gospel_acclamation": "John 13:34", "gospel": "Luke 10:25-37"}
SUNDAY = {"first_reading": "Galatians 2:1-2", "responsorial_psalm": "Psalm 23:1-3",
          "second_reading": "Galatians 3:1", "gospel_acclamation": "John 13:34", "gospel": "Luke 11:1-4"}
EMPTY = {"first_reading": "", "responsorial_psalm": "", "gospel_acclamation": "", "gospel": ""}


def ev(day, key, name, grade, **extra):
    return {"date": f"{day}T00:00:00+00:00", "event_key": key, "name": name, "grade": grade, "color": ["green"],
            "liturgical_season": "ORDINARY_TIME", "liturgical_season_lcl": "Ordinary Time", **extra}


def lectionary():
    files = {name: {} for name in ("dominicale_et_festivum_A", "dominicale_et_festivum_B", "dominicale_et_festivum_C",
                                   "feriale_per_annum_I", "feriale_tempus_adventus", "feriale_tempus_nativitatis",
                                   "feriale_tempus_paschatis", "feriale_tempus_quadragesimae")}
    files["dominicale_et_festivum_A"]["OrdSunday27"] = SUNDAY
    files["feriale_per_annum_II"] = {f"OrdWeekday26{d}": WEEKDAY for d in ("Monday", "Wednesday", "Thursday", "Friday")}
    files["feriale_per_annum_II"]["OrdWeekday26Saturday"] = EMPTY
    files["sanctorum"] = {"StsArchangels": WEEKDAY, "StThereseChildJesus": EMPTY}
    return files


def events():
    y2 = {"liturgical_year": "YEAR II"}
    return {
        date(2026, 9, 28): [ev("2026-09-28", "OrdWeekday26Monday", "Monday of the 26th Week of Ordinary Time", 0, **y2)],
        date(2026, 9, 29): [ev("2026-09-29", "StsArchangels", "Saints Michael, Gabriel and Raphael, Archangels", 4, color=["white"])],
        date(2026, 9, 30): [ev("2026-09-30", "OrdWeekday26Wednesday", "Wednesday of the 26th Week of Ordinary Time", 0, **y2)],
        date(2026, 10, 1): [ev("2026-10-01", "StThereseChildJesus", "Saint Therese of the Child Jesus", 3, color=["white"])],
        date(2026, 10, 2): [ev("2026-10-02", "OrdWeekday26Friday", "Friday of the 26th Week of Ordinary Time", 0, **y2)],
        date(2026, 10, 3): [
            ev("2026-10-03", "OrdWeekday26Saturday", "Saturday of the 26th Week of Ordinary Time", 0, **y2),
            ev("2026-10-03", "SatMemBVM", "Saturday Memorial of the Blessed Virgin Mary", 2),
            ev("2026-10-03", "OrdSunday27_vigil", "27th Sunday of Ordinary Time Vigil Mass", 5,
               is_vigil_mass=True, is_vigil_for="OrdSunday27"),
        ],
        date(2026, 10, 4): [ev("2026-10-04", "OrdSunday27", "27th Sunday of Ordinary Time", 5, liturgical_year="YEAR A")],
    }


def douay():
    names = {"GAL": "Galatians", "LUK": "Luke", "JHN": "John", "PSA": "Psalms"}
    chapters = {"GAL": 6, "LUK": 24, "JHN": 21, "PSA": 150}
    return DouayIndex({"books": [{"id": b, "name": names[b],
                                  "chapters": [[f"{b} {c}:{v}" for v in range(1, 61)] for c in range(1, n + 1)]}
                                 for b, n in chapters.items()]})


class LectionaryTest(unittest.TestCase):
    def build(self, fill=None):
        index = douay()
        builder = CalendarBuilder(events(), lectionary(), fill or {"sets": {}, "memorials": {}},
                                  Versifier(index, TvtmsMap({})), index)
        return builder.build(date(2026, 9, 28), date(2026, 10, 4))

    def test_cycles_and_lectionary_numbers(self):
        self.assertEqual(advent_start(2026), date(2026, 11, 29))
        self.assertEqual(advent_start(2022), date(2022, 11, 27))
        self.assertEqual(sunday_cycle(date(2026, 10, 4)), "A")
        self.assertEqual(sunday_cycle(date(2026, 11, 29)), "B")
        self.assertEqual(ord_weekday_lectionary_number("OrdWeekday27Monday"), 461)
        self.assertEqual(ord_weekday_lectionary_number("OrdWeekday1Monday"), 305)
        self.assertIsNone(ord_weekday_lectionary_number("Advent1"))

    def test_optional_memorials_and_vigils_are_never_primary(self):
        self.assertEqual(primary_event(events()[date(2026, 10, 3)])["event_key"], "OrdWeekday26Saturday")

    def test_rank_labels(self):
        self.assertIsNone(rank_label(events()[date(2026, 10, 4)][0]))
        self.assertEqual(rank_label(events()[date(2026, 9, 29)][0]), "Feast")
        self.assertEqual(rank_label(events()[date(2026, 10, 1)][0]), "Memorial")
        self.assertIsNone(rank_label(events()[date(2026, 9, 28)][0]))

    def test_completeness(self):
        self.assertTrue(is_complete(WEEKDAY))
        self.assertFalse(is_complete({**WEEKDAY, "responsorial_psalm": "Psalm 71"}))
        self.assertFalse(is_complete({**WEEKDAY, "gospel": ""}))
        self.assertFalse(is_complete({**WEEKDAY, "first_reading": "Nowhere 1:1"}))

    def test_gaps_and_unclassified_memorials_become_harvest_needs(self):
        result = self.build()
        self.assertEqual(result.needs["OrdWeekday26Saturday/II"]["kind"], "set")
        self.assertEqual(result.needs["memorial:StThereseChildJesus"]["kind"], "memorial")

    def test_full_assembly(self):
        fill = {"sets": {"OrdWeekday26Saturday/II": {"readings": WEEKDAY}},
                "memorials": {"StThereseChildJesus": {"use": "weekday"}}}
        result = self.build(fill)
        self.assertEqual(result.needs, {})
        self.assertEqual(result.missing_overrides, {})
        days = result.calendar["days"]
        self.assertEqual(days["2026-10-01"]["masses"], [{"title": None, "set": "OrdWeekday26Thursday/II"}])
        self.assertEqual(days["2026-10-01"]["rank"], "Memorial")
        self.assertEqual(days["2026-10-03"]["optional"], ["Saturday Memorial of the Blessed Virgin Mary"])
        self.assertEqual(len(days["2026-10-03"]["masses"]), 1)
        self.assertEqual(days["2026-09-29"]["colors"], ["white"])
        sunday = result.calendar["sets"]["OrdSunday27/A"]
        self.assertEqual([r["kind"] for r in sunday],
                         ["first_reading", "responsorial_psalm", "second_reading", "gospel_acclamation", "gospel"])
        psalm = sunday[1]
        self.assertEqual(psalm["label"], "Responsorial Psalm")
        self.assertEqual(psalm["passages"], [{"book": "PSA", "ranges": [[22, 1, 22, 3]]}])
        self.assertEqual(psalm["douay"], "Psalm 22:1-3")
        self.assertTrue(psalm["differs"])
        self.assertEqual(sunday[3]["label"], "Alleluia")
        self.assertEqual(validate(result.calendar, douay()), [])

    def test_validate_reports_missing_gospel(self):
        calendar = {"start": "2026-10-04", "end": "2026-10-04",
                    "sets": {"X/": [{"kind": "first_reading", "passages": [{"book": "GAL", "ranges": [[1, 1, 1, 2]]}]}]},
                    "days": {"2026-10-04": {"masses": [{"title": None, "set": "X/"}]}}}
        self.assertTrue(any("Gospel" in p for p in validate(calendar, douay())))
