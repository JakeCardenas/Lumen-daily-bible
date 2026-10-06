"""Chooses past dates to look up on AELF and decides whether a page answers a need."""
import re
from datetime import date, timedelta

from .aelf import MASS_VARIANTS, AelfDay
from .citations import CitationError, parse, split_alternatives
from .lectionary import (CYCLE_DEPENDENT_SANCTORUM, DAY_NAMES, cycle_of, is_complete, ordered_readings,
                         primary_event, sunday_cycle)

FRENCH_DAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
WEEKDAY_CYCLES = {"Impaire": "I", "Paire": "II"}
_ORD_WEEKDAY = re.compile(r"^OrdWeekday(?P<week>\d+)(?P<day>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)$")


def set_parts(set_id: str) -> tuple[str, str, str]:
    key, rest = set_id.split("/", 1)
    cycle, _, variant = rest.partition("#")
    return key, cycle, variant


def candidate_dates(need: dict, by_date: dict[date, list[dict]], before: date, limit: int = 4,
                    weekday_of=None, weekday_memorials: frozenset[str] = frozenset()) -> list[date]:
    """Past dates (newest first) whose primary celebration is the needed one.

    Two kinds of dates follow, still newest first: a weekday displaced by a memorial that only the US
    keeps (St. Elizabeth Ann Seton) is still the celebration in AELF's General Roman Calendar; and a
    weekday displaced by one of [weekday_memorials], memorials known to keep the weekday readings, is
    read at that memorial's Mass. [weekday_of] gives the (key, cycle) of the weekday a memorial displaces.
    """
    key, cycle = (need["key"], "") if need["kind"] == "memorial" else set_parts(need["set"])[:2]
    primary_dates, displaced_dates, memorial_dates = [], [], []
    for day in sorted(by_date, reverse=True):
        if day >= before:
            continue
        primary = primary_event(by_date[day])
        if need["kind"] == "memorial":
            if primary["event_key"] == key and day.weekday() != 6:
                primary_dates.append(day)
            continue
        for event in by_date[day]:
            if event["event_key"] == key and (event is primary or event["grade"] == 0) and (
                    not cycle or cycle_of(event) == cycle
                    or (key in CYCLE_DEPENDENT_SANCTORUM and sunday_cycle(day) == cycle)):
                (primary_dates if event is primary else displaced_dates).append(day)
                break
        else:
            if (weekday_of and primary["grade"] == 3 and primary["event_key"] in weekday_memorials
                    and weekday_of(day) == (key, cycle)):
                memorial_dates.append(day)
    return (primary_dates + displaced_dates + memorial_dates)[:limit]


def _record(day: date, page: AelfDay) -> dict:
    info = page.info
    label = " / ".join(part for part in (info.get("ligne1"), info.get("ligne2")) if part)
    return {"date": day.isoformat(), "source": "aelf", "day": label}


def _obligatory_memorial(info: dict) -> bool:
    third = (info.get("ligne3") or "").lower()
    return third.startswith("mémoire") and "facultative" not in third


def _plain_weekday(info: dict) -> bool:
    return not _obligatory_memorial(info) and not {info.get("degre"), info.get("ligne2")} & {"Fête", "Solennité"}


def _page_matches(key: str, cycle: str, info: dict, during_memorial: bool = False) -> bool:
    match = _ORD_WEEKDAY.match(key)
    if match:
        return (info.get("temps_liturgique") == "ordinaire"
                and re.match(rf"^{int(match['week'])}(?:ère|ème|e) ", info.get("semaine") or "") is not None
                and info.get("jour") == FRENCH_DAYS[DAY_NAMES.index(match["day"])]
                and (during_memorial or not _obligatory_memorial(info))
                and (not cycle or WEEKDAY_CYCLES.get(info.get("annee")) == cycle))
    if cycle in ("A", "B", "C"):
        return info.get("annee") in (cycle, None)   # blank on some solemnities; the date was chosen by cycle
    if cycle in ("I", "II"):
        return WEEKDAY_CYCLES.get(info.get("annee")) == cycle and not _obligatory_memorial(info)
    if "Weekday" in key or key.startswith("DayAfterEpiphany"):
        return _plain_weekday(info)
    return True


# The US keeps the Ascension on the following Sunday; AELF's General Roman Calendar keeps Thursday.
AELF_DAY_SHIFT = {"Ascension": -3}
# Solemnities whose AELF page prints no rank.
UNRANKED_SOLEMNITIES = frozenset({"PalmSun", "AllSouls"})


def aelf_date(set_id: str, day: date) -> date:
    """The date of AELF's page for a set the US celebrates on [day]."""
    return day + timedelta(days=AELF_DAY_SHIFT.get(set_parts(set_id)[0], 0))


def _rank_matches(key: str, grade: int | None, info: dict) -> bool:
    """A feast's page must not be a solemnity (St. Matthias in a year he gives way to the Ascension),
    and a solemnity's page must be one."""
    if grade is None or grade < 4:
        return True
    rank = " ".join(info.get(field) or "" for field in ("degre", "ligne2", "fete"))
    if grade >= 6:
        return "Solennité" in rank or key in UNRANKED_SOLEMNITIES
    return "Solennité" not in rank


def _fit_slots(readings: dict, slots) -> dict:
    """AELF lists a feast's second reading as another first reading (Transfiguration: Daniel, then 2 Peter)."""
    first = split_alternatives(readings.get("first_reading") or "")
    if "second_reading" in slots and "second_reading" not in readings and len(first) == 2:
        return ordered_readings({**readings, "first_reading": first[0], "second_reading": first[1]})
    return readings


def accept(need: dict, day: date, page: AelfDay, slots=(), during_memorial: bool = False,
           grade: int | None = None) -> dict | None:
    """The fill record for a reading-set need, or None if this page does not answer it.

    [slots] are the reading kinds the open Lectionary data has for this set, even when empty.
    [during_memorial]: the page is a memorial known to keep the weekday readings, so it may answer a weekday.
    [grade]: LitCal's rank for a celebration that is not a Sunday, checked against AELF's.
    """
    key, cycle, variant = set_parts(need["set"])
    readings = page.masses.get(variant or "day")
    if readings is None and variant not in MASS_VARIANTS.values() and len(page.masses) == 1:
        readings = next(iter(page.masses.values()))   # e.g. All Souls: the one Mass AELF gives answers "schema_one"
    if not readings or not is_complete(readings) or not _page_matches(key, cycle, page.info, during_memorial):
        return None
    if not _rank_matches(key, grade, page.info):
        return None
    return {**_record(day, page), "readings": _fit_slots(readings, slots)}


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


def classify_memorial(day: date, page: AelfDay, weekday: dict | None, weekday_id: str | None = None) -> dict | None:
    """Whether a memorial keeps the weekday readings, and if not, which readings are its own.

    With no weekday to compare ([weekday] None), the whole page is kept, tied to [weekday_id].
    """
    readings = page.masses.get("day")
    if not readings or not is_complete(readings):
        return None
    if weekday is None:
        return {**_record(day, page), "use": "proper", "weekday": weekday_id, "readings": readings}
    if not is_complete(weekday):
        return None
    proper = {kind: citation for kind, citation in readings.items()
              if kind != "gospel_acclamation" and _anchor(kind, citation) != _anchor(kind, weekday.get(kind, ""))}
    if "gospel" in proper and "gospel_acclamation" in readings:
        proper = {"gospel_acclamation": readings["gospel_acclamation"], **proper}
    record = {**_record(day, page), "use": "proper" if proper else "weekday"}
    if proper:
        record["readings"] = proper
    return record


def apply_corrections(fill: dict, corrections: dict) -> list[str]:
    """Applies reviewed fixes for AELF typos. Returns the corrections that no longer match the harvested value."""
    stale = []
    for set_id, kinds in corrections.get("sets", {}).items():
        record = fill["sets"].get(set_id)
        for kind, fix in kinds.items():
            current = record["readings"].get(kind) if record else None
            if current == fix["aelf"]:
                record["readings"][kind] = fix["corrected"]
                record.setdefault("corrections", {})[kind] = fix["why"]
            elif current != fix["corrected"]:
                stale.append(f"{set_id} {kind}: expected {fix['aelf']!r}, found {current!r}")
    return stale
