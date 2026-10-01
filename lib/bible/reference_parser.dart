import 'bible.dart';
import 'psalm_numbering.dart';

/// Lowercases and simplifies a book name: "II Cor." -> "2 cor", "1Kgs" -> "1 kgs".
/// Mirrors `normalize_name` in tool/lumen_data/books.py.
String normalizeBookName(String name) {
  var text = name.toLowerCase().replaceAll('.', ' ').replaceAll('’', "'").replaceAll(RegExp(r'\s+'), ' ').trim();
  text = text.replaceFirst(RegExp(r'^(st|saint|the) '), '');
  const numberWords = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'first': '1', 'second': '2', 'third': '3', 'fourth': '4'};
  final parts = text.split(' ');
  if (parts.length > 1 && numberWords.containsKey(parts.first)) parts[0] = numberWords[parts.first]!;
  return parts.join(' ').replaceFirstMapped(RegExp(r'^([1-4])(?=[a-z])'), (m) => '${m[1]} ');
}

class ReferenceMatch {
  const ReferenceMatch({required this.bookId, required this.chapter, this.verse, required this.label, this.note});

  final String bookId;
  final int chapter;
  final int? verse;
  final String label;
  final String? note;
}

/// Reads typed references such as "John 3:16", "Isaiah 9" or "Ps 23".
class ReferenceParser {
  ReferenceParser(this._bible)
      : _aliases = {for (final b in _bible.books) for (final a in b.aliases) normalizeBookName(a): b.id};

  final Bible _bible;
  final Map<String, String> _aliases;
  static final _pattern = RegExp(r'^\s*([1-4]?\s*[A-Za-z][A-Za-z .]*?)\s*(\d+)(?:\s*[:.,]\s*(\d+))?\s*$');

  List<ReferenceMatch> parse(String input) {
    final match = _pattern.firstMatch(input);
    if (match == null) return const [];
    final bookId = _aliases[normalizeBookName(match[1]!)];
    final book = bookId == null ? null : _bible.book(bookId);
    if (book == null) return const [];
    final chapter = int.parse(match[2]!);
    final verse = match[3] == null ? null : int.parse(match[3]!);
    final results = <ReferenceMatch>[];
    if (book.id == 'PSA') {
      final (douayChapter, douayVerse) = hebrewToDouayPsalm(chapter, verse ?? 1);
      final target = verse != null ? douayVerse : (douayVerse == 1 ? null : douayVerse);
      if (douayChapter != chapter || target != verse) {
        final modern = verse == null ? '$chapter' : '$chapter:$verse';
        _add(results, book, douayChapter, target, note: 'Psalm $modern in most modern Bibles');
        _add(results, book, chapter, verse, note: 'Douay-Rheims numbering');
        return results;
      }
    }
    _add(results, book, chapter, verse);
    return results;
  }

  void _add(List<ReferenceMatch> out, Book book, int chapter, int? verse, {String? note}) {
    if (chapter < 1 || chapter > book.chapterCount) return;
    if (verse != null && (verse < 1 || verse > book.verseCount(chapter))) return;
    final name = book.id == 'PSA' ? 'Psalm' : book.name;
    out.add(ReferenceMatch(
      bookId: book.id,
      chapter: chapter,
      verse: verse,
      label: verse == null ? '$name $chapter' : '$name $chapter:$verse',
      note: note,
    ));
  }
}
