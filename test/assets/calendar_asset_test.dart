import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/bible.dart';
import 'package:lumen/liturgy/liturgy.dart';

void main() {
  final bible = Bible.fromJson(
      jsonDecode(File('assets/bible/douay_rheims.json').readAsStringSync()) as Map<String, dynamic>);
  final calendar = LiturgicalCalendar.fromJson(
      jsonDecode(File('assets/liturgy/calendar_us.json').readAsStringSync()) as Map<String, dynamic>);

  test('covers 2026 until the first Sunday AELF cannot supply yet', () {
    expect(calendar.first, DateTime(2026));
    expect(calendar.last, DateTime(2030, 2, 23));
  });

  test('every day has a Gospel and every reading resolves to Douay-Rheims text', () {
    for (var d = calendar.first; !d.isAfter(calendar.last); d = DateTime(d.year, d.month, d.day + 1)) {
      final day = calendar.dayFor(d);
      expect(day?.masses, isNotEmpty, reason: dateKey(d));
      for (final mass in day!.masses) {
        expect(mass.readings.any((r) => r.kind == 'gospel'), isTrue, reason: '${dateKey(d)} ${mass.title}');
        for (final reading in mass.readings) {
          for (final passage in reading.passages) {
            expect(bible.versesFor(passage), isNotEmpty, reason: '${dateKey(d)} ${reading.citation}');
          }
        }
      }
    }
  });

  test('known dates', () {
    expect(calendar.dayFor(DateTime(2026, 4, 5))!.name, contains('Easter'));
    final monday = calendar.dayFor(DateTime(2026, 10, 5))!;
    expect(monday.masses.first.readings.first.citation.replaceAll(' ', ''), 'Galatians1:6-12');
    expect(monday.gospel!.citation.replaceAll(' ', ''), 'Luke10:25-37');
    expect(calendar.dayFor(DateTime(2027, 5, 9))!.gospel!.citation, 'Mark 16:15-20'); // Ascension, Year B
  });
}
