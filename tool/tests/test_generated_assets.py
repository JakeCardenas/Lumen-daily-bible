import json
import unittest

from lumen_data.bible import DouayIndex
from lumen_data.lectionary import spot_check, validate
from lumen_data.paths import ASSETS

CALENDAR = ASSETS / "liturgy" / "calendar_us.json"
BIBLE = ASSETS / "bible" / "douay_rheims.json"


@unittest.skipUnless(CALENDAR.exists() and BIBLE.exists(), "generated assets not built yet")
class GeneratedAssetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calendar = json.loads(CALENDAR.read_text(encoding="utf-8"))
        cls.douay = DouayIndex(json.loads(BIBLE.read_text(encoding="utf-8")))

    def test_covers_2026_through_2035(self):
        self.assertEqual((self.calendar["start"], self.calendar["end"]), ("2026-01-01", "2035-12-31"))
        self.assertEqual(len(self.calendar["days"]), 3652)

    def test_every_day_validates(self):
        self.assertEqual(validate(self.calendar, self.douay), [])

    def test_spot_checks(self):
        self.assertEqual(spot_check(self.calendar), [])

    def test_only_citations_are_stored(self):
        for readings in self.calendar["sets"].values():
            for reading in readings:
                self.assertLess(len(reading["citation"]), 120, reading["citation"])
