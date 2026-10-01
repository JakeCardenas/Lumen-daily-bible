"""Parses lectionary citations such as 'Psalm 51:3-4, 5-6ab, 12-13, 14 and 17'."""
import re
from dataclasses import dataclass

from .books import Book, find_book


class CitationError(ValueError):
    pass


@dataclass(frozen=True)
class Point:
    chapter: str      # digits, or a letter for Esther's additions ("C")
    verse: int
    part: str = ""    # verse-part letters as written, e.g. "ab"


@dataclass(frozen=True)
class Span:
    start: Point
    end: Point


@dataclass(frozen=True)
class Citation:
    book: str
    spans: tuple[Span, ...] = ()
    chapters: tuple[str, ...] = ()   # whole-chapter citations such as "Psalm 71"

    @property
    def is_whole_chapter(self) -> bool:
        return not self.spans


SINGLE_CHAPTER_BOOKS = frozenset({"OBA", "PHM", "2JN", "3JN", "JUD"})
_DASHES = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-"})
_PREFIX = re.compile(r"^(?:cf|see|or)\b\.?\s*", re.IGNORECASE)
_NAME = re.compile(r"^(?P<name>(?:[1-4]\s*)?[A-Za-z][A-Za-z.' ]*?)\s*(?P<rest>(?:\d|[A-F]\s*:).*)$")
_ITEM = re.compile(r"(?:(?P<c1>\d+|[A-F]):)?(?P<v1>\d+)(?P<p1>[a-h]*)(?:-(?:(?P<c2>\d+|[A-F]):)?(?P<v2>\d+)(?P<p2>[a-h]*))?")


def split_alternatives(text: str) -> list[str]:
    """'Luke 2:22-40|Luke 2:22-32' -> ['Luke 2:22-40', 'Luke 2:22-32']."""
    return [part.strip() for part in text.split("|") if part.strip()]


def parse(text: str) -> list[Citation]:
    """Parses one citation (no '|' alternatives). Returns one Citation per book."""
    cleaned = text.translate(_DASHES).strip().rstrip(".")
    cleaned = re.sub(r"\s+and\s+", ", ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    citations: list[Citation] = []
    book: Book | None = None
    for token in (t.strip() for t in cleaned.split(";")):
        token = _PREFIX.sub("", token).strip()
        if not token:
            continue
        found = _match_book(token, text)
        if found is not None:
            book, rest = found
        elif book is None:
            raise CitationError(f"no book name in {text!r}")
        else:
            rest = token
        citations.append(_parse_rest(book, rest, text))
    if not citations:
        raise CitationError(f"empty citation {text!r}")
    return _merge_same_book(citations)


def citation_key(citation: Citation) -> str:
    """Compact, formatting-independent key, e.g. 'SIR 3:2-6,12-14'."""
    if citation.is_whole_chapter:
        return f"{citation.book} {','.join(citation.chapters)}"
    parts, last_chapter = [], None
    for span in citation.spans:
        text = f"{span.start.verse}{span.start.part}"
        if span.end != span.start:
            end = f"{span.end.verse}{span.end.part}"
            text += f"-{end}" if span.end.chapter == span.start.chapter else f"-{span.end.chapter}:{end}"
        parts.append(text if span.start.chapter == last_chapter else f"{span.start.chapter}:{text}")
        last_chapter = span.end.chapter
    return f"{citation.book} {','.join(parts)}"


def _match_book(token: str, original: str) -> tuple[Book, str] | None:
    match = _NAME.match(token)
    if match is None:
        return None
    book = find_book(match.group("name"))
    if book is None:
        raise CitationError(f"unknown book {match.group('name')!r} in {original!r}")
    return book, match.group("rest").strip()


def _parse_rest(book: Book, rest: str, original: str) -> Citation:
    if book.id in SINGLE_CHAPTER_BOOKS and ":" not in rest:
        return Citation(book.id, _parse_items("1", rest, original))   # "Jude 17, 20b-25"
    dual = re.fullmatch(r"(?P<a>\d+)\s*\((?P<b>\d+)\)\s*(?::\s*(?P<v>.+))?", rest)
    if dual:
        a, b = int(dual.group("a")), int(dual.group("b"))
        chapter = str(max(a, b)) if book.id == "PSA" else str(a)   # the Hebrew psalm number is the larger
        if dual.group("v") is None:
            return Citation(book.id, chapters=(chapter,))
        return Citation(book.id, _parse_items(chapter, dual.group("v"), original))
    european = re.fullmatch(r"(?P<c>\d+),(?P<v>\d+[a-h]*)", rest)
    if european:
        return Citation(book.id, _parse_items(european.group("c"), european.group("v"), original))
    verses = re.fullmatch(r"(?P<c>\d+|[A-F])\s*:\s*(?P<v>.+)", rest)
    if verses:
        return Citation(book.id, _parse_items(verses.group("c"), verses.group("v"), original))
    whole = re.fullmatch(r"(?P<c>\d+)(?:\s*-\s*(?P<c2>\d+))?", rest)
    if whole:
        first, last = int(whole.group("c")), int(whole.group("c2") or whole.group("c"))
        return Citation(book.id, chapters=tuple(str(c) for c in range(first, last + 1)))
    raise CitationError(f"cannot read {rest!r} in {original!r}")


def _parse_items(chapter: str, text: str, original: str) -> tuple[Span, ...]:
    spans, current = [], chapter
    for item in (i.replace(" ", "") for i in text.split(",")):
        if not item:
            continue
        match = _ITEM.fullmatch(item)
        if match is None:
            raise CitationError(f"cannot read verses {item!r} in {original!r}")
        start_chapter = match.group("c1") or current
        start = Point(start_chapter, int(match.group("v1")), match.group("p1"))
        end = start
        if match.group("v2"):
            end = Point(match.group("c2") or start_chapter, int(match.group("v2")), match.group("p2"))
        spans.append(Span(start, end))
        current = end.chapter
    return tuple(spans)


def _merge_same_book(citations: list[Citation]) -> list[Citation]:
    merged: list[Citation] = []
    for citation in citations:
        previous = merged[-1] if merged else None
        if previous and previous.book == citation.book and previous.spans and citation.spans:
            merged[-1] = Citation(previous.book, previous.spans + citation.spans)
        else:
            merged.append(citation)
    return merged
