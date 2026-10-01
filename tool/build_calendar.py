"""Builds assets/liturgy/calendar_us.json (US calendar, 2026-2035).

Run from tool/: python3 build_calendar.py
Exit codes: 0 written; 2 run harvest_usccb.py first; 3 review tool/data/dc_overrides_todo.json;
4 validation or spot checks failed.
"""
import json
import sys
from datetime import date

from lumen_data import litcal
from lumen_data.bible import DouayIndex
from lumen_data.lectionary import CalendarBuilder, events_by_date, spot_check, validate
from lumen_data.net import Fetcher
from lumen_data.paths import ASSETS, CACHE, DATA
from lumen_data.versification import TvtmsMap, Versifier

START, END = date(2026, 1, 1), date(2035, 12, 31)
TVTMS_URL = ("https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Versification/"
             "TVTMS%20-%20Translators%20Versification%20Traditions%20with%20Methodology%20for%20Standardisation"
             "%20for%20Eng%2BHeb%2BLat%2BGrk%2BOthers%20-%20STEPBible.org%20CC%20BY.txt")


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    fetcher = Fetcher(min_interval=1.0)
    by_date = events_by_date([litcal.calendar_events(year, fetcher) for year in range(START.year, END.year + 1)])
    lect = litcal.lectionary(fetcher)
    douay = DouayIndex(json.loads((ASSETS / "bible" / "douay_rheims.json").read_text(encoding="utf-8")))
    tvtms = fetcher.get(TVTMS_URL, CACHE / "tvtms.txt").decode("utf-8", "replace")
    versifier = Versifier(douay, TvtmsMap.parse(tvtms, "Hebrew"), TvtmsMap.parse(tvtms, "Greek"),
                          load_json(DATA / "dc_overrides.json", {}))
    fill = load_json(DATA / "lectionary_fill.json", {"sets": {}, "memorials": {}})
    result = CalendarBuilder(by_date, lect, fill, versifier, douay).build(START, END)

    if result.needs:
        write_json(DATA / "harvest_needed.json", list(result.needs.values()))
        kinds = {k: sum(1 for n in result.needs.values() if n["kind"] == k) for k in ("set", "memorial")}
        print(f"{len(result.needs)} needs ({kinds['set']} reading sets, {kinds['memorial']} memorials). "
              "Next: python3 harvest_usccb.py")
        return 2
    if result.missing_overrides:
        write_json(DATA / "dc_overrides_todo.json", result.missing_overrides)
        print(f"{len(result.missing_overrides)} deuterocanonical citations need a reviewed mapping: "
              "tool/data/dc_overrides_todo.json")
        return 3
    problems = validate(result.calendar, douay) + spot_check(result.calendar)
    if problems:
        for problem in problems[:60]:
            print("PROBLEM:", problem)
        print(f"{len(problems)} problems; nothing written")
        return 4
    out = ASSETS / "liturgy" / "calendar_us.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result.calendar, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for leftover in ("harvest_needed.json", "dc_overrides_todo.json"):
        (DATA / leftover).unlink(missing_ok=True)
    print(f"wrote {out}: {len(result.calendar['days'])} days, {len(result.calendar['sets'])} reading sets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
