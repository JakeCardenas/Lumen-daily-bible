"""Fills lectionary gaps from USCCB daily readings pages: citations and lectionary numbers only.

Run from tool/: python3 harvest_usccb.py [--max-pages 600]
Reads tool/data/harvest_needed.json, fetches at most --max-pages pages over the network (>= 1.5 s
apart, cached under tool/cache/usccb/), merges results into tool/data/lectionary_fill.json and
writes tool/data/fill_report.md for human review. Reading text is never stored.
"""
import argparse
import json
import sys
from datetime import date

from lumen_data import litcal
from lumen_data.harvest import accept, candidate_dates
from lumen_data.lectionary import events_by_date
from lumen_data.net import Fetcher
from lumen_data.paths import DATA
from lumen_data.usccb import fetch_day

HARVEST_YEARS = range(2019, 2027)


def report(fill: dict) -> str:
    lines = ["# Lectionary fill report", "",
             "Citations and lectionary numbers taken from USCCB daily readings pages. No reading text is stored.", "",
             "## Reading sets", "", "| Set | Page date | Lectionary | First reading | Gospel |", "|---|---|---|---|---|"]
    for set_id, record in fill["sets"].items():
        readings = record["readings"]
        lines.append(f"| {set_id} | {record['date']} | {record.get('lectionary')} | "
                     f"{readings.get('first_reading', '')} | {readings.get('gospel', '')} |")
    lines += ["", "## Memorials", "", "| Memorial | Page date | Lectionary | Readings used |", "|---|---|---|---|"]
    for key, record in fill["memorials"].items():
        lines.append(f"| {key} | {record['date']} | {record.get('lectionary')} | {record['use']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-pages", type=int, default=600, help="network requests allowed (cached pages are free)")
    args = parser.parse_args()

    needs = json.loads((DATA / "harvest_needed.json").read_text(encoding="utf-8"))
    fill_path = DATA / "lectionary_fill.json"
    fill = json.loads(fill_path.read_text(encoding="utf-8")) if fill_path.exists() else {"sets": {}, "memorials": {}}
    by_date = events_by_date([litcal.calendar_events(year, Fetcher(min_interval=1.0)) for year in HARVEST_YEARS])
    pages = Fetcher(min_interval=1.5)
    unresolved = []
    for need in needs:
        record = None
        for day in candidate_dates(need, by_date, before=date.today()):
            if pages.network_requests >= args.max_pages:
                break
            page = fetch_day(day, pages)
            record = accept(need, day, page) if page else None
            if record:
                break
        if record is None:
            unresolved.append(need)
        elif need["kind"] == "memorial":
            fill["memorials"][need["key"]] = {k: v for k, v in record.items() if k != "readings"}
            if record["use"] == "proper":
                fill["sets"][f"{need['key']}/"] = record
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
