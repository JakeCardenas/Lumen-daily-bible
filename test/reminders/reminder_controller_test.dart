import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/reminders/reminder_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import '../support/fake_notification_gateway.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(tzdata.initializeTimeZones);

  late SharedPreferences prefs;
  late FakeNotificationGateway gateway;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    prefs = await SharedPreferences.getInstance();
    gateway = FakeNotificationGateway();
    tz.setLocalLocation(tz.UTC);
  });

  // 2026-10-04 13:00 UTC, 09:00 in New York, seen in whichever zone is current.
  tz.TZDateTime now() => tz.TZDateTime.from(DateTime.utc(2026, 10, 4, 13), tz.local);

  ReminderController controller() => ReminderController(
      prefs: prefs, gateway: gateway, lookup: (d) => (name: 'Day ${d.day}', gospel: 'John 3:16'), clock: now);

  test('never asks for permission before reminders are turned on', () async {
    final c = controller();
    await c.start();
    expect(gateway.requestCount, 0);
    expect(gateway.scheduled, isEmpty);
    expect(c.showPermissionHelp, isFalse);
  });

  test('turning reminders on asks once and schedules a daily reminder in local time', () async {
    final c = controller();
    await c.start();
    await c.setEnabled(true);
    expect(gateway.requestCount, 1);
    expect(c.settings.enabled, isTrue);
    expect(prefs.getBool('reminder.enabled'), isTrue);
    final reminder = gateway.scheduled.single;
    expect(reminder.repeatsDaily, isTrue);
    expect(reminder.when.location.name, 'America/New_York');
    expect((reminder.when.day, reminder.when.hour, reminder.when.minute), (5, 8, 0));
  });

  test('a denied request keeps reminders off and shows help', () async {
    gateway.grant = false;
    final c = controller();
    await c.setEnabled(true);
    expect(c.settings.enabled, isFalse);
    expect(c.showPermissionHelp, isTrue);
    expect(gateway.scheduled, isEmpty);
    await c.openSystemSettings();
    expect(gateway.openSettingsCount, 1);
  });

  test('turning reminders off cancels them and hides help', () async {
    final c = controller();
    await c.setEnabled(true);
    await c.setEnabled(false);
    expect(gateway.scheduled, isEmpty);
    expect(c.settings.enabled, isFalse);
    expect(c.showPermissionHelp, isFalse);
  });

  test('changing the time reschedules', () async {
    final c = controller();
    await c.setEnabled(true);
    await c.setTime(21, 15);
    final reminder = gateway.scheduled.single;
    expect((reminder.when.day, reminder.when.hour, reminder.when.minute), (4, 21, 15));
  });

  test('previews schedule 60 days with date payloads', () async {
    final c = controller();
    await c.setEnabled(true);
    await c.setShowDetails(true);
    expect(gateway.scheduled, hasLength(60));
    expect(gateway.scheduled.first.payload, 'day:2026-10-05');
    expect(gateway.scheduled.first.body, 'Day 5 · Gospel: John 3:16');
  });

  test('settings survive a restart and reminders are refreshed at launch', () async {
    await controller().setEnabled(true);
    gateway.scheduled.clear();
    final restarted = controller();
    expect(restarted.settings.enabled, isTrue);
    await restarted.start();
    expect(gateway.scheduled, hasLength(1));
    expect(gateway.requestCount, 1);
  });

  test('notifications turned off in phone settings show help on resume', () async {
    final c = controller();
    await c.setEnabled(true);
    gateway.allowed = false;
    await c.onResume();
    expect(c.showPermissionHelp, isTrue);
    expect(c.settings.enabled, isTrue);
  });

  test('a time zone change on resume reschedules in the new zone', () async {
    final c = controller();
    await c.start();
    await c.setEnabled(true);
    gateway.zone = 'America/Los_Angeles';
    await c.onResume();
    final reminder = gateway.scheduled.single;
    expect(reminder.when.location.name, 'America/Los_Angeles');
    expect((reminder.when.day, reminder.when.hour), (4, 8));
  });

  test('a scheduling failure is reported, not thrown', () async {
    gateway.failSchedule = true;
    final c = controller();
    await c.setEnabled(true);
    expect(c.schedulingFailed, isTrue);
  });
}
