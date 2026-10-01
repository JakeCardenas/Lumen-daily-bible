import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/bible.dart';
import 'package:lumen/moods/moods.dart';

void main() {
  final bible = Bible.fromJson(
      jsonDecode(File('assets/bible/douay_rheims.json').readAsStringSync()) as Map<String, dynamic>);
  final library =
      MoodLibrary.fromJson(jsonDecode(File('assets/moods/moods.json').readAsStringSync()) as Map<String, dynamic>);

  test('offers the five moods, with the crisis line for sad and hopeless only', () {
    expect(library.moods.map((m) => m.label), ['Sad', 'Anxious', 'Hopeless', 'Happy', 'Grateful']);
    expect({for (final m in library.moods) m.id: m.crisisLine},
        {'sad': true, 'anxious': false, 'hopeless': true, 'happy': false, 'grateful': false});
  });

  test('every entry has text in the Douay-Rheims, a short reflection and a prayer', () {
    for (final mood in library.moods) {
      expect(mood.entries.length, inInclusiveRange(4, 6), reason: mood.id);
      for (final entry in mood.entries) {
        expect(bible.versesFor(entry.passage), isNotEmpty, reason: '${mood.id} ${entry.passage.key}');
        final sentences = RegExp(r'[.!?](\s|$)').allMatches(entry.reflection).length;
        expect(sentences, inInclusiveRange(2, 4), reason: entry.reflection);
        expect(entry.prayer, endsWith('Amen.'));
      }
    }
  });
}
