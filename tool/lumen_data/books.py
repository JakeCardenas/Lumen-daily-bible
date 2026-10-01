"""The 73 books of the Catholic Bible in Douay-Rheims order, with every name used to cite them."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    id: str          # app id (USFM)
    vpl: str         # code in the eBible.org VPL file
    tvtms: str       # code in STEPBible TVTMS
    douay: str       # Douay-Rheims name
    modern: str      # common modern Catholic name
    testament: str   # "old" | "new"
    tradition: str   # numbering the US Lectionary follows: "hebrew" | "greek" | "latin"
    aliases: tuple[str, ...] = ()


_B = Book
BOOKS: tuple[Book, ...] = (
    _B("GEN", "GEN", "Gen", "Genesis", "Genesis", "old", "hebrew", ("gn", "gen")),
    _B("EXO", "EXO", "Exo", "Exodus", "Exodus", "old", "hebrew", ("ex", "exod", "exo")),
    _B("LEV", "LEV", "Lev", "Leviticus", "Leviticus", "old", "hebrew", ("lv", "lev")),
    _B("NUM", "NUM", "Num", "Numbers", "Numbers", "old", "hebrew", ("nm", "num")),
    _B("DEU", "DEU", "Deu", "Deuteronomy", "Deuteronomy", "old", "hebrew", ("dt", "deut")),
    _B("JOS", "JOS", "Jos", "Josue", "Joshua", "old", "hebrew", ("jos", "josh")),
    _B("JDG", "JDG", "Jdg", "Judges", "Judges", "old", "hebrew", ("jgs", "judg", "jdg")),
    _B("RUT", "RUT", "Rut", "Ruth", "Ruth", "old", "hebrew", ("ru", "rut")),
    _B("1SA", "1SA", "1Sa", "1 Kings", "1 Samuel", "old", "hebrew", ("1 sm", "1 sam", "1 samuel")),
    _B("2SA", "2SA", "2Sa", "2 Kings", "2 Samuel", "old", "hebrew", ("2 sm", "2 sam", "2 samuel")),
    _B("1KI", "1KI", "1Ki", "3 Kings", "1 Kings", "old", "hebrew", ("1 kgs", "1 kings", "3 kings", "3 kgs")),
    _B("2KI", "2KI", "2Ki", "4 Kings", "2 Kings", "old", "hebrew", ("2 kgs", "2 kings", "4 kings", "4 kgs")),
    _B("1CH", "1CH", "1Ch", "1 Paralipomenon", "1 Chronicles", "old", "hebrew", ("1 chr", "1 chron", "1 par")),
    _B("2CH", "2CH", "2Ch", "2 Paralipomenon", "2 Chronicles", "old", "hebrew", ("2 chr", "2 chron", "2 par")),
    _B("EZR", "EZR", "Ezr", "1 Esdras", "Ezra", "old", "hebrew", ("ezr", "1 esd")),
    _B("NEH", "NEH", "Neh", "2 Esdras", "Nehemiah", "old", "hebrew", ("neh", "2 esd")),
    _B("TOB", "TOB", "Tob", "Tobias", "Tobit", "old", "greek", ("tb", "tob")),
    _B("JDT", "JDT", "Jdt", "Judith", "Judith", "old", "greek", ("jdt",)),
    _B("EST", "EST", "Est", "Esther", "Esther", "old", "hebrew", ("est", "esth")),
    _B("JOB", "JOB", "Job", "Job", "Job", "old", "hebrew", ("jb",)),
    _B("PSA", "PSA", "Psa", "Psalms", "Psalms", "old", "hebrew", ("ps", "pss", "psalm", "psa")),
    _B("PRO", "PRO", "Pro", "Proverbs", "Proverbs", "old", "hebrew", ("prv", "prov", "pro")),
    _B("ECC", "ECC", "Ecc", "Ecclesiastes", "Ecclesiastes", "old", "hebrew", ("eccl", "eccles", "qoheleth", "ecc")),
    _B("SNG", "SOL", "Sng", "Canticle of Canticles", "Song of Songs", "old", "hebrew", ("sg", "song", "song of solomon", "canticles", "cant")),
    _B("WIS", "WIS", "Wis", "Wisdom", "Wisdom", "old", "greek", ("wis", "ws", "wisdom of solomon")),
    _B("SIR", "SIR", "Sir", "Ecclesiasticus", "Sirach", "old", "greek", ("sir", "ecclus")),
    _B("ISA", "ISA", "Isa", "Isaias", "Isaiah", "old", "hebrew", ("is", "isa")),
    _B("JER", "JER", "Jer", "Jeremias", "Jeremiah", "old", "hebrew", ("jer",)),
    _B("LAM", "LAM", "Lam", "Lamentations", "Lamentations", "old", "hebrew", ("lam",)),
    _B("BAR", "BAR", "Bar", "Baruch", "Baruch", "old", "greek", ("bar",)),
    _B("EZK", "EZE", "Ezk", "Ezechiel", "Ezekiel", "old", "hebrew", ("ez", "ezek", "eze")),
    _B("DAN", "DAN", "Dan", "Daniel", "Daniel", "old", "latin", ("dn", "dan")),
    _B("HOS", "HOS", "Hos", "Osee", "Hosea", "old", "hebrew", ("hos", "os")),
    _B("JOL", "JOE", "Jol", "Joel", "Joel", "old", "hebrew", ("jl",)),
    _B("AMO", "AMO", "Amo", "Amos", "Amos", "old", "hebrew", ("am",)),
    _B("OBA", "OBA", "Oba", "Abdias", "Obadiah", "old", "hebrew", ("ob", "obad")),
    _B("JON", "JON", "Jon", "Jonas", "Jonah", "old", "hebrew", ("jon",)),
    _B("MIC", "MIC", "Mic", "Micheas", "Micah", "old", "hebrew", ("mi", "mic")),
    _B("NAM", "NAH", "Nam", "Nahum", "Nahum", "old", "hebrew", ("na", "nah")),
    _B("HAB", "HAB", "Hab", "Habacuc", "Habakkuk", "old", "hebrew", ("hb", "hab")),
    _B("ZEP", "ZEP", "Zep", "Sophonias", "Zephaniah", "old", "hebrew", ("zep", "zeph")),
    _B("HAG", "HAG", "Hag", "Aggeus", "Haggai", "old", "hebrew", ("hg", "hag")),
    _B("ZEC", "ZEC", "Zec", "Zacharias", "Zechariah", "old", "hebrew", ("zec", "zech")),
    _B("MAL", "MAL", "Mal", "Malachias", "Malachi", "old", "hebrew", ("mal",)),
    _B("1MA", "1MA", "1Ma", "1 Machabees", "1 Maccabees", "old", "greek", ("1 mc", "1 macc")),
    _B("2MA", "2MA", "2Ma", "2 Machabees", "2 Maccabees", "old", "greek", ("2 mc", "2 macc")),
    _B("MAT", "MAT", "Mat", "Matthew", "Matthew", "new", "latin", ("mt", "matt")),
    _B("MRK", "MAR", "Mrk", "Mark", "Mark", "new", "latin", ("mk",)),
    _B("LUK", "LUK", "Luk", "Luke", "Luke", "new", "latin", ("lk",)),
    _B("JHN", "JOH", "Jhn", "John", "John", "new", "latin", ("jn",)),
    _B("ACT", "ACT", "Act", "Acts", "Acts", "new", "latin", ("acts of the apostles",)),
    _B("ROM", "ROM", "Rom", "Romans", "Romans", "new", "latin", ("rom",)),
    _B("1CO", "1CO", "1Co", "1 Corinthians", "1 Corinthians", "new", "latin", ("1 cor",)),
    _B("2CO", "2CO", "2Co", "2 Corinthians", "2 Corinthians", "new", "latin", ("2 cor",)),
    _B("GAL", "GAL", "Gal", "Galatians", "Galatians", "new", "latin", ("gal",)),
    _B("EPH", "EPH", "Eph", "Ephesians", "Ephesians", "new", "latin", ("eph",)),
    _B("PHP", "PHI", "Php", "Philippians", "Philippians", "new", "latin", ("phil", "php")),
    _B("COL", "COL", "Col", "Colossians", "Colossians", "new", "latin", ("col",)),
    _B("1TH", "1TH", "1Th", "1 Thessalonians", "1 Thessalonians", "new", "latin", ("1 thes", "1 thess")),
    _B("2TH", "2TH", "2Th", "2 Thessalonians", "2 Thessalonians", "new", "latin", ("2 thes", "2 thess")),
    _B("1TI", "1TI", "1Ti", "1 Timothy", "1 Timothy", "new", "latin", ("1 tm", "1 tim")),
    _B("2TI", "2TI", "2Ti", "2 Timothy", "2 Timothy", "new", "latin", ("2 tm", "2 tim")),
    _B("TIT", "TIT", "Tit", "Titus", "Titus", "new", "latin", ("ti", "tit")),
    _B("PHM", "PHM", "Phm", "Philemon", "Philemon", "new", "latin", ("phlm", "philem")),
    _B("HEB", "HEB", "Heb", "Hebrews", "Hebrews", "new", "latin", ("heb", "hewbrews")),
    _B("JAS", "JAM", "Jas", "James", "James", "new", "latin", ("jas",)),
    _B("1PE", "1PE", "1Pe", "1 Peter", "1 Peter", "new", "latin", ("1 pt", "1 pet")),
    _B("2PE", "2PE", "2Pe", "2 Peter", "2 Peter", "new", "latin", ("2 pt", "2 pet")),
    _B("1JN", "1JO", "1Jn", "1 John", "1 John", "new", "latin", ("1 jn",)),
    _B("2JN", "2JO", "2Jn", "2 John", "2 John", "new", "latin", ("2 jn",)),
    _B("3JN", "3JO", "3Jn", "3 John", "3 John", "new", "latin", ("3 jn",)),
    _B("JUD", "JUD", "Jud", "Jude", "Jude", "new", "latin", ()),
    _B("REV", "REV", "Rev", "Apocalypse", "Revelation", "new", "latin", ("rv", "rev", "apoc")),
)

BY_ID = {b.id: b for b in BOOKS}
BY_VPL = {b.vpl: b for b in BOOKS}

_NUMBER_WORDS = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "first": "1", "second": "2", "third": "3", "fourth": "4"}


def normalize_name(name: str) -> str:
    """'II Cor.' -> '2 cor', '1Kgs' -> '1 kgs'."""
    text = re.sub(r"\s+", " ", name.lower().replace(".", " ").replace("’", "'")).strip()
    text = re.sub(r"^(st|saint|the) ", "", text)
    parts = text.split(" ")
    if len(parts) > 1 and parts[0] in _NUMBER_WORDS:
        parts[0] = _NUMBER_WORDS[parts[0]]
    return re.sub(r"^([1-4])(?=[a-z])", r"\1 ", " ".join(parts))


def _build_lookup() -> dict[str, str]:
    table: dict[str, str] = {}
    for book in BOOKS:  # Douay names first, so modern names and aliases win ("1 Kings" is the modern 1 Kings).
        table[normalize_name(book.douay)] = book.id
    for book in BOOKS:
        for name in (book.id, book.modern, *book.aliases):
            table[normalize_name(name)] = book.id
    return table


LOOKUP = _build_lookup()


def find_book(name: str) -> Book | None:
    book_id = LOOKUP.get(normalize_name(name))
    return BY_ID[book_id] if book_id else None


def all_aliases(book: Book) -> list[str]:
    """Every normalized name that resolves to this book (shipped to the app for reference search)."""
    return sorted(name for name, book_id in LOOKUP.items() if book_id == book.id)
