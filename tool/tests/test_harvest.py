import unittest
from datetime import date

from lumen_data.aelf import AelfDay
from lumen_data.harvest import aelf_date, accept, apply_corrections, candidate_dates, classify_memorial

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
    date(2025, 1, 4): [ev("2025-01-04", "ChristmasWeekdayJan4", 0), ev("2025-01-04", "StElizabethSeton", 3)],
    date(2024, 1, 4): [ev("2024-01-04", "ChristmasWeekdayJan4", 0)],
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

    def test_weekdays_displaced_by_a_us_memorial_are_candidates_after_plain_ones(self):
        need = {"kind": "set", "set": "ChristmasWeekdayJan4/"}
        self.assertEqual(candidate_dates(need, EVENTS, before=date(2026, 1, 1)), [date(2024, 1, 4), date(2025, 1, 4)])

    def test_memorials_that_keep_the_weekday_readings_offer_their_dates_last(self):
        need = {"kind": "set", "set": "OrdWeekday27Monday/II"}
        events = {**EVENTS, date(2026, 10, 5): [ev("2026-10-05", "StFaustina", 3)]}

        def weekday_of(day):
            return ("OrdWeekday27Monday", "II") if day == date(2026, 10, 5) else None
        found = candidate_dates(need, events, before=date(2026, 10, 6), weekday_of=weekday_of,
                                weekday_memorials=frozenset({"StFaustina"}))
        self.assertEqual(found, [date(2024, 10, 7), date(2022, 10, 3), date(2026, 10, 5)])
        self.assertEqual(candidate_dates(need, events, before=date(2026, 10, 6), weekday_of=weekday_of), found[:2])

    def test_a_memorial_page_answers_a_weekday_only_when_the_memorial_keeps_its_readings(self):
        need = {"kind": "set", "set": "OrdWeekday27Monday/II"}
        memorial = page({**WEEKDAY_INFO, "ligne3": "Mémoire"})
        self.assertIsNone(accept(need, date(2026, 10, 5), memorial))
        self.assertEqual(accept(need, date(2026, 10, 5), memorial, during_memorial=True)["readings"], READINGS)
        wrong_week = page({**WEEKDAY_INFO, "ligne3": "Mémoire", "jour": "mardi"})
        self.assertIsNone(accept(need, date(2026, 10, 5), wrong_week, during_memorial=True))

    def test_weekday_pages_that_are_memorials_or_feasts_are_rejected(self):
        need = {"kind": "set", "set": "ChristmasWeekdayJan4/"}
        info = {"ligne1": "4 janvier", "ligne2": "de la férie", "ligne3": "", "degre": ""}
        self.assertIsNotNone(accept(need, date(2025, 1, 4), page(info)))
        self.assertIsNone(accept(need, date(2025, 1, 4), page({**info, "ligne3": "Mémoire"})))
        self.assertIsNone(accept(need, date(2025, 1, 4), page({**info, "ligne2": "Fête", "degre": "Fête"})))

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

    def test_a_single_mass_answers_a_choice_of_formularies_but_not_a_time_of_day(self):
        self.assertEqual(accept({"kind": "set", "set": "AllSouls/#schema_one"}, date(2025, 11, 2), page({}))["readings"],
                         READINGS)
        self.assertIsNone(accept({"kind": "set", "set": "Christmas/A#vigil"}, date(2022, 12, 25),
                                 page({"annee": "A"}, day=READINGS)))

    def test_a_second_reading_listed_as_another_first_reading_takes_its_slot(self):
        readings = {**READINGS, "first_reading": "Daniel 7:9-10, 13-14|2 Peter 1:16-19"}
        need = {"kind": "set", "set": "Transfiguration/B"}
        slots = ("first_reading", "responsorial_psalm", "second_reading", "gospel_acclamation", "gospel")
        fixed = accept(need, date(2024, 8, 6), page({"annee": "B"}, day=readings), slots)["readings"]
        self.assertEqual((fixed["first_reading"], fixed["second_reading"]), ("Daniel 7:9-10, 13-14", "2 Peter 1:16-19"))
        self.assertEqual(list(fixed), ["first_reading", "responsorial_psalm", "second_reading", "gospel"])
        alternatives = accept(need, date(2024, 8, 6), page({"annee": "B"}, day=readings), slots[:2] + slots[3:])
        self.assertEqual(alternatives["readings"], readings)

    def test_feasts_and_solemnities_must_have_the_same_rank_on_aelf(self):
        need = {"kind": "set", "set": "StMatthiasAp/"}
        feast = {"ligne1": "Saint Matthias, apôtre", "degre": "Fête", "ligne2": "Fête"}
        ascension = {"ligne1": "Ascension", "degre": "Solennité du Seigneur", "ligne2": "Solennité"}
        self.assertIsNotNone(accept(need, date(2025, 5, 14), page(feast), grade=4))
        self.assertIsNone(accept(need, date(2026, 5, 14), page(ascension), grade=4))
        sunday = {"ligne1": "7ème Dimanche de Pâques", "degre": "", "ligne2": "", "annee": "B"}
        self.assertIsNone(accept({"kind": "set", "set": "Ascension/B"}, date(2024, 5, 12), page(sunday), grade=7))
        self.assertIsNotNone(accept({"kind": "set", "set": "Ascension/B"}, date(2024, 5, 9),
                                    page({**ascension, "annee": "B"}), grade=7))
        # AELF leaves the year blank on Ascension Thursday; the candidate date already has the right cycle.
        self.assertIsNotNone(accept({"kind": "set", "set": "Ascension/B"}, date(2021, 5, 13),
                                    page({**ascension, "annee": None}), grade=7))
        self.assertIsNone(accept({"kind": "set", "set": "Ascension/B"}, date(2022, 5, 26),
                                 page({**ascension, "annee": "C"}), grade=7))
        palm = {"ligne1": "Dimanche des Rameaux", "degre": "", "ligne2": "", "annee": "C"}
        self.assertIsNotNone(accept({"kind": "set", "set": "PalmSun/C"}, date(2025, 4, 13), page(palm), grade=7))

    def test_the_us_ascension_sunday_is_read_from_aelf_on_thursday(self):
        self.assertEqual(aelf_date("Ascension/B", date(2024, 5, 12)), date(2024, 5, 9))
        self.assertEqual(aelf_date("Trinity/B", date(2024, 5, 26)), date(2024, 5, 26))

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

    def test_a_memorial_that_always_displaces_its_weekday_keeps_the_whole_page(self):
        record = classify_memorial(date(2026, 1, 2), page({}, day=READINGS), None, weekday_id="ChristmasWeekdayJan2/")
        self.assertEqual((record["use"], record["readings"], record["weekday"]), ("proper", READINGS, "ChristmasWeekdayJan2/"))


class CorrectionTest(unittest.TestCase):
    CORRECTIONS = {"sets": {"OrdWeekday8Wednesday/I": {"gospel_acclamation": {
        "aelf": "Matthew 10:45", "corrected": "Mark 10:45", "why": "typo"}}}}

    def test_reviewed_corrections_replace_only_the_value_they_were_written_for(self):
        fill = {"sets": {"OrdWeekday8Wednesday/I": {"readings": {**READINGS, "gospel_acclamation": "Matthew 10:45"}}},
                "memorials": {}}
        self.assertEqual(apply_corrections(fill, self.CORRECTIONS), [])
        record = fill["sets"]["OrdWeekday8Wednesday/I"]
        self.assertEqual(record["readings"]["gospel_acclamation"], "Mark 10:45")
        self.assertEqual(record["corrections"], {"gospel_acclamation": "typo"})
        self.assertEqual(apply_corrections(fill, self.CORRECTIONS), [])   # applying twice changes nothing

    def test_a_correction_that_no_longer_matches_is_reported(self):
        fill = {"sets": {"OrdWeekday8Wednesday/I": {"readings": {**READINGS, "gospel_acclamation": "Mark 10:44"}}},
                "memorials": {}}
        stale = apply_corrections(fill, self.CORRECTIONS)
        self.assertEqual(len(stale), 1)
        self.assertEqual(fill["sets"]["OrdWeekday8Wednesday/I"]["readings"]["gospel_acclamation"], "Mark 10:44")
