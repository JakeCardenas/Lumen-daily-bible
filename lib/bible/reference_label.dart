import 'bible.dart';
import 'scripture_ref.dart';

/// "Psalm" for one psalm, "Psalms" for several, otherwise the Douay-Rheims book name.
String referenceBookName(Book? book, String bookId, {required bool singleChapter}) {
  if (book == null) return bookId;
  if (book.id == 'PSA') return singleChapter ? 'Psalm' : 'Psalms';
  return book.name;
}

/// "Isaias 9:2-7", "Psalm 115:3-4, 6-9", "Matthew 26:14-27:66".
String referenceLabel(Bible bible, ScriptureRef ref) {
  final chapters = {for (final r in ref.ranges) ...[r.startChapter, r.endChapter]};
  final name = referenceBookName(bible.book(ref.bookId), ref.bookId, singleChapter: chapters.length == 1);
  final buffer = StringBuffer();
  int? lastChapter;
  for (final r in ref.ranges) {
    if (r.startChapter == r.endChapter) {
      final body = r.startVerse == r.endVerse ? '${r.startVerse}' : '${r.startVerse}-${r.endVerse}';
      if (r.startChapter == lastChapter) {
        buffer.write(', $body');
      } else {
        if (buffer.isNotEmpty) buffer.write('; ');
        buffer.write('${r.startChapter}:$body');
      }
    } else {
      if (buffer.isNotEmpty) buffer.write('; ');
      buffer.write('${r.startChapter}:${r.startVerse}-${r.endChapter}:${r.endVerse}');
    }
    lastChapter = r.endChapter;
  }
  return '$name $buffer';
}

/// "John 3:16", "Psalm 22:1".
String verseLabel(Bible bible, Verse verse) =>
    '${referenceBookName(bible.book(verse.bookId), verse.bookId, singleChapter: true)} ${verse.chapter}:${verse.number}';
