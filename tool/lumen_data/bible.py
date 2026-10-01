"""Parses the eBible.org Douay-Rheims VPL file and builds the app's Bible asset."""
import re

from .books import BOOKS, BY_VPL, all_aliases

TRANSLATION = "Douay-Rheims Bible, 1899 American Edition"
SOURCE = "eBible.org (public domain)"
_LINE = re.compile(r"^(\S+) (\d+):(\d+) (.*)$")


class BibleFormatError(ValueError):
    pass


def parse_vpl(text: str) -> dict[str, dict[int, dict[int, str]]]:
    """Returns {book id: {chapter: {verse: text}}}."""
    verses: dict[str, dict[int, dict[int, str]]] = {}
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip().lstrip("﻿")
        if not line:
            continue
        match = _LINE.match(line)
        if not match:
            raise BibleFormatError(f"line {number}: cannot read {line[:60]!r}")
        book = BY_VPL.get(match.group(1))
        if book is None:
            raise BibleFormatError(f"line {number}: unknown book code {match.group(1)!r}")
        chapter, verse = int(match.group(2)), int(match.group(3))
        verses.setdefault(book.id, {}).setdefault(chapter, {})[verse] = match.group(4).strip()
    return verses


def build_bible(verses: dict[str, dict[int, dict[int, str]]], require_all: bool = True) -> tuple[dict, list[str]]:
    """Builds the asset dict. Missing verses become None and are listed in the returned gaps."""
    books, gaps = [], []
    for book in BOOKS:
        chapters = verses.get(book.id)
        if chapters is None:
            if require_all:
                raise BibleFormatError(f"missing book {book.id}")
            continue
        rows = []
        for chapter in range(1, max(chapters) + 1):
            found = chapters.get(chapter, {})
            row = []
            for verse in range(1, max(found, default=0) + 1):
                text = found.get(verse)
                if text is None:
                    gaps.append(f"{book.id} {chapter}:{verse}")
                row.append(text)
            if not row:
                gaps.append(f"{book.id} {chapter}")
            rows.append(row)
        books.append({
            "id": book.id,
            "name": book.douay,
            "modern": book.modern,
            "testament": book.testament,
            "aliases": all_aliases(book),
            "chapters": rows,
        })
    return {"translation": TRANSLATION, "source": SOURCE, "books": books}, gaps


class DouayIndex:
    """Read-only lookups over the built Bible asset."""

    def __init__(self, bible: dict):
        self._chapters = {b["id"]: b["chapters"] for b in bible["books"]}
        self._names = {b["id"]: b["name"] for b in bible["books"]}

    def name(self, book: str) -> str:
        return self._names[book]

    def chapter_len(self, book: str, chapter: int) -> int:
        chapters = self._chapters.get(book, [])
        return len(chapters[chapter - 1]) if 1 <= chapter <= len(chapters) else 0

    def text(self, book: str, chapter: int, verse: int) -> str | None:
        if not 1 <= verse <= self.chapter_len(book, chapter):
            return None
        return self._chapters[book][chapter - 1][verse - 1]

    def has(self, book: str, chapter: int, verse: int) -> bool:
        return self.text(book, chapter, verse) is not None
