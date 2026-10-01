/// An inclusive range of verses in Douay-Rheims numbering.
class VerseRange {
  const VerseRange(this.startChapter, this.startVerse, this.endChapter, this.endVerse);

  factory VerseRange.fromJson(List<dynamic> json) =>
      VerseRange(json[0] as int, json[1] as int, json[2] as int, json[3] as int);

  final int startChapter;
  final int startVerse;
  final int endChapter;
  final int endVerse;

  List<int> toJson() => [startChapter, startVerse, endChapter, endVerse];

  @override
  bool operator ==(Object other) =>
      other is VerseRange &&
      other.startChapter == startChapter &&
      other.startVerse == startVerse &&
      other.endChapter == endChapter &&
      other.endVerse == endVerse;

  @override
  int get hashCode => Object.hash(startChapter, startVerse, endChapter, endVerse);

  @override
  String toString() => '$startChapter:$startVerse-$endChapter:$endVerse';
}

/// A passage in one book: one or more verse ranges.
class ScriptureRef {
  const ScriptureRef(this.bookId, this.ranges);

  factory ScriptureRef.fromJson(Map<String, dynamic> json) => ScriptureRef(
        json['book'] as String,
        [for (final r in json['ranges'] as List<dynamic>) VerseRange.fromJson(r as List<dynamic>)],
      );

  final String bookId;
  final List<VerseRange> ranges;

  Map<String, dynamic> toJson() => {
        'book': bookId,
        'ranges': [for (final r in ranges) r.toJson()],
      };

  /// Stable identity, e.g. `JHN:3:16-3:16`. Used to tell whether a passage is saved.
  String get key => '$bookId:${ranges.join(',')}';
}

/// Groups verse numbers within one chapter into consecutive ranges.
List<VerseRange> rangesForVerses(int chapter, Iterable<int> verses) {
  final sorted = verses.toSet().toList()..sort();
  final ranges = <VerseRange>[];
  for (final verse in sorted) {
    if (ranges.isNotEmpty && ranges.last.endVerse == verse - 1) {
      final last = ranges.removeLast();
      ranges.add(VerseRange(chapter, last.startVerse, chapter, verse));
    } else {
      ranges.add(VerseRange(chapter, verse, chapter, verse));
    }
  }
  return ranges;
}
