import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/features/settings/settings_screen.dart';
import 'package:lumen/moods/moods.dart';

import '../support/harness.dart';

void main() {
  Finder reminderSwitch() => find.widgetWithText(SwitchListTile, 'Daily reminder');

  testWidgets('turning reminders on asks for permission only then, and schedules', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const SettingsScreen()));
    expect(deps.gateway.requestCount, 0);
    await tester.tap(reminderSwitch());
    await tester.pumpAndSettle();
    expect(deps.gateway.requestCount, 1);
    expect(deps.gateway.scheduled, hasLength(1));
    expect(tester.widget<SwitchListTile>(reminderSwitch()).value, isTrue);
    expect(find.text('8:00 AM'), findsOneWidget);
  });

  testWidgets('a denied request shows Android steps and an Open Settings button', (tester) async {
    final deps = await TestDeps.create();
    deps.gateway.grant = false;
    await tester.pumpWidget(deps.wrap(const SettingsScreen(), platform: TargetPlatform.android));
    await tester.tap(reminderSwitch());
    await tester.pumpAndSettle();
    expect(find.text('Notifications are off for Lumen'), findsOneWidget);
    expect(find.textContaining('tap Apps, choose Lumen, tap Notifications'), findsOneWidget);
    expect(find.textContaining('You can keep using Lumen without them.'), findsOneWidget);
    expect(tester.widget<SwitchListTile>(reminderSwitch()).value, isFalse);
    await tester.tap(find.text('Open Settings'));
    expect(deps.gateway.openSettingsCount, 1);
  });

  testWidgets('iPhone steps name the iOS settings path', (tester) async {
    final deps = await TestDeps.create();
    deps.gateway.grant = false;
    await tester.pumpWidget(deps.wrap(const SettingsScreen(), platform: TargetPlatform.iOS));
    await tester.tap(reminderSwitch());
    await tester.pumpAndSettle();
    expect(find.textContaining('turn on Allow Notifications'), findsOneWidget);
  });

  testWidgets('shows help when notifications were turned off in phone settings', (tester) async {
    final deps = await TestDeps.create(prefs: {'reminder.enabled': true});
    deps.gateway.allowed = false;
    await deps.reminders.start();
    await tester.pumpWidget(deps.wrap(const SettingsScreen()));
    expect(find.text('Notifications are off for Lumen'), findsOneWidget);
    expect(tester.widget<SwitchListTile>(reminderSwitch()).value, isTrue);
  });

  testWidgets('the preview switch schedules a reminder for each day', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const SettingsScreen()));
    await tester.tap(reminderSwitch());
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(SwitchListTile, 'Show Scripture in notification preview'));
    await tester.pumpAndSettle();
    expect(deps.gateway.scheduled, hasLength(60));
  });

  testWidgets('About lists sources and opens the licence page', (tester) async {
    useTallScreen(tester);
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const SettingsScreen()));
    expect(find.textContaining('Douay-Rheims Bible, 1899 American Edition'), findsOneWidget);
    expect(find.textContaining('Apache License 2.0'), findsOneWidget);
    expect(find.textContaining('AELF'), findsOneWidget);
    expect(find.textContaining('USCCB'), findsNothing);
    expect(find.textContaining('Readings are included through October 6, 2026.'), findsOneWidget);
    expect(find.textContaining('CC BY 4.0'), findsOneWidget);
    expect(find.text(moodDisclaimer), findsOneWidget);
    await tester.tap(find.text('View licenses'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));
    expect(find.byType(LicensePage), findsOneWidget);
  });
}
