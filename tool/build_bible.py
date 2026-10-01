"""Builds assets/bible/douay_rheims.json from eBible.org's Douay-Rheims 1899 (public domain).

Run from tool/: python3 build_bible.py
"""
import io
import json
import sys
import zipfile

from lumen_data.bible import build_bible, parse_vpl
from lumen_data.net import Fetcher
from lumen_data.paths import ASSETS, CACHE

URL = "https://ebible.org/Scriptures/engDRA_vpl.zip"


def main() -> int:
    raw = Fetcher().get(URL, CACHE / "ebible" / "engDRA_vpl.zip")
    if raw is None:
        print(f"download failed: {URL}", file=sys.stderr)
        return 1
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        text = archive.read("engDRA_vpl.txt").decode("utf-8-sig")
    bible, gaps = build_bible(parse_vpl(text))
    out = ASSETS / "bible" / "douay_rheims.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bible, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    verses = sum(1 for b in bible["books"] for c in b["chapters"] for v in c if v is not None)
    print(f"wrote {out}: {len(bible['books'])} books, {verses} verses, {len(gaps)} gaps")
    for gap in gaps[:20]:
        print("  gap:", gap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
