import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/reference_parser.dart';

import '../support/bible_fixture.dart';

void main() {
  final parser = ReferenceParser(fixtureBible());

  ReferenceMatch only(String input) {
    final results = parser.parse(input);
    expect(results, hasLength(1), reason: input);
    return results.single;
  }

  test('parses book, chapter and verse with common names', () {
    final match = only('John 3:16');
    expect((match.bookId, match.chapter, match.verse, match.label, match.note), ('JHN', 3, 16, 'John 3:16', null));
    expect(only('jn 3').verse, isNull);
    expect(only('Isaiah 9:6').label, 'Isaias 9:6');
    expect(only('1 Kings 2').bookId, '1KI');
    expect(only('1 Samuel 2').label, '1 Kings 2');
    expect(only('Ps 5').label, 'Psalm 5');
  });

  test('offers both readings of a modern psalm number', () {
    final results = parser.parse('Psalm 23');
    expect(results.map((r) => (r.label, r.note)),
        [('Psalm 22', 'Psalm 23 in most modern Bibles'), ('Psalm 23', 'Douay-Rheims numbering')]);
    final verse = parser.parse('Ps 23:4');
    expect(verse.map((r) => r.label), ['Psalm 22:4', 'Psalm 23:4']);
  });

  test('rejects text that is not a valid reference', () {
    expect(parser.parse('loved the world'), isEmpty);
    expect(parser.parse('John 30'), isEmpty);
    expect(parser.parse('John 3:99'), isEmpty);
    expect(parser.parse('Hezekiah 1'), isEmpty);
  });

  test('normalizes book names like the data build', () {
    expect(normalizeBookName('  II  Cor. '), '2 cor');
    expect(normalizeBookName('1Kgs'), '1 kgs');
  });
}
