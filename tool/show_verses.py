"""Prints Douay-Rheims verses for reviewing mappings, e.g.: python3 show_verses.py SIR 35:10-20"""
import json
import sys

from lumen_data.bible import DouayIndex
from lumen_data.books import find_book
from lumen_data.paths import ASSETS


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    book = find_book(sys.argv[1])
    if book is None:
        print(f"unknown book {sys.argv[1]}")
        return 1
    douay = DouayIndex(json.loads((ASSETS / "bible" / "douay_rheims.json").read_text(encoding="utf-8")))
    chapter_text, _, verses = sys.argv[2].partition(":")
    chapter = int(chapter_text)
    first, _, last = verses.partition("-")
    start = int(first) if first else 1
    end = int(last) if last else (start if first else douay.chapter_len(book.id, chapter))
    for verse in range(start, end + 1):
        print(f"{douay.name(book.id)} {chapter}:{verse}  {douay.text(book.id, chapter, verse)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
