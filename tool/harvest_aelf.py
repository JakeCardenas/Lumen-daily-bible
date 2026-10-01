"""Fills lectionary gaps from AELF's daily Mass API (General Roman Calendar): citations only.

Run from tool/: python3 harvest_aelf.py [--max-pages 650]
Reads tool/data/harvest_needed.json, fetches at most --max-pages pages over the network (>= 1.5 s
apart, cached under tool/cache/aelf/), merges results into tool/data/lectionary_fill.json and writes
tool/data/fill_report.md for human review. Reading text is never stored in the repository.
"""
import argparse
import json
import sys
from datetime import date

from lumen_data import litcal
from lumen_data.aelf import fetch_day
from lumen_data.harvest import accept, candidate_dates, classify_memorial
from lumen_data.lectionary import events_by_date, find_entry, is_complete, underlying_weekday, variants
from lumen_data.net import Fetcher
from lumen_data.paths import DATA

HARVEST_YEARS = range(2019, 2027)


def report(fill: dict) -> str:
    lines = ["# Lectionary fill report", "",
             "Citations taken from AELF's daily Mass readings (api.aelf.org, General Roman Calendar). "
             "No reading text is stored.", "",
             "## Reading sets", "", "| Set | Page date | AELF day | First reading | Gospel |", "|---|---|---|---|---|"]
    for set_id, record in fill["sets"].items():
        readings = record["readings"]
        lines.append(f"| {set_id} | {record['date']} | {record.get('day', '')} | "
                     f"{readings.get('first_reading', '')} | {readings.get('gospel', '')} |")
    lines += ["", "## Memorials", "", "| Memorial | Page date | AELF day | Proper readings |", "|---|---|---|---|"]
    for key, record in fill["memorials"].items():
        proper = "; ".join(f"{k}: {v}" for k, v in record.get("readings", {}).items()) or "none (weekday readings)"
        lines.append(f"| {key} | {record['date']} | {record.get('day', '')} | {proper} |")
    return "\n".join(lines) + "\n"


def weekday_readings(day: date, by_date: dict, lect: dict, fill: dict) -> dict | None:
    weekday = underlying_weekday(day, by_date, lect)
    if weekday is None:
        return None
    key, cycle = weekday
    entry = find_entry(lect, key, cycle)
    readings = variants(entry)[0][1] if entry is not None else {}
    if is_complete(readings):
        return readings
    return fill["sets"].get(f"{key}/{cycle}", {}).get("readings")


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
    pages = Fetcher(min_interval=1.5)
    unresolved = []
    for need in needs:
        record = None
        for day in candidate_dates(need, by_date, before=date.today()):
            if pages.network_requests >= args.max_pages:
                break
            if need["kind"] == "memorial":
                weekday = weekday_readings(day, by_date, lect, fill)
                if weekday is None:
                    continue
                page = fetch_day(day, pages)
                record = classify_memorial(day, page, weekday) if page else None
            else:
                page = fetch_day(day, pages)
                record = accept(need, day, page) if page else None
            if record:
                break
        if record is None:
            unresolved.append(need)
        elif need["kind"] == "memorial":
            fill["memorials"][need["key"]] = record
        else:
            fill["sets"][need["set"]] = record

    fill = {"sets": dict(sorted(fill["sets"].items())), "memorials": dict(sorted(fill["memorials"].items()))}
    fill_path.parent.mkdir(parents=True, exist_ok=True)
    fill_path.write_text(json.dumps(fill, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "fill_report.md").write_text(report(fill), encoding="utf-8")
    (DATA / "harvest_unresolved.json").write_text(json.dumps(unresolved, indent=2) + "\n", encoding="utf-8")
    print(f"network pages: {pages.network_requests}; reading sets: {len(fill['sets'])}; "
          f"memorials: {len(fill['memorials'])}; unresolved: {len(unresolved)}")
    return 0 if not unresolved else 1


if __name__ == "__main__":
    sys.exit(main())
