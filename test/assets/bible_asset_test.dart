import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/bible.dart';
import 'package:lumen/bible/bible_search.dart';
import 'package:lumen/bible/reference_parser.dart';

void main() {
  final bible = Bible.fromJson(
      jsonDecode(File('assets/bible/douay_rheims.json').readAsStringSync()) as Map<String, dynamic>);

  test('has the 73 books of the Catholic Bible', () {
    expect(bible.books, hasLength(73));
    expect(bible.books.where((b) => b.testament == Testament.newTestament), hasLength(27));
  });

  test('contains well-known verses in Douay-Rheims numbering', () {
    expect(bible.book('PSA')!.chapters[21][0], contains('The Lord ruleth me'));
    expect(bible.book('PSA')!.verseCount(9), 39);
    expect(bible.book('JHN')!.chapters[2][15], contains('so loved the world'));
  });

  test('reference and word search work on the full text', () {
    expect(ReferenceParser(bible).parse('Psalm 23').first.label, 'Psalm 22');
    final search = BibleSearch(bible)..search('light'); // the first search builds the index
    final stopwatch = Stopwatch()..start();
    final result = search.search('shadow of death');
    expect(result.verses.any((v) => v.bookId == 'PSA' && v.chapter == 22 && v.number == 4), isTrue);
    // Timed after the index exists: the whole suite runs in parallel, so the index build is too noisy to time.
    expect(stopwatch.elapsed, lessThan(const Duration(seconds: 1)));
  });
}
