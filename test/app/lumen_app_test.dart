import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/app/lumen_app.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../support/bible_fixture.dart';
import '../support/calendar_fixture.dart';
import '../support/fake_notification_gateway.dart';
import '../support/harness.dart';
import '../support/moods_fixture.dart';

Future<({FakeNotificationGateway gateway, NotificationRouter router})> pumpLumen(WidgetTester tester,
    {String? launchPayload, Map<String, Object> prefs = const {}}) async {
  ensureTimeZones();
  SharedPreferences.setMockInitialValues(prefs);
  final store = await SharedPreferences.getInstance();
  final gateway = FakeNotificationGateway();
  final router = NotificationRouter(initial: launchPayload);
  await tester.pumpWidget(LumenApp(
    services: AppServices(
        bible: fixtureBible(), calendar: fixtureCalendar(), moods: fixtureMoods(), prefs: store, notifications: gateway),
    router: router,
    clock: () => DateTime(2026, 10, 4, 9),
  ));
  await tester.pumpAndSettle();
  return (gateway: gateway, router: router);
}

Finder tab(String label) => find.widgetWithText(NavigationDestination, label);

void main() {
  testWidgets('opens on Today with three labeled tabs, without asking for notification permission', (tester) async {
    final app = await pumpLumen(tester);
    expect(find.text('27th Sunday of Ordinary Time'), findsOneWidget);
    expect(tab('Today'), findsOneWidget);
    expect(tab('Bible'), findsOneWidget);
    expect(tab('Saved'), findsOneWidget);
    expect(app.gateway.requestCount, 0);
  });

  testWidgets('reminders already on are refreshed at launch without a prompt', (tester) async {
    final app = await pumpLumen(tester, prefs: {'reminder.enabled': true});
    expect(app.gateway.scheduled, hasLength(1));
    expect(app.gateway.requestCount, 0);
  });

  testWidgets('switches tabs', (tester) async {
    await pumpLumen(tester);
    await tester.tap(tab('Bible'));
    await tester.pumpAndSettle();
    expect(find.text('Search the Bible'), findsOneWidget);
    await tester.tap(tab('Saved'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Passages you save will appear here.'), findsOneWidget);
  });

  testWidgets('a reminder that launched the app opens the day it was for', (tester) async {
    await pumpLumen(tester, launchPayload: 'day:2026-10-03');
    expect(find.text('Saturday of the 26th Week of Ordinary Time'), findsOneWidget);
  });

  testWidgets('a reminder tapped while the app is open switches to Today and that day', (tester) async {
    final app = await pumpLumen(tester);
    await tester.tap(tab('Bible'));
    await tester.pumpAndSettle();
    app.router.open('day:2026-10-05');
    await tester.pumpAndSettle();
    expect(find.text('Monday of the 27th Week of Ordinary Time'), findsOneWidget);
  });

  testWidgets('system back closes a pushed screen, then returns to Today from another tab', (tester) async {
    await pumpLumen(tester);
    await tester.tap(find.widgetWithText(TextButton, 'Settings'));
    await tester.pumpAndSettle();
    expect(find.text('Show Scripture in notification preview'), findsOneWidget);
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('27th Sunday of Ordinary Time'), findsOneWidget);

    await tester.tap(tab('Saved'));
    await tester.pumpAndSettle();
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('27th Sunday of Ordinary Time'), findsOneWidget);
  });

  test('reads notification payloads', () {
    final now = DateTime(2026, 10, 4, 9);
    expect(dateFromPayload('today', now), DateTime(2026, 10, 4));
    expect(dateFromPayload('day:2026-12-25', now), DateTime(2026, 12, 25));
    expect(dateFromPayload('day:not-a-date', now), isNull);
    expect(dateFromPayload('something-else', now), isNull);
    expect(dateFromPayload(null, now), isNull);
  });

  test('reminder previews name the celebration and Gospel', () {
    final preview = previewFor(fixtureCalendar(), DateTime(2026, 10, 4));
    expect(preview, (name: '27th Sunday of Ordinary Time', gospel: 'John 3:16-18'));
    expect(previewFor(fixtureCalendar(), DateTime(2030, 1, 1)), isNull);
  });
}
