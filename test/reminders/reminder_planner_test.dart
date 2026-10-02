import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/reminders/reminder_planner.dart';
import 'package:lumen/reminders/reminder_settings.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

void main() {
  late tz.Location newYork;

  setUpAll(() {
    tzdata.initializeTimeZones();
    newYork = tz.getLocation('America/New_York');
  });

  DayPreview? preview(DateTime d) => (name: 'Day ${d.day}', gospel: 'John 3:16');
  tz.TZDateTime at(int y, int m, int d, int h, [int min = 0]) => tz.TZDateTime(newYork, y, m, d, h, min);

  test('nothing is planned while reminders are off', () {
    expect(planReminders(settings: const ReminderSettings(), now: at(2026, 10, 4, 9), lookup: preview), isEmpty);
  });

  test('a time already past today starts tomorrow', () {
    final plan = planReminders(settings: const ReminderSettings(enabled: true), now: at(2026, 10, 4, 9), lookup: preview);
    final reminder = plan.single;
    expect(reminder.when, at(2026, 10, 5, 8));
    expect(reminder.repeatsDaily, isTrue);
    expect(reminder.payload, 'today');
    expect(reminder.title, 'Lumen');
    expect(reminder.body, "Today's readings are ready.");
  });

  test('a later time today starts today', () {
    final plan = planReminders(
        settings: const ReminderSettings(enabled: true, hour: 20, minute: 30), now: at(2026, 10, 4, 9), lookup: preview);
    expect(plan.single.when, at(2026, 10, 4, 20, 30));
  });

  test('with previews on, each day gets its own reminder', () {
    final plan = planReminders(
        settings: const ReminderSettings(enabled: true, showDetails: true), now: at(2026, 10, 4, 9), lookup: preview);
    expect(plan, hasLength(60));
    expect(plan.map((n) => n.id).toSet(), {for (var i = 1; i <= 60; i++) i});
    expect(plan.first.payload, 'day:2026-10-05');
    expect(plan.first.body, 'Day 5 · Gospel: John 3:16');
    expect(plan.last.when, at(2026, 12, 3, 8));
    expect(plan.every((n) => !n.repeatsDaily), isTrue);
  });

  test('days without data use the generic text', () {
    final plan = planReminders(
        settings: const ReminderSettings(enabled: true, showDetails: true), now: at(2026, 10, 4, 9), lookup: (_) => null);
    expect(plan.first.body, "Today's readings are ready.");
    expect(previewBody((name: 'Ash Wednesday', gospel: null)), 'Ash Wednesday');
  });

  test('the reminder keeps its local time across daylight saving changes', () {
    final plan = planReminders(
        settings: const ReminderSettings(enabled: true, showDetails: true), now: at(2027, 3, 12, 9), lookup: preview);
    final before = plan.firstWhere((n) => n.when.month == 3 && n.when.day == 13);
    final after = plan.firstWhere((n) => n.when.month == 3 && n.when.day == 14);
    expect((before.when.hour, after.when.hour), (8, 8));
    expect((before.when.toUtc().hour, after.when.toUtc().hour), (13, 12));
  });
}
