"""Assembles per-date Mass readings from Liturgical Calendar API data and harvested fills."""
import re
from dataclasses import dataclass
from datetime import date, timedelta

from .bible import DouayIndex
from .citations import CitationError, parse, split_alternatives
from .versification import MissingOverride, Versifier, format_passage

SUNDAY_FILES = {c: f"dominicale_et_festivum_{c}" for c in "ABC"}
WEEKDAY_FILES = {"I": "feriale_per_annum_I", "II": "feriale_per_annum_II"}
SEASON_FILES = ("feriale_tempus_adventus", "feriale_tempus_nativitatis", "feriale_tempus_paschatis",
                "feriale_tempus_quadragesimae")
CYCLE_DEPENDENT_SANCTORUM = frozenset({"Transfiguration"})
VIGIL_FOR = frozenset({"Christmas", "Pentecost", "Assumption", "NativityJohnBaptist", "StsPeterPaulAp"})
DAY_VARIANTS = {"Christmas": ("night", "dawn", "day")}
VARIANT_TITLES = {"vigil": "Vigil Mass (evening)", "night": "Mass during the Night", "dawn": "Mass at Dawn",
                  "day": "Mass during the Day"}
SOLEMNITY_KEYS = frozenset({"Christmas", "Easter", "Pentecost", "Ascension", "Epiphany", "Trinity", "CorpusChristi",
                            "ChristKing", "MaryMotherOfGod", "SacredHeart"})
DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
LABELS = {"first_reading": "First Reading", "second_reading": "Second Reading", "third_reading": "Third Reading",
          "fourth_reading": "Fourth Reading", "fifth_reading": "Fifth Reading", "sixth_reading": "Sixth Reading",
          "seventh_reading": "Seventh Reading", "epistle": "Epistle", "gospel": "Gospel",
          "palm_gospel": "Gospel at the Procession with Palms"}
_WEEKDAY_KEY = re.compile(r"^(?P<prefix>[A-Za-z]+Weekday\d+)(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)$")
_ORD_WEEKDAY = re.compile(r"^OrdWeekday(?P<week>\d+)(?P<day>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)$")


def event_date(event: dict) -> date:
    return date.fromisoformat(event["date"][:10])


def events_by_date(calendars: list[list[dict]]) -> dict[date, list[dict]]:
    out: dict[date, list[dict]] = {}
    for events in calendars:
        for event in events:
            out.setdefault(event_date(event), []).append(event)
    return out


def cycle_of(event: dict) -> str:
    value = (event.get("liturgical_year") or "").upper().replace("YEAR", "").strip()
    return value if value in ("A", "B", "C", "I", "II") else ""


def advent_start(year: int) -> date:
    christmas = date(year, 12, 25)
    days_back = (christmas.weekday() + 1) % 7 or 7   # to the Sunday before Christmas (Advent 4)
    return christmas - timedelta(days=days_back + 21)


def sunday_cycle(day: date) -> str:
    start_year = day.year if day >= advent_start(day.year) else day.year - 1
    return "ABC"[(start_year - 2022) % 3]


def is_vigil(event: dict) -> bool:
    return bool(event.get("is_vigil_mass"))


def primary_event(events: list[dict]) -> dict:
    """The celebration of the day. Optional memorials (grade 2) and vigil Masses never qualify."""
    regular = [e for e in events if not is_vigil(e)]
    candidates = [e for e in regular if e["grade"] != 2] or regular
    if not candidates:
        raise ValueError("a day has only vigil Masses")
    return max(candidates, key=lambda e: e["grade"])


def rank_label(event: dict) -> str | None:
    grade, key = event["grade"], event["event_key"]
    if "Sunday" in event["name"] or grade in (0, 1, 2):
        return None
    if grade == 3:
        return "Memorial"
    if grade in (4, 5):
        return "Feast"
    if grade == 6 or key in SOLEMNITY_KEYS:
        return "Solemnity"
    return None


def find_entry(lect: dict[str, dict], key: str, cycle: str):
    if cycle in SUNDAY_FILES and key in lect[SUNDAY_FILES[cycle]]:
        return lect[SUNDAY_FILES[cycle]][key]
    if cycle in WEEKDAY_FILES and key in lect[WEEKDAY_FILES[cycle]]:
        return lect[WEEKDAY_FILES[cycle]][key]
    for name in SEASON_FILES:
        if key in lect[name]:
            return lect[name][key]
    return lect["sanctorum"].get(key)


def variants(entry) -> list[tuple[str | None, dict]]:
    """Splits multi-Mass entries ({"vigil": {...}, "day": {...}}) into (name, readings) pairs."""
    if isinstance(entry, dict) and entry and all(isinstance(v, dict) for v in entry.values()):
        return list(entry.items())
    return [(None, entry if isinstance(entry, dict) else {})]


def is_complete(readings) -> bool:
    if not isinstance(readings, dict):
        return False
    if not (readings.get("first_reading") or "").strip() or not (readings.get("gospel") or "").strip():
        return False
    if not re.search(r"[:,]\s*\d", readings.get("responsorial_psalm") or ""):
        return False   # "Psalm 71" without verses is not usable
    try:
        for value in readings.values():
            if isinstance(value, str) and value.strip():
                for option in split_alternatives(value):
                    parse(option)
    except CitationError:
        return False
    return True


def ord_weekday_lectionary_number(key: str) -> int | None:
    """US Lectionary number of an Ordinary Time weekday, e.g. OrdWeekday27Monday -> 461."""
    match = _ORD_WEEKDAY.match(key)
    if match is None:
        return None
    return 305 + (int(match.group("week")) - 1) * 6 + DAY_NAMES.index(match.group("day"))


def label_for(kind: str, event: dict) -> str:
    if kind.startswith("responsorial_psalm"):
        return "Responsorial Psalm"
    if kind == "gospel_acclamation":
        lenten = event.get("liturgical_season") in ("LENT", "EASTER_TRIDUUM")
        return "Verse Before the Gospel" if lenten else "Alleluia"
    return LABELS.get(kind, kind.replace("_", " ").title())


def underlying_weekday(day: date, by_date: dict[date, list[dict]], lect: dict[str, dict]) -> tuple[str, str] | None:
    """(key, cycle) of the weekday that a memorial on this date replaces."""
    monday = day - timedelta(days=day.weekday())
    for offset in range(6):
        for event in by_date.get(monday + timedelta(days=offset), []):
            match = _WEEKDAY_KEY.match(event["event_key"])
            if match:
                return match.group("prefix") + DAY_NAMES[day.weekday()], cycle_of(event)
    for prefix in ("ChristmasWeekday", "AdventWeekday"):
        key = f"{prefix}{MONTHS[day.month - 1]}{day.day}"
        if find_entry(lect, key, "") is not None:
            return key, ""
    return None


def convert_readings(readings: dict, event: dict, versifier: Versifier, douay: DouayIndex) -> list[dict]:
    out = []
    for kind, value in readings.items():
        if not isinstance(value, str) or not value.strip():
            continue
        options = split_alternatives(value)
        passages = [versifier.convert(c) for c in parse(options[0])]
        out.append({
            "kind": kind,
            "label": label_for(kind, event),
            "citation": options[0],
            "alternatives": options[1:],
            "passages": [{"book": p.book, "ranges": [list(r) for r in p.ranges]} for p in passages],
            "douay": "; ".join(format_passage(p, douay) for p in passages),
            "differs": any(p.differs for p in passages),
            "partial": any(p.partial for p in passages),
        })
    return out


def _set_id(key: str, cycle: str, variant: str | None) -> str:
    return f"{key}/{cycle}" + (f"#{variant}" if variant else "")


@dataclass
class BuildResult:
    calendar: dict
    needs: dict[str, dict]
    missing_overrides: dict[str, dict]


class CalendarBuilder:
    def __init__(self, by_date: dict[date, list[dict]], lect: dict[str, dict], fill: dict,
                 versifier: Versifier, douay: DouayIndex):
        self.by_date = by_date
        self.lect = lect
        self.fill = fill
        self.versifier = versifier
        self.douay = douay
        self.sets: dict[str, list[dict]] = {}
        self.needs: dict[str, dict] = {}
        self.missing: dict[str, dict] = {}

    def build(self, start: date, end: date) -> BuildResult:
        days, day = {}, start
        while day <= end:
            days[day.isoformat()] = self._day(day)
            day += timedelta(days=1)
        calendar = {"version": 1, "calendar": "United States", "start": start.isoformat(), "end": end.isoformat(),
                    "sets": dict(sorted(self.sets.items())), "days": days}
        return BuildResult(calendar, dict(sorted(self.needs.items())), dict(sorted(self.missing.items())))

    def _day(self, day: date) -> dict:
        events = self.by_date.get(day)
        if not events:
            raise ValueError(f"no calendar events for {day}")
        primary = primary_event(events)
        masses = self._masses(primary, day)
        for event in events:
            if is_vigil(event) and event.get("is_vigil_for") in VIGIL_FOR:
                masses.append(self._vigil_mass(event, day))
        return {
            "name": primary["name"],
            "season": primary.get("liturgical_season_lcl") or "",
            "colors": list(primary.get("color") or []),
            "rank": rank_label(primary),
            "optional": [e["name"] for e in events if e["grade"] == 2 and not is_vigil(e) and e is not primary],
            "masses": [m for m in masses if m is not None],
        }

    def _masses(self, event: dict, day: date) -> list[dict | None]:
        if event["grade"] == 3:
            return [self._memorial_mass(event, day)]
        key, cycle = event["event_key"], cycle_of(event)
        if key in CYCLE_DEPENDENT_SANCTORUM:
            cycle = sunday_cycle(day)
        options = variants(self._entry(key, cycle, day))
        if len(options) == 1:
            name, readings = options[0]
            return [self._mass(None, _set_id(key, cycle, name), readings, event, day)]
        names = [n for n, _ in options]
        wanted = DAY_VARIANTS.get(key) or (("day",) if "day" in names else (names[0],))
        chosen = [(n, r) for n, r in options if n in wanted]
        titled = len(chosen) > 1
        return [self._mass(VARIANT_TITLES.get(n) if titled else None, _set_id(key, cycle, n), r, event, day)
                for n, r in chosen]

    def _memorial_mass(self, event: dict, day: date) -> dict | None:
        key = event["event_key"]
        memorial = self.fill["memorials"].get(key)
        if memorial is None:
            self.needs.setdefault(f"memorial:{key}", {"kind": "memorial", "key": key, "first_date": day.isoformat()})
            return None
        if memorial["use"] == "proper":
            return self._mass(None, f"{key}/", None, event, day)
        weekday = underlying_weekday(day, self.by_date, self.lect)
        if weekday is None:
            raise ValueError(f"cannot find the weekday that {key} replaces on {day}")
        weekday_key, weekday_cycle = weekday
        readings = variants(self._entry(weekday_key, weekday_cycle, day))[0][1]
        return self._mass(None, f"{weekday_key}/{weekday_cycle}", readings, event, day)

    def _vigil_mass(self, event: dict, day: date) -> dict | None:
        target, cycle = event["is_vigil_for"], cycle_of(event)
        for name, readings in variants(self._entry(target, cycle, day + timedelta(days=1))):
            if name == "vigil":
                return self._mass(VARIANT_TITLES["vigil"], _set_id(target, cycle, name), readings, event, day)
        return None

    def _entry(self, key: str, cycle: str, day: date):
        entry = find_entry(self.lect, key, cycle)
        if entry is None and not cycle:
            entry = find_entry(self.lect, key, sunday_cycle(day))
        return entry

    def _mass(self, title: str | None, set_id: str, readings, event: dict, day: date) -> dict | None:
        if set_id not in self.sets:
            source = readings if is_complete(readings) else self.fill["sets"].get(set_id, {}).get("readings")
            if source is None:
                self.needs.setdefault(set_id, {"kind": "set", "set": set_id, "first_date": day.isoformat()})
                return None
            try:
                self.sets[set_id] = convert_readings(source, event, self.versifier, self.douay)
            except MissingOverride as missing:
                self.missing[missing.key] = missing.proposal
                return None
        return {"title": title, "set": set_id}


def validate(calendar: dict, douay: DouayIndex) -> list[str]:
    problems = []
    day, end = date.fromisoformat(calendar["start"]), date.fromisoformat(calendar["end"])
    while day <= end:
        entry = calendar["days"].get(day.isoformat())
        if entry is None or not entry["masses"]:
            problems.append(f"{day}: no Mass readings")
        for mass in (entry or {}).get("masses", []):
            readings = calendar["sets"].get(mass["set"])
            if not readings:
                problems.append(f"{day}: reading set {mass['set']} is missing")
                continue
            kinds = {r["kind"] for r in readings}
            if "gospel" not in kinds:
                problems.append(f"{day}: {mass['set']} has no Gospel")
            if not kinds - {"gospel", "gospel_acclamation", "palm_gospel"}:
                problems.append(f"{day}: {mass['set']} has only a Gospel")
            for reading in readings:
                for passage in reading["passages"]:
                    for c1, v1, c2, v2 in passage["ranges"]:
                        if (c1, v1) > (c2, v2) or not douay.has(passage["book"], c1, v1) or not douay.has(passage["book"], c2, v2):
                            problems.append(f"{day}: {passage['book']} {c1}:{v1}-{c2}:{v2} is not in Douay-Rheims")
        day += timedelta(days=1)
    return problems


def spot_check(calendar: dict) -> list[str]:
    """Known dates in the US calendar that the data must get right."""
    days, sets = calendar["days"], calendar["sets"]

    def citation(iso: str, kind: str) -> str:
        readings = sets[days[iso]["masses"][0]["set"]]
        found = next((r["citation"] for r in readings if r["kind"] == kind), "")
        return re.sub(r"\s+", "", found)

    checks = [
        ("Ash Wednesday 2026", lambda: "Ash Wednesday" in days["2026-02-18"]["name"]),
        ("Easter 2026", lambda: "Easter" in days["2026-04-05"]["name"]),
        ("Ascension on Sunday 2026", lambda: "Ascension" in days["2026-05-17"]["name"]),
        ("Christmas Masses", lambda: [m["title"] for m in days["2026-12-25"]["masses"]]
            == ["Mass during the Night", "Mass at Dawn", "Mass during the Day"]),
        ("Christmas Eve vigil", lambda: [m["title"] for m in days["2026-12-24"]["masses"]] == [None, "Vigil Mass (evening)"]),
        ("2026-10-05 readings", lambda: citation("2026-10-05", "first_reading") == "Galatians1:6-12"
            and citation("2026-10-05", "gospel") == "Luke10:25-37"),
    ]
    for year in range(date.fromisoformat(calendar["start"]).year, date.fromisoformat(calendar["end"]).year + 1):
        if date(year, 12, 8).weekday() == 6:
            iso = f"{year}-12-09"
            checks.append((f"Immaculate Conception moved in {year}",
                           lambda iso=iso: "Immaculate Conception" in days[iso]["name"]))
    problems = []
    for name, check in checks:
        try:
            ok = check()
        except (KeyError, IndexError):
            ok = False
        if not ok:
            problems.append(f"spot check failed: {name}")
    return problems
