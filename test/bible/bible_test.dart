import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/bible.dart';
import 'package:lumen/bible/psalm_numbering.dart';
import 'package:lumen/bible/reference_label.dart';
import 'package:lumen/bible/scripture_ref.dart';

import '../support/bible_fixture.dart';

void main() {
  final bible = fixtureBible();

  test('looks up books and names', () {
    expect(bible.books.map((b) => b.id), ['GEN', '1SA', '1KI', 'PSA', 'ISA', 'JHN']);
    expect(bible.book('ISA')!.displayName, 'Isaias (Isaiah)');
    expect(bible.book('JHN')!.displayName, 'John');
    expect(bible.book('PSA')!.verseCount(22), 6);
    expect(bible.book('PSA')!.verseCount(99), 0);
    expect(bible.book('XXX'), isNull);
  });

  test('returns verses for ranges, including across chapters', () {
    final verses = bible.versesFor(const ScriptureRef('PSA', [VerseRange(21, 4, 22, 2)]));
    expect(verses.map((v) => '${v.chapter}:${v.number}'), ['21:4', '21:5', '22:1', '22:2']);
    expect(verses[2].text, startsWith('A psalm for David'));
    expect(bible.versesFor(const ScriptureRef('PSA', [VerseRange(99, 1, 99, 3)])), isEmpty);
    expect(bible.versesFor(const ScriptureRef('XXX', [VerseRange(1, 1, 1, 1)])), isEmpty);
    expect(bible.chapter('GEN', 1), hasLength(3));
  });

  test('formats reference labels', () {
    expect(referenceLabel(bible, const ScriptureRef('ISA', [VerseRange(9, 2, 9, 7)])), 'Isaias 9:2-7');
    expect(referenceLabel(bible, const ScriptureRef('PSA', [VerseRange(22, 1, 22, 2), VerseRange(22, 4, 22, 4)])),
        'Psalm 22:1-2, 4');
    expect(referenceLabel(bible, const ScriptureRef('PSA', [VerseRange(21, 5, 22, 1)])), 'Psalms 21:5-22:1');
    expect(referenceLabel(bible, const ScriptureRef('JHN', [VerseRange(3, 16, 3, 16)])), 'John 3:16');
    expect(verseLabel(bible, const Verse('PSA', 22, 1, 'x')), 'Psalm 22:1');
  });

  test('groups selected verses into ranges', () {
    expect(rangesForVerses(3, [5, 1, 2, 3, 7]),
        const [VerseRange(3, 1, 3, 3), VerseRange(3, 5, 3, 5), VerseRange(3, 7, 3, 7)]);
  });

  test('converts modern psalm numbers to Douay-Rheims', () {
    expect(hebrewToDouayPsalm(23, 1), (22, 1));
    expect(hebrewToDouayPsalm(10, 1), (9, 22));
    expect(hebrewToDouayPsalm(116, 10), (115, 1));
    expect(hebrewToDouayPsalm(116, 9), (114, 9));
    expect(hebrewToDouayPsalm(115, 1), (113, 9));
    expect(hebrewToDouayPsalm(147, 12), (147, 1));
    expect(hebrewToDouayPsalm(147, 3), (146, 3));
    expect(hebrewToDouayPsalm(5, 2), (5, 2));
  });

  test('scripture refs round-trip through JSON with stable keys', () {
    const ref = ScriptureRef('JHN', [VerseRange(3, 16, 3, 18)]);
    expect(ScriptureRef.fromJson(ref.toJson()).key, ref.key);
    expect(ref.key, 'JHN:3:16-3:18');
  });
}
