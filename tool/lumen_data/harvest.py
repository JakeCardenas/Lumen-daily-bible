"""Chooses past dates to look up on USCCB and decides whether a page answers a need."""
from datetime import date

from .lectionary import (CYCLE_DEPENDENT_SANCTORUM, cycle_of, is_complete, ord_weekday_lectionary_number,
                         primary_event, sunday_cycle)
from .usccb import UsccbDay

WEEKDAY_LECTIONARY = range(175, 509)   # Advent, Christmas, Lent, Easter and Ordinary Time weekday numbers
SEPARATE_PAGE_VARIANTS = frozenset({"vigil", "night", "dawn"})


def _parts(set_id: str) -> tuple[str, str, str]:
    key, rest = set_id.split("/", 1)
    cycle, _, variant = rest.partition("#")
    return key, cycle, variant


def candidate_dates(need: dict, by_date: dict[date, list[dict]], before: date, limit: int = 4) -> list[date]:
    """Past dates (newest first) whose primary celebration is the needed one."""
    if need["kind"] == "set":
        key, cycle, variant = _parts(need["set"])
        if variant in SEPARATE_PAGE_VARIANTS:
            return []   # these Masses have their own USCCB pages; resolve by hand
    found = []
    for day in sorted(by_date, reverse=True):
        if day >= before:
            continue
        primary = primary_event(by_date[day])
        if need["kind"] == "memorial":
            matches = primary["event_key"] == need["key"] and day.weekday() != 6
        else:
            matches = primary["event_key"] == key and (
                not cycle or cycle_of(primary) == cycle
                or (key in CYCLE_DEPENDENT_SANCTORUM and sunday_cycle(day) == cycle))
        if matches:
            found.append(day)
            if len(found) == limit:
                break
    return found


def accept(need: dict, day: date, page: UsccbDay) -> dict | None:
    record = {"date": day.isoformat(), "lectionary": page.lectionary, "title": page.title}
    if need["kind"] == "memorial":
        if page.lectionary is None:
            return None
        record["use"] = "weekday" if page.lectionary in WEEKDAY_LECTIONARY else "proper"
        if record["use"] == "proper":
            if not is_complete(page.readings):
                return None
            record["readings"] = page.readings
        return record
    key, _, _ = _parts(need["set"])
    expected = ord_weekday_lectionary_number(key)
    if expected is not None and page.lectionary != expected:
        return None
    if not is_complete(page.readings):
        return None
    record["readings"] = page.readings
    return record
