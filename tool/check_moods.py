"""Prints every mood passage from assets/moods/moods.json in Douay-Rheims for review.

Run from tool/: python3 check_moods.py
"""
import json
import sys

from lumen_data.bible import DouayIndex
from lumen_data.paths import ASSETS


def main() -> int:
    douay = DouayIndex(json.loads((ASSETS / "bible" / "douay_rheims.json").read_text(encoding="utf-8")))
    moods = json.loads((ASSETS / "moods" / "moods.json").read_text(encoding="utf-8"))["moods"]
    missing = 0
    for mood in moods:
        print(f"== {mood['label']}")
        for entry in mood["entries"]:
            book = entry["passage"]["book"]
            for c1, v1, c2, v2 in entry["passage"]["ranges"]:
                for chapter in range(c1, c2 + 1):
                    first = v1 if chapter == c1 else 1
                    last = v2 if chapter == c2 else douay.chapter_len(book, chapter)
                    for verse in range(first, last + 1):
                        text = douay.text(book, chapter, verse)
                        missing += text is None
                        print(f"  {book} {chapter}:{verse}  {text}")
            print()
    print(f"{missing} missing verses")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
