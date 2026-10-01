"""Reads reading citations (never text) from AELF's daily Mass API for the General Roman Calendar.

AELF (Association Episcopale Liturgique pour les pays Francophones) publishes the readings of the
Roman Lectionary at https://api.aelf.org. Only the references are used, converted to English names.
"""
import json
import re
from dataclasses import dataclass
from datetime import date

from .books import BY_ID
from .citations import CitationError
from .lectionary import ordered_readings
from .net import Fetcher
from .paths import CACHE

URL = "https://api.aelf.org/v1/messes/{d:%Y-%m-%d}/romain"

FRENCH_BOOKS = {
    "Gn": "GEN", "Ex": "EXO", "Lv": "LEV", "Nb": "NUM", "Dt": "DEU", "Jos": "JOS", "Jg": "JDG", "Rt": "RUT",
    "1 S": "1SA", "2 S": "2SA", "1 R": "1KI", "2 R": "2KI", "1 Ch": "1CH", "2 Ch": "2CH", "Esd": "EZR", "Ne": "NEH",
    "Tb": "TOB", "Jdt": "JDT", "Est": "EST", "1 M": "1MA", "2 M": "2MA", "Jb": "JOB", "Ps": "PSA", "Pr": "PRO",
    "Qo": "ECC", "Ct": "SNG", "Sg": "WIS", "Si": "SIR", "Is": "ISA", "Jr": "JER", "Lm": "LAM", "Ba": "BAR",
    "Ez": "EZK", "Dn": "DAN", "Os": "HOS", "Jl": "JOL", "Am": "AMO", "Ab": "OBA", "Jon": "JON", "Mi": "MIC",
    "Na": "NAM", "Ha": "HAB", "So": "ZEP", "Ag": "HAG", "Za": "ZEC", "Ml": "MAL",
    "Mt": "MAT", "Mc": "MRK", "Lc": "LUK", "Jn": "JHN", "Ac": "ACT", "Rm": "ROM", "1 Co": "1CO", "2 Co": "2CO",
    "Ga": "GAL", "Ep": "EPH", "Ph": "PHP", "Col": "COL", "1 Th": "1TH", "2 Th": "2TH", "1 Tm": "1TI", "2 Tm": "2TI",
    "Tt": "TIT", "Phm": "PHM", "He": "HEB", "Jc": "JAS", "1 P": "1PE", "2 P": "2PE", "1 Jn": "1JN", "2 Jn": "2JN",
    "3 Jn": "3JN", "Jude": "JUD", "Ap": "REV",
}
MASS_VARIANTS = {"messe de la veille au soir": "vigil", "messe de la nuit": "night", "messe de l'aurore": "dawn",
                 "messe du jour": "day"}
KINDS = {"lecture_1": "first_reading", "lecture_2": "second_reading", "lecture_3": "third_reading",
         "lecture_4": "fourth_reading", "lecture_5": "fifth_reading", "lecture_6": "sixth_reading",
         "lecture_7": "seventh_reading", "epitre": "epistle", "psaume": "responsorial_psalm", "evangile": "gospel"}
_CLEAN = str.maketrans({" ": " ", "–": "-", "—": "-", "‒": "-", "‐": "-", "‑": "-",
                        "’": "'"})


@dataclass(frozen=True)
class AelfDay:
    info: dict
    masses: dict[str, dict[str, str]]   # "vigil" | "night" | "dawn" | "day" -> readings


def to_citation(ref: str, default_book: str | None = None) -> str:
    """'Ps 110 (111), 1-2, 7-8, 9.10c' -> 'Psalm 111:1-2, 7-8, 9, 10c'."""
    text = re.sub(r"\s+", " ", ref.translate(_CLEAN)).strip().rstrip(".")
    text = re.sub(r"^cf\.?\s*", "", text, flags=re.IGNORECASE)
    book_id, rest = None, text
    match = re.match(r"^((?:[1-3] ?)?[A-Za-zÀ-ÿ]+) (.*)$", text)
    if match:
        book_id = FRENCH_BOOKS.get(re.sub(r"^([1-3]) ?", r"\1 ", match.group(1)))
        if book_id:
            rest = match.group(2)
    if book_id is None:
        if default_book is None or not re.match(r"^\d", text):
            raise CitationError(f"unknown book in AELF reference {ref!r}")
        book_id = default_book
    groups = []
    for group in (g.strip() for g in rest.split(";")):
        if not group:
            continue
        cross = re.fullmatch(r"(\d+) ?, ?(\d+[a-z]*) ?- ?(\d+) ?, ?(\d+[a-z]*)", group)
        if cross:
            groups.append(f"{cross[1]}:{cross[2]}-{cross[3]}:{cross[4]}")
            continue
        head, _, verses = group.partition(",")
        numbers = [int(n) for n in re.findall(r"\d+", head)]
        if not numbers:
            raise CitationError(f"no chapter in AELF reference {ref!r}")
        chapter = max(numbers) if book_id == "PSA" else numbers[0]   # "110 (111)": the Hebrew number is the larger
        verses = re.sub(r"\s*-\s*", "-", re.sub(r"\s*[.,]\s*", ", ", verses.strip()))
        groups.append(f"{chapter}:{verses}" if verses else str(chapter))
    name = "Psalm" if book_id == "PSA" else BY_ID[book_id].modern
    return f"{name} {'; '.join(groups)}"


def parse_day(payload: dict) -> AelfDay:
    masses: dict[str, dict[str, str]] = {}
    for mass in payload.get("messes") or []:
        variant = MASS_VARIANTS.get((mass.get("nom") or "").translate(_CLEAN).strip().lower())
        if variant is None or variant in masses:
            continue
        readings: dict[str, str] = {}
        for lecture in mass.get("lectures") or []:
            kind = KINDS.get(lecture.get("type"))
            ref = (lecture.get("ref") or "").strip()
            if not kind or not ref:
                continue
            try:
                citation = to_citation(ref, "PSA" if kind == "responsorial_psalm" else None)
            except CitationError:
                continue   # leaves the set incomplete, so the page is not used
            if kind in readings:
                if kind == "gospel":
                    readings[kind] += "|" + citation
                continue
            readings[kind] = citation
            verse = (lecture.get("ref_verset") or "").strip()
            if kind == "gospel" and verse:
                try:
                    readings["gospel_acclamation"] = to_citation(verse)
                except CitationError:
                    pass
        masses[variant] = ordered_readings(readings)
    return AelfDay(payload.get("informations") or {}, masses)


def fetch_day(day: date, fetcher: Fetcher) -> AelfDay | None:
    raw = fetcher.get(URL.format(d=day), CACHE / "aelf" / f"{day.isoformat()}.json", {"Accept": "application/json"})
    return None if raw is None else parse_day(json.loads(raw))
