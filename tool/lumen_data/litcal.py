"""Liturgical Calendar API data (https://litcal.johnromanodorazio.com, Apache License 2.0)."""
import json

from .net import Fetcher
from .paths import CACHE

CALENDAR_URL = "https://litcal.johnromanodorazio.com/api/dev/calendar/nation/US/{year}?year_type=CIVIL&locale=en_US"
LECTIONARY_URL = ("https://raw.githubusercontent.com/Liturgical-Calendar/LiturgicalCalendarAPI/development/"
                  "jsondata/sourcedata/rite/roman/lectionary/{name}/en.json")
LICENSE_URL = "https://raw.githubusercontent.com/Liturgical-Calendar/LiturgicalCalendarAPI/development/LICENSE"
LECTIONARY_FILES = (
    "dominicale_et_festivum_A", "dominicale_et_festivum_B", "dominicale_et_festivum_C",
    "feriale_per_annum_I", "feriale_per_annum_II",
    "feriale_tempus_adventus", "feriale_tempus_nativitatis", "feriale_tempus_paschatis", "feriale_tempus_quadragesimae",
    "sanctorum",
)


def calendar_events(year: int, fetcher: Fetcher) -> list[dict]:
    """Events dated in the given civil year for the United States calendar."""
    raw = fetcher.get(CALENDAR_URL.format(year=year), CACHE / "litcal" / f"calendar_US_{year}.json",
                      {"Accept": "application/json"})
    if raw is None:
        raise RuntimeError(f"Liturgical Calendar API has no US calendar for {year}")
    return [event for event in json.loads(raw)["litcal"] if event["date"].startswith(str(year))]


def lectionary(fetcher: Fetcher) -> dict[str, dict]:
    files = {}
    for name in LECTIONARY_FILES:
        raw = fetcher.get(LECTIONARY_URL.format(name=name), CACHE / "litcal" / f"{name}.json")
        if raw is None:
            raise RuntimeError(f"missing lectionary file {name}")
        files[name] = json.loads(raw)
    return files
