"""Maps lectionary citations (modern numbering) to Douay-Rheims (Vulgate) numbering.

Hebrew-numbered books use STEPBible's TVTMS data (Tyndale House, CC BY 4.0); the New Testament
uses TVTMS's Greek-to-Latin rows where the Vulgate splits verses differently; Daniel shares the
Vulgate's numbering. Books the US Lectionary numbers from the Greek
(Tobit, Judith, Wisdom, Sirach, Baruch, 1-2 Maccabees) need a reviewed entry in
tool/data/dc_overrides.json, because no single numbering scheme matches them.
"""
import re
from dataclasses import dataclass

from .bible import DouayIndex
from .books import BY_ID, Book
from .citations import Citation, Point, citation_key

Ref = tuple[int, int]
Range = tuple[int, int, int, int]

# Esther's Greek additions as lettered in the US Lectionary -> Douay-Rheims.
# letter: [(first verse, last verse, Douay chapter, Douay verse of the first)]. Source: STEPBible TVTMS notes.
ESTHER_ADDITIONS: dict[str, list[tuple[int, int, int, int]]] = {
    "A": [(1, 11, 11, 2), (12, 17, 12, 1)],
    "B": [(1, 7, 13, 1)],
    "C": [(1, 11, 13, 8), (12, 30, 14, 1)],
    "E": [(1, 24, 16, 1)],
    "F": [(1, 10, 10, 4), (11, 11, 11, 1)],
}


class VersificationError(ValueError):
    pass


class MissingOverride(VersificationError):
    def __init__(self, key: str, proposal: dict):
        super().__init__(f"no reviewed Douay-Rheims mapping for {key}")
        self.key = key
        self.proposal = proposal


def psalm_hebrew_to_douay(psalm: int, verse: int) -> Ref:
    """Hebrew psalm numbering (used by the US Lectionary) -> Douay-Rheims."""
    if psalm <= 9 or psalm >= 148:
        return psalm, verse
    if psalm == 10:
        return 9, verse + 21
    if psalm <= 113:
        return psalm - 1, verse
    if psalm == 114:
        return 113, verse
    if psalm == 115:
        return 113, verse + 8
    if psalm == 116:
        return (114, verse) if verse <= 9 else (115, verse - 9)
    if psalm <= 146:
        return psalm - 1, verse
    return (146, verse) if verse <= 11 else (147, verse - 11)


class TvtmsMap:
    """Verses in another tradition's numbering -> Latin (Vulgate) verses."""

    def __init__(self, mapping: dict[tuple[str, int, int], list[Ref]]):
        self._mapping = mapping

    @classmethod
    def parse(cls, text: str, tradition: str = "Hebrew") -> "TvtmsMap":
        douay_rows: dict[tuple[str, int, int], list[Ref]] = {}
        latin_rows: dict[tuple[str, int, int], list[Ref]] = {}
        inside = False
        for line in text.splitlines():
            if line.startswith("#DataStart(Expanded)"):
                inside = True
                continue
            if line.startswith("#DataEnd(Expanded)"):
                break
            columns = line.split("\t")
            if not inside or len(columns) < 8 or not columns[1].strip():
                continue
            types = {t.strip() for t in columns[0].split("+")}
            if "Latin2-DRA" in types:
                target = douay_rows
            elif "Latin" in types:
                target = latin_rows
            else:
                continue
            ancient = dict(re.findall(r"(Hebrew|Latin|Greek)\s*=\s*([^•)]+)", columns[7]))
            other = re.fullmatch(r"(\d+):(\d+)[a-z]?", ancient.get(tradition, "").strip())
            source = re.fullmatch(r"(\w+)\.(\d+):(\d+)(?:!\w+)?", columns[1].strip())
            if not other or not source:
                continue
            key = (source.group(1), int(other.group(1)), int(other.group(2)))
            latin = (int(source.group(2)), int(source.group(3)))
            refs = target.setdefault(key, [])
            if latin not in refs:
                refs.append(latin)
        merged = {**latin_rows, **douay_rows}
        return cls({key: sorted(refs) for key, refs in merged.items()})

    def latin_for(self, book: str, chapter: int, verse: int) -> list[Ref] | None:
        return self._mapping.get((book, chapter, verse))


@dataclass(frozen=True)
class DouayPassage:
    book: str
    ranges: tuple[Range, ...]
    differs: bool    # Douay-Rheims numbering differs from the citation
    partial: bool    # the citation names verse parts (a, b, ...); whole verses are shown


class Versifier:
    def __init__(self, douay: DouayIndex, hebrew: TvtmsMap, greek: TvtmsMap | None = None, overrides: dict | None = None):
        self.douay = douay
        self.hebrew = hebrew
        self.greek = greek
        self.overrides = overrides or {}

    def convert(self, citation: Citation) -> DouayPassage:
        book = BY_ID[citation.book]
        partial = any(s.start.part or s.end.part for s in citation.spans)
        if book.tradition == "greek":
            return self._from_override(citation, partial)
        if citation.is_whole_chapter:
            ranges = [self._whole_chapter(book, int(c)) for c in citation.chapters]
            differs = any(r[0] != int(c) for r, c in zip(ranges, citation.chapters))
            return DouayPassage(book.id, self._merge(book.id, ranges), differs, False)
        ranges, differs = [], False
        for span in citation.spans:
            start = self._point(book, span.start, first=True)
            end = self._point(book, span.end, first=False)
            if end < start:
                raise VersificationError(f"{citation_key(citation)} runs backwards in Douay-Rheims")
            modern = (_number(span.start.chapter), span.start.verse, _number(span.end.chapter), span.end.verse)
            if start + end != modern:
                differs = True
            ranges.append(start + end)
        return DouayPassage(book.id, self._merge(book.id, ranges), differs, partial)

    def propose(self, citation: Citation) -> dict:
        """Best-guess mapping for a reviewer, with the Douay text at each end."""
        ranges = [[*self._guess(citation.book, s.start, True), *self._guess(citation.book, s.end, False)] for s in citation.spans]
        if not ranges:
            ranges = [[int(c), 1, int(c), self.douay.chapter_len(citation.book, int(c))] for c in citation.chapters]
        return {
            "ranges": ranges,
            "first_verse": self.douay.text(citation.book, ranges[0][0], ranges[0][1]),
            "last_verse": self.douay.text(citation.book, ranges[-1][2], ranges[-1][3]),
        }

    def _point(self, book: Book, point: Point, first: bool) -> Ref:
        if not point.chapter.isdigit():
            ref = self._esther_addition(book, point)
        elif book.tradition == "latin":
            # The New Testament follows the Greek, which the Vulgate splits differently in a few places (Mark 9, Acts 14...).
            refs = self.greek.latin_for(book.tvtms, int(point.chapter), point.verse) if self.greek and book.testament == "new" else None
            ref = _pick(refs or [(int(point.chapter), point.verse)], point.part, first)
        else:
            refs = self.hebrew.latin_for(book.tvtms, int(point.chapter), point.verse)
            if not refs:
                if book.id == "PSA":
                    refs = [psalm_hebrew_to_douay(int(point.chapter), point.verse)]
                else:
                    refs = [(int(point.chapter), point.verse)]
            ref = _pick(refs, point.part, first)
        if not self.douay.has(book.id, *ref):
            raise VersificationError(
                f"{book.modern} {point.chapter}:{point.verse} maps to Douay-Rheims {ref[0]}:{ref[1]}, which does not exist")
        return ref

    def _esther_addition(self, book: Book, point: Point) -> Ref:
        if book.id != "EST":
            raise VersificationError(f"lettered chapter {point.chapter} only exists in Esther")
        for first, last, chapter, verse in ESTHER_ADDITIONS.get(point.chapter, []):
            if first <= point.verse <= last:
                return chapter, verse + point.verse - first
        raise VersificationError(f"Esther {point.chapter}:{point.verse} has no Douay-Rheims mapping")

    def _whole_chapter(self, book: Book, chapter: int) -> Range:
        start = psalm_hebrew_to_douay(chapter, 1) if book.id == "PSA" else (chapter, 1)
        length = self.douay.chapter_len(book.id, start[0])
        if length == 0:
            raise VersificationError(f"{book.modern} {chapter} does not exist in Douay-Rheims")
        return start[0], start[1], start[0], length

    def _from_override(self, citation: Citation, partial: bool) -> DouayPassage:
        key = citation_key(citation)
        entry = self.overrides.get(key)
        if entry is None:
            raise MissingOverride(key, self.propose(citation))
        ranges = tuple(tuple(r) for r in entry["ranges"])
        for r in ranges:
            if not (self.douay.has(citation.book, r[0], r[1]) and self.douay.has(citation.book, r[2], r[3])):
                raise VersificationError(f"override for {key} points outside Douay-Rheims: {r}")
        modern = tuple((_number(s.start.chapter), s.start.verse, _number(s.end.chapter), s.end.verse) for s in citation.spans)
        return DouayPassage(citation.book, ranges, ranges != modern, partial)

    def _guess(self, book_id: str, point: Point, first: bool) -> Ref:
        book = BY_ID[book_id]
        refs = self.greek.latin_for(book.tvtms, _number(point.chapter), point.verse) if self.greek else None
        return _pick(refs or [(_number(point.chapter), point.verse)], point.part, first)

    def _merge(self, book: str, ranges: list[Range]) -> tuple[Range, ...]:
        merged: list[Range] = []
        for r in ranges:
            if merged and self._continues(book, merged[-1], r):
                previous = merged.pop()
                end = max((previous[2], previous[3]), (r[2], r[3]))
                merged.append((previous[0], previous[1], *end))
            else:
                merged.append(r)
        return tuple(merged)

    def _continues(self, book: str, a: Range, b: Range) -> bool:
        """True when b starts inside a or on the verse right after it."""
        start, end, next_start = (a[0], a[1]), (a[2], a[3]), (b[0], b[1])
        if start <= next_start <= end:
            return True
        following = (a[2], a[3] + 1) if a[3] < self.douay.chapter_len(book, a[2]) else (a[2] + 1, 1)
        return next_start == following


def format_passage(passage: DouayPassage, douay: DouayIndex) -> str:
    """'Isaias 9:2-7', 'Psalm 115:3-4, 6-9', 'Matthew 26:14-27:66'."""
    chapters = {c for r in passage.ranges for c in (r[0], r[2])}
    if passage.book == "PSA":
        name = "Psalm" if len(chapters) == 1 else "Psalms"
    else:
        name = douay.name(passage.book)
    text, last_chapter = "", None
    for c1, v1, c2, v2 in passage.ranges:
        if c1 == c2:
            body = f"{v1}" if v1 == v2 else f"{v1}-{v2}"
            text += f", {body}" if c1 == last_chapter else f"{'; ' if text else ''}{c1}:{body}"
        else:
            text += f"{'; ' if text else ''}{c1}:{v1}-{c2}:{v2}"
        last_chapter = c2
    return f"{name} {text}"


def _pick(refs: list[Ref], part: str, first: bool) -> Ref:
    if len(refs) == 1:
        return refs[0]
    if part:
        return refs[0] if part.startswith("a") else refs[-1]
    return refs[0] if first else refs[-1]


def _number(chapter: str) -> int:
    return int(chapter) if chapter.isdigit() else -1
