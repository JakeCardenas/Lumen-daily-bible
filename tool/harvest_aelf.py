"""Fills lectionary gaps from AELF's daily Mass API (General Roman Calendar): citations only.

Run from tool/: python3 harvest_aelf.py [--max-pages 650]
Reads tool/data/harvest_needed.json, fetches at most --max-pages pages over the network (>= 1.5 s
apart, cached under tool/cache/aelf/), merges results into tool/data/lectionary_fill.json and writes
tool/data/fill_report.md for human review. Reading text is never stored in the repository.
"""
import argparse
import json
import re
import sys
from datetime import date

from lumen_data import litcal
from lumen_data.aelf import cache_file, fetch_day
from lumen_data.harvest import set_parts
from lumen_data.harvest import accept, aelf_date, apply_corrections, candidate_dates, classify_memorial
from lumen_data.lectionary import (events_by_date, find_entry, is_complete, primary_event, underlying_weekday,
                                   variants)
from lumen_data.net import BudgetExhausted, Fetcher
from lumen_data.paths import DATA

HARVEST_YEARS = range(2010, 2027)
NETWORK_TRIES_PER_NEED = 3
# Weekdays whose readings depend only on the date: a memorial that always displaces one keeps the whole page.
DATE_FIXED_WEEKDAY = re.compile(r"^(?:Christmas|Advent)Weekday[A-Z][a-z]{2}\d+/$")


def report(fill: dict) -> str:
    lines = ["# Lectionary fill report", "",
             "Citations taken from AELF's daily Mass readings (api.aelf.org, General Roman Calendar). "
             "No reading text is stored.", "",
             "## Reading sets", "", "| Set | Page date | AELF day | First reading | Gospel |", "|---|---|---|---|---|"]
    for set_id, record in fill["sets"].items():
        readings = record["readings"]
        lines.append(f"| {set_id} | {record['date']} | {record.get('day', '')} | "
                     f"{readings.get('first_reading', '')} | {readings.get('gospel', '')} |")
    corrected = [(set_id, kind, why) for set_id, record in fill["sets"].items()
                 for kind, why in record.get("corrections", {}).items()]
    if corrected:
        lines += ["", "## Corrections", "", "| Set | Reading | Why |", "|---|---|---|"]
        lines += [f"| {set_id} | {kind} | {why} |" for set_id, kind, why in corrected]
    lines += ["", "## Memorials", "", "| Memorial | Page date | AELF day | Proper readings |", "|---|---|---|---|"]
    for key, record in fill["memorials"].items():
        proper = "; ".join(f"{k}: {v}" for k, v in record.get("readings", {}).items()) or "none (weekday readings)"
        lines.append(f"| {key} | {record['date']} | {record.get('day', '')} | {proper} |")
    return "\n".join(lines) + "\n"


def slots_for(set_id: str, lect: dict) -> tuple[str, ...]:
    """The reading kinds the open data has for a set, even when they are empty."""
    key, cycle, variant = set_parts(set_id)
    entry = find_entry(lect, key, cycle)
    if entry is None:
        return ()
    options = dict(variants(entry))
    return tuple(options.get(variant or None) or options.get(variant) or next(iter(options.values())))


def weekday_readings(day: date, by_date: dict, lect: dict, fill: dict) -> tuple[str | None, dict | None]:
    """The id and readings of the weekday a memorial on [day] replaces; readings are None when unknown."""
    weekday = underlying_weekday(day, by_date, lect)
    if weekday is None:
        return None, None
    key, cycle = weekday
    entry = find_entry(lect, key, cycle)
    readings = variants(entry)[0][1] if entry is not None else {}
    if is_complete(readings):
        return f"{key}/{cycle}", readings
    return f"{key}/{cycle}", fill["sets"].get(f"{key}/{cycle}", {}).get("readings")


def page_date(need: dict, day: date) -> date:
    return aelf_date(need["set"], day) if need["kind"] == "set" else day


def cached_first(need: dict, days: list[date]) -> list[date]:
    """Pages already fetched cost nothing, so they are tried first (newest first within each group)."""
    return sorted(days, key=lambda day: not cache_file(page_date(need, day)).exists())


def cached_weekday(set_id: str, by_date: dict, lect: dict, fill: dict) -> dict | None:
    """A weekday's readings from pages already fetched, even when the calendar does not need that weekday.
    Kept in the fill, because a memorial's classification rests on it."""
    need = {"kind": "set", "set": set_id}
    for day in candidate_dates(need, by_date, before=date.today(), limit=12):
        if cache_file(day).exists():
            page = fetch_day(day, Fetcher(max_network=0))
            record = accept(need, day, page, slots_for(set_id, lect)) if page else None
            if record:
                fill["sets"][set_id] = record
                return record["readings"]
    return None


def harvest_day(need: dict, day: date, pages: Fetcher, by_date: dict, lect: dict, fill: dict) -> dict | None:
    """The fill record [day]'s AELF page gives for [need], if any."""
    if need["kind"] == "memorial":
        weekday_id, weekday = weekday_readings(day, by_date, lect, fill)
        date_fixed = bool(weekday_id and DATE_FIXED_WEEKDAY.match(weekday_id))
        if weekday is None and weekday_id and not date_fixed:
            weekday = cached_weekday(weekday_id, by_date, lect, fill)
        if weekday is None and not date_fixed:
            return None   # compared with the weekday once that is harvested
        page = fetch_day(day, pages)
        return classify_memorial(day, page, weekday, weekday_id) if page else None
    primary = primary_event(by_date[day])
    during_memorial = primary["grade"] == 3 and fill["memorials"].get(primary["event_key"], {}).get("use") == "weekday"
    is_need = primary["event_key"] == set_parts(need["set"])[0]
    grade = primary["grade"] if is_need and "Sunday" not in primary["name"] else None
    page_day = page_date(need, day)
    page = fetch_day(page_day, pages)
    return accept(need, page_day, page, slots_for(need["set"], lect), during_memorial, grade) if page else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-pages", type=int, default=650, help="network requests allowed (cached pages are free)")
    args = parser.parse_args()

    needs = json.loads((DATA / "harvest_needed.json").read_text(encoding="utf-8"))
    needs.sort(key=lambda need: need["kind"] == "memorial")   # sets first: memorials compare against weekday sets
    fill_path = DATA / "lectionary_fill.json"
    fill = json.loads(fill_path.read_text(encoding="utf-8")) if fill_path.exists() else {"sets": {}, "memorials": {}}
    calendars = Fetcher(min_interval=1.0)
    by_date = events_by_date([litcal.calendar_events(year, calendars) for year in HARVEST_YEARS])
    lect = litcal.lectionary(calendars)
    pages = Fetcher(min_interval=1.5, max_network=args.max_pages)
    weekday_memorials = frozenset(key for key, record in fill["memorials"].items() if record["use"] == "weekday")

    def weekday_of(day: date) -> tuple[str, str] | None:
        return underlying_weekday(day, by_date, lect)

    unresolved = []
    for need in needs:
        record, network_tries = None, 0
        for day in cached_first(need, candidate_dates(need, by_date, before=date.today(), limit=12,
                                                      weekday_of=weekday_of, weekday_memorials=weekday_memorials)):
            if not cache_file(page_date(need, day)).exists():
                if network_tries == NETWORK_TRIES_PER_NEED:
                    break
                network_tries += 1
            try:
                record = harvest_day(need, day, pages, by_date, lect, fill)
            except BudgetExhausted:
                break   # the dates left are not cached either; later needs may still be answered from the cache
            if record:
                break
        if record is None:
            unresolved.append(need)
        elif need["kind"] == "memorial":
            fill["memorials"][need["key"]] = record
        else:
            fill["sets"][need["set"]] = record

    stale = apply_corrections(fill, json.loads((DATA / "fill_corrections.json").read_text(encoding="utf-8")))
    for problem in stale:
        print("CORRECTION NO LONGER MATCHES:", problem)
    fill = {"sets": dict(sorted(fill["sets"].items())), "memorials": dict(sorted(fill["memorials"].items()))}
    fill_path.parent.mkdir(parents=True, exist_ok=True)
    fill_path.write_text(json.dumps(fill, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "fill_report.md").write_text(report(fill), encoding="utf-8")
    (DATA / "harvest_unresolved.json").write_text(json.dumps(unresolved, indent=2) + "\n", encoding="utf-8")
    print(f"network pages: {pages.network_requests}; reading sets: {len(fill['sets'])}; "
          f"memorials: {len(fill['memorials'])}; unresolved: {len(unresolved)}")
    return 0 if not unresolved and not stale else 1


if __name__ == "__main__":
    sys.exit(main())
