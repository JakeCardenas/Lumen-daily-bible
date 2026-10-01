"""Chooses past dates to look up on AELF and decides whether a page answers a need."""
import re
from datetime import date

from .aelf import AelfDay
from .citations import CitationError, parse, split_alternatives
from .lectionary import CYCLE_DEPENDENT_SANCTORUM, DAY_NAMES, cycle_of, is_complete, primary_event, sunday_cycle

FRENCH_DAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
WEEKDAY_CYCLES = {"Impaire": "I", "Paire": "II"}
_ORD_WEEKDAY = re.compile(r"^OrdWeekday(?P<week>\d+)(?P<day>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)$")


def _parts(set_id: str) -> tuple[str, str, str]:
    key, rest = set_id.split("/", 1)
    cycle, _, variant = rest.partition("#")
    return key, cycle, variant


def candidate_dates(need: dict, by_date: dict[date, list[dict]], before: date, limit: int = 4) -> list[date]:
    """Past dates (newest first) whose primary celebration is the needed one."""
    key, cycle = (need["key"], "") if need["kind"] == "memorial" else _parts(need["set"])[:2]
    found = []
    for day in sorted(by_date, reverse=True):
        if day >= before:
            continue
        primary = primary_event(by_date[day])
        if need["kind"] == "memorial":
            matches = primary["event_key"] == key and day.weekday() != 6
        else:
            matches = primary["event_key"] == key and (
                not cycle or cycle_of(primary) == cycle
                or (key in CYCLE_DEPENDENT_SANCTORUM and sunday_cycle(day) == cycle))
        if matches:
            found.append(day)
            if len(found) == limit:
                break
    return found


def _record(day: date, page: AelfDay) -> dict:
    info = page.info
    label = " / ".join(part for part in (info.get("ligne1"), info.get("ligne2")) if part)
    return {"date": day.isoformat(), "source": "aelf", "day": label}


def _obligatory_memorial(info: dict) -> bool:
    third = (info.get("ligne3") or "").lower()
    return third.startswith("mémoire") and "facultative" not in third


def _page_matches(key: str, cycle: str, info: dict) -> bool:
    match = _ORD_WEEKDAY.match(key)
    if match:
        return (info.get("temps_liturgique") == "ordinaire"
                and re.match(rf"^{int(match['week'])}(?:ère|ème|e) ", info.get("semaine") or "") is not None
                and info.get("jour") == FRENCH_DAYS[DAY_NAMES.index(match["day"])]
                and not _obligatory_memorial(info)
                and (not cycle or WEEKDAY_CYCLES.get(info.get("annee")) == cycle))
    if cycle in ("A", "B", "C"):
        return info.get("annee") == cycle
    if cycle in ("I", "II"):
        return WEEKDAY_CYCLES.get(info.get("annee")) == cycle and not _obligatory_memorial(info)
    return True


def accept(need: dict, day: date, page: AelfDay) -> dict | None:
    """The fill record for a reading-set need, or None if this page does not answer it."""
    key, cycle, variant = _parts(need["set"])
    readings = page.masses.get(variant or "day")
    if readings is None and not variant and len(page.masses) == 1:
        readings = next(iter(page.masses.values()))
    if not readings or not is_complete(readings) or not _page_matches(key, cycle, page.info):
        return None
    return {**_record(day, page), "readings": readings}


def _anchor(kind: str, citation: str) -> tuple | None:
    """Where a reading starts; psalms by number only. Formatting differences between sources don't matter."""
    try:
        first = parse(split_alternatives(citation)[0])[0]
    except (CitationError, IndexError):
        return None
    if first.is_whole_chapter:
        return first.book, first.chapters[0]
    start = first.spans[0].start
    return (first.book, start.chapter) if kind == "responsorial_psalm" else (first.book, start.chapter, start.verse)


def classify_memorial(day: date, page: AelfDay, weekday: dict) -> dict | None:
    """Whether a memorial keeps the weekday readings, and if not, which readings are its own."""
    readings = page.masses.get("day")
    if not readings or not is_complete(readings) or not is_complete(weekday):
        return None
    proper = {kind: citation for kind, citation in readings.items()
              if kind != "gospel_acclamation" and _anchor(kind, citation) != _anchor(kind, weekday.get(kind, ""))}
    if "gospel" in proper and "gospel_acclamation" in readings:
        proper = {"gospel_acclamation": readings["gospel_acclamation"], **proper}
    record = {**_record(day, page), "use": "proper" if proper else "weekday"}
    if proper:
        record["readings"] = proper
    return record
