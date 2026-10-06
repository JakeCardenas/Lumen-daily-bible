"""Reads reading citations (never text) from AELF's daily Mass API for the General Roman Calendar.

AELF (Association Episcopale Liturgique pour les pays Francophones) publishes the readings of the
Roman Lectionary at https://api.aelf.org. Only the references are used, converted to English names.
"""
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .books import BY_ID
from .citations import SINGLE_CHAPTER_BOOKS, CitationError
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
    "3 Jn": "3JN", "Jude": "JUD", "Ap": "REV", "Jean": "JHN",
}
MASS_VARIANTS = {"messe de la veille au soir": "vigil", "messe de la nuit": "night", "messe de l'aurore": "dawn",
                 "messe du jour": "day", "messe de la passion": "day"}
PROCESSION = "procession des rameaux"   # its Gospel is read before the Mass of the Passion
KINDS = {"lecture_1": "first_reading", "lecture_2": "second_reading", "lecture_3": "third_reading",
         "lecture_4": "fourth_reading", "lecture_5": "fifth_reading", "lecture_6": "sixth_reading",
         "lecture_7": "seventh_reading", "epitre": "epistle", "psaume": "responsorial_psalm", "cantique": "responsorial_psalm",
         "evangile": "gospel"}
_CLEAN = str.maketrans({" ": " ", "–": "-", "—": "-", "‒": "-", "‐": "-", "‑": "-",
                        "’": "'"})


@dataclass(frozen=True)
class AelfDay:
    info: dict
    masses: dict[str, dict[str, str]]   # "vigil" | "night" | "dawn" | "day" -> readings


_BOOK_AT_START = re.compile(r"^((?:[1-3] ?)?[A-Za-zÀ-ÿ]+) ?(\d.*)$")
_CROSS_CHAPTER = re.compile(r"(\d+[a-z]*)\s*[–—]\s*(\d+)\s*,\s*(\d+[a-z]*)")   # AELF dashes between chapters
_NOTE = re.compile(r"\s*[(\[][^)\]]*[A-Za-zÀ-ÿ]{3,}[^)\]]*[)\]]")   # "(lecture brève)", not "(116b)"


def _book_at_start(text: str) -> tuple[str, str] | None:
    match = _BOOK_AT_START.match(text)
    if match:
        book_id = FRENCH_BOOKS.get(re.sub(r"^([1-3]) ?", r"\1 ", match.group(1)))
        if book_id:
            return book_id, match.group(2)
    return None


def _without_label(text: str) -> str:
    """Drops leading words that are not part of the reference: 'cf.', '[CANTIQUE]', 'Stabat Mater.'."""
    words = text.split(" ")
    for i, word in enumerate(words):
        rest = " ".join(words[i:])
        if _book_at_start(rest) or re.search(r"\d", word):
            return rest
    return text


def _verses(verses: str) -> str:
    """'2a.c.3bc, 15-16a' -> '2a, 2c, 3bc, 15-16a'."""
    verses = re.sub(r"\s+et\s+", ", ", verses)
    verses = re.sub(r"\s*,\s*-\s*", "-", verses)            # "11,-12ab"
    verses = re.sub(r"(\d) ([a-z]+)\b", r"\1\2", verses)    # "8 cde"
    verses = re.sub(r"\s*-\s*", "-", verses)
    items = []
    for item in (i for i in re.split(r"\s*[.,]\s*", verses) if i):
        if re.fullmatch(r"[a-z]+", item) and items:          # "2a.c": the letter continues the last verse
            item = re.findall(r"\d+", items[-1])[-1] + item
        items.append(item)
    return ", ".join(items)


def _hebrew_psalm(head: str, ref: str) -> int:
    """AELF numbers psalms the Greek way, adding the Hebrew number in brackets: '110 (111)'."""
    numbers = re.findall(r"(\d+)([a-z]?)", head.lower())   # "9A" too
    if not numbers:
        raise CitationError(f"no psalm number in AELF reference {ref!r}")
    if len(numbers) > 1:
        return max(int(n) for n, _ in numbers)   # the Hebrew number is the larger
    greek, part = int(numbers[0][0]), numbers[0][1]
    if greek <= 8 or greek >= 148:
        return greek
    if 10 <= greek <= 112 or 116 <= greek <= 145:
        return greek + 1
    split = {(9, "a"): 9, (9, "b"): 10, (113, "a"): 114, (113, "b"): 115}
    if (greek, part) in split:
        return split[greek, part]
    raise CitationError(f"Greek psalm {greek}{part} has no single Hebrew number: {ref!r}")   # verses differ too


def to_citation(ref: str, default_book: str | None = None) -> str:
    """'Ps 110 (111), 1-2, 7-8, 9.10c' -> 'Psalm 111:1-2, 7-8, 9, 10c'."""
    text = _CROSS_CHAPTER.sub(r"\1-\2:\3", ref.replace("\xa0", " "))   # "31 – 5, 1": into chapter 5
    text = re.sub(r"\s+", " ", _NOTE.sub("", text.translate(_CLEAN))).strip().rstrip(".")
    text = _without_label(text)
    found = _book_at_start(text)
    if found:
        book_id, rest = found
    else:
        if default_book is None or not re.match(r"^\d", text):
            raise CitationError(f"unknown book in AELF reference {ref!r}")
        book_id, rest = default_book, text
    parts = []
    for group in (g.strip() for g in rest.split(";")):
        if not group:
            continue
        switch = _book_at_start(group)   # "1 S 3, 9 ; Jn 6, 68c"
        if switch:
            book_id, group = switch
        parts.append((book_id, _chapter_and_verses(book_id, group, ref)))
    out, previous = [], None
    for book_id, text in parts:
        out.append(text if book_id == previous else f"{'Psalm' if book_id == 'PSA' else BY_ID[book_id].modern} {text}")
        previous = book_id
    return "; ".join(out)


def _chapter_and_verses(book_id: str, group: str, ref: str) -> str:
    head, _, verses = group.partition(",")
    if not verses and book_id in SINGLE_CHAPTER_BOOKS:   # "Phm 7-20"
        head, verses = "1", group
    elif not verses:   # "2 6-11": the comma after the chapter is missing
        missing_comma = re.fullmatch(r"(\d+[a-z]?(?: ?\(\d+[a-z]?\))?) (\d.*)", group)
        if missing_comma:
            head, verses = missing_comma.groups()
    if book_id == "PSA":
        chapter = _hebrew_psalm(head, ref)
    else:
        numbers = re.findall(r"\d+", head)
        if not numbers:
            raise CitationError(f"no chapter in AELF reference {ref!r}")
        chapter = int(numbers[0])
    verses = _verses(verses.strip())
    return f"{chapter}:{verses}" if verses else str(chapter)


def _citation(kind: str, ref: str) -> str | None:
    try:
        return to_citation(ref, "PSA" if kind == "responsorial_psalm" else None)
    except CitationError:
        return None


def parse_day(payload: dict) -> AelfDay:
    masses: dict[str, dict[str, str]] = {}
    palm_gospels: list[str] = []
    for mass in payload.get("messes") or []:
        name = re.sub(r"\s+", " ", (mass.get("nom") or "").translate(_CLEAN)).strip().lower()
        lectures = mass.get("lectures") or []
        if name == PROCESSION:
            palm_gospels += [c for l in lectures if l.get("type") in ("evangile", "entree_messianique")
                             if (c := _citation("gospel", (l.get("ref") or "").strip()))]
            continue
        variant = MASS_VARIANTS.get(name, name)
        if variant in masses:
            continue
        readings: dict[str, str] = {}
        unreadable = False
        for lecture in lectures:
            kind = KINDS.get(lecture.get("type"))
            ref = (lecture.get("ref") or "").strip()
            if not kind or not ref:
                continue
            citation = _citation(kind, ref)
            if citation is None:
                unreadable = True
                continue
            if kind in readings:   # a second entry of the same kind is an alternative (often the short form)
                readings[kind] += "|" + citation
                continue
            readings[kind] = citation
            verse = (lecture.get("ref_verset") or "").strip()
            if kind == "gospel" and verse:
                try:
                    readings["gospel_acclamation"] = to_citation(verse)
                except CitationError:
                    pass
        masses[variant] = {} if unreadable else ordered_readings(readings)   # never use a partly read Mass
    if palm_gospels and "day" in masses:
        masses["day"] = ordered_readings({**masses["day"], "palm_gospel": "|".join(palm_gospels)})
    return AelfDay(payload.get("informations") or {}, masses)


def cache_file(day: date) -> Path:
    return CACHE / "aelf" / f"{day.isoformat()}.json"


def fetch_day(day: date, fetcher: Fetcher) -> AelfDay | None:
    raw = fetcher.get(URL.format(d=day), cache_file(day), {"Accept": "application/json"})
    return None if raw is None else parse_day(json.loads(raw))
