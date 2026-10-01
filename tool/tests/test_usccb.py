import unittest
from datetime import date
from pathlib import Path

from lumen_data.usccb import URL, parse_page

FIXTURE = Path(__file__).parent / "fixtures" / "usccb_day.html"


class UsccbTest(unittest.TestCase):
    def test_parses_title_lectionary_number_and_first_citation_per_heading(self):
        day = parse_page(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(day.title, "Monday of the Twenty-seventh Week in Ordinary Time")
        self.assertEqual(day.lectionary, 461)
        self.assertEqual(day.readings, {
            "first_reading": "Galatians 1:6-12",
            "responsorial_psalm": "Psalm 111:1b-2, 7-8, 9, 10c",
            "gospel_acclamation": "John 13:34",
            "gospel": "Luke 10:25-37",
        })

    def test_page_without_readings(self):
        day = parse_page("<html><title>Nothing</title></html>")
        self.assertIsNone(day.lectionary)
        self.assertEqual(day.readings, {})

    def test_url_format(self):
        self.assertEqual(URL.format(d=date(2026, 10, 5)), "https://bible.usccb.org/bible/readings/100526.cfm")
