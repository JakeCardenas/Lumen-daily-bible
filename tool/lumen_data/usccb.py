"""Reads reading citations and lectionary numbers (never text) from USCCB daily readings pages."""
import html
import re
from dataclasses import dataclass
from datetime import date

from .net import Fetcher
from .paths import CACHE

URL = "https://bible.usccb.org/bible/readings/{d:%m%d%y}.cfm"
HEADINGS = {
    "reading 1": "first_reading", "reading i": "first_reading", "first reading": "first_reading",
    "responsorial psalm": "responsorial_psalm",
    "reading 2": "second_reading", "reading ii": "second_reading", "second reading": "second_reading",
    "alleluia": "gospel_acclamation", "verse before the gospel": "gospel_acclamation",
    "gospel acclamation": "gospel_acclamation",
    "gospel": "gospel",
}


@dataclass(frozen=True)
class UsccbDay:
    title: str
    lectionary: int | None
    readings: dict[str, str]


def _clean(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def parse_page(page: str) -> UsccbDay:
    title_match = re.search(r"<title>(.*?)</title>", page, re.S)
    title = _clean(title_match.group(1)).split("|")[0].strip() if title_match else ""
    number = re.search(r"Lectionary:\s*(\d+)", page)
    readings: dict[str, str] = {}
    for chunk in page.split('<h3 class="name">')[1:]:
        key = HEADINGS.get(_clean(chunk.split("</h3>", 1)[0]).lower())
        address = re.search(r'<div class="address">(.*?)</div>', chunk, re.S)
        if key and address and key not in readings:
            citation = _clean(address.group(1))
            if citation:
                readings[key] = citation
    return UsccbDay(title, int(number.group(1)) if number else None, readings)


def fetch_day(day: date, fetcher: Fetcher) -> UsccbDay | None:
    raw = fetcher.get(URL.format(d=day), CACHE / "usccb" / f"{day.isoformat()}.html")
    return None if raw is None else parse_page(raw.decode("utf-8", "replace"))
