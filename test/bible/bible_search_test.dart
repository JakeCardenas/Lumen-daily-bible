import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/bible_search.dart';

import '../support/bible_fixture.dart';

void main() {
  final search = BibleSearch(fixtureBible());

  test('finds verses containing every word, ignoring case and punctuation', () {
    final result = search.search('LOVED world');
    expect(result.verses.map((v) => '${v.bookId} ${v.chapter}:${v.number}'), ['JHN 3:16']);
    expect(result.terms, ['loved', 'world']);
  });

  test('matches the start of words only', () {
    expect(search.search('light').verses.map((v) => v.number), [3]);
    expect(search.search('ight').verses, isEmpty);
  });

  test('ignores queries without searchable words', () {
    expect(search.search('a').verses, isEmpty);
    expect(search.search('  !! ').verses, isEmpty);
  });

  test('stops at the limit and reports truncation', () {
    final result = search.search('placeholder', limit: 3);
    expect(result.verses, hasLength(3));
    expect(result.truncated, isTrue);
  });

  test('folds accents and punctuation', () {
    expect(normalizeForSearch('Thérèse’s  Œuvre'), 'therese s oeuvre');
  });
}
