import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/today/today_controller.dart';

import '../support/calendar_fixture.dart';

void main() {
  TodayController controller() => TodayController(calendar: fixtureCalendar(), today: DateTime(2026, 10, 4, 9));

  test('starts on today', () {
    final c = controller();
    expect(c.selectedDate, DateTime(2026, 10, 4));
    expect(c.isShowingToday, isTrue);
    expect(c.day!.name, '27th Sunday of Ordinary Time');
  });

  test('moves between days within the calendar', () {
    final c = controller()..previous();
    expect(c.selectedDate, DateTime(2026, 10, 3));
    expect(c.canGoBack, isFalse);
    c.previous();
    expect(c.selectedDate, DateTime(2026, 10, 3));
    c
      ..goToToday()
      ..next()
      ..next();
    expect(c.selectedDate, DateTime(2026, 10, 6));
    expect(c.canGoForward, isFalse);
  });

  test('shows a requested date, or today when it is outside the data', () {
    final c = controller()..showDate(DateTime(2026, 10, 5, 20));
    expect(c.selectedDate, DateTime(2026, 10, 5));
    c.showDate(DateTime(2030, 1, 1));
    expect(c.selectedDate, DateTime(2026, 10, 4));
  });

  test('chooses among several Masses and resets when the date changes', () {
    final c = controller()
      ..showDate(DateTime(2026, 10, 6))
      ..selectMass(1);
    expect(c.mass!.title, 'Vigil Mass (evening)');
    c.previous();
    expect(c.massIndex, 0);
  });

  test('follows the new day after midnight only when showing today', () {
    final c = controller()..refreshToday(DateTime(2026, 10, 5, 0, 5));
    expect(c.selectedDate, DateTime(2026, 10, 5));
    c
      ..previous()
      ..refreshToday(DateTime(2026, 10, 6, 0, 5));
    expect(c.selectedDate, DateTime(2026, 10, 4));
    expect(c.today, DateTime(2026, 10, 6));
  });

  test('notifies listeners on changes', () {
    final c = controller();
    var count = 0;
    c
      ..addListener(() => count++)
      ..next()
      ..selectMass(0);
    expect(count, 2);
  });
}
