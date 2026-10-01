import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/liturgy/liturgy.dart';

import '../support/calendar_fixture.dart';

void main() {
  final calendar = fixtureCalendar();

  test('reads a day with its readings', () {
    final day = calendar.dayFor(DateTime(2026, 10, 4, 15, 30))!;
    expect(day.name, '27th Sunday of Ordinary Time');
    expect(day.date, DateTime(2026, 10, 4));
    expect(dayDescription(day), 'Green · Ordinary Time');
    final readings = day.masses.single.readings;
    expect(readings.map((r) => r.kind), ['first_reading', 'responsorial_psalm', 'gospel_acclamation', 'gospel']);
    expect(readings.first.numberingDiffers, isTrue);
    expect(readings.first.douayCitation, 'Isaias 9:2-7');
    expect(readings.first.passages.single.bookId, 'ISA');
    expect(readings[1].partialVerses, isTrue);
    expect(readings.last.alternatives, ['John 3:16-17']);
    expect(day.gospel!.citation, 'John 3:16-18');
  });

  test('knows its date range', () {
    expect(calendar.covers(DateTime(2026, 10, 3)), isTrue);
    expect(calendar.covers(DateTime(2026, 10, 6, 23, 59)), isTrue);
    expect(calendar.covers(DateTime(2026, 10, 7)), isFalse);
    expect(calendar.dayFor(DateTime(2026, 10, 7)), isNull);
  });

  test('describes rank, colors and several Masses', () {
    final day = calendar.dayFor(DateTime(2026, 10, 6))!;
    expect(dayDescription(day), 'White · Ordinary Time · Memorial');
    expect(day.masses.map((m) => m.title), [null, 'Vigil Mass (evening)']);
    expect(colorLabel(['purple', 'pink']), 'Violet or Rose');
  });

  test('formats date keys', () {
    expect(dateKey(DateTime(2026, 1, 5)), '2026-01-05');
  });
}
