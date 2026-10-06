import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/app/app_scope.dart';
import 'package:lumen/app/shell_controller.dart';
import 'package:lumen/bible/bible.dart';
import 'package:lumen/bookmarks/bookmark_store.dart';
import 'package:lumen/liturgy/liturgy.dart';
import 'package:lumen/moods/moods.dart';
import 'package:lumen/reminders/reminder_controller.dart';
import 'package:lumen/theme.dart';
import 'package:lumen/today/today_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import 'bible_fixture.dart';
import 'calendar_fixture.dart';
import 'fake_notification_gateway.dart';
import 'moods_fixture.dart';

var _zonesReady = false;

void ensureTimeZones() {
  if (_zonesReady) return;
  tzdata.initializeTimeZones();
  _zonesReady = true;
}

/// Everything a screen needs, built from fixtures. The clock defaults to Sunday 2026-10-04 09:00.
class TestDeps {
  TestDeps._({
    required this.bible,
    required this.calendar,
    required this.moods,
    required this.prefs,
    required this.gateway,
    required this.bookmarks,
    required this.today,
    required this.reminders,
    required this.shell,
  });

  static Future<TestDeps> create({DateTime? now, Map<String, Object> prefs = const {}}) async {
    ensureTimeZones();
    SharedPreferences.setMockInitialValues(prefs);
    final store = await SharedPreferences.getInstance();
    final clock = now ?? DateTime(2026, 10, 4, 9);
    final calendar = fixtureCalendar();
    final gateway = FakeNotificationGateway();
    return TestDeps._(
      bible: fixtureBible(),
      calendar: calendar,
      moods: fixtureMoods(),
      prefs: store,
      gateway: gateway,
      bookmarks: BookmarkStore(store),
      today: TodayController(calendar: calendar, today: clock),
      reminders: ReminderController(
          prefs: store, gateway: gateway, lookup: (_) => null, clock: () => tz.TZDateTime.from(clock, tz.local)),
      shell: ShellController(),
    );
  }

  final Bible bible;
  final LiturgicalCalendar calendar;
  final MoodLibrary moods;
  final SharedPreferences prefs;
  final FakeNotificationGateway gateway;
  final BookmarkStore bookmarks;
  final TodayController today;
  final ReminderController reminders;
  final ShellController shell;

  Widget wrap(Widget child, {TargetPlatform? platform}) => AppScope(
        bible: bible,
        calendar: calendar,
        moods: moods,
        bookmarks: bookmarks,
        today: today,
        reminders: reminders,
        shell: shell,
        child: MaterialApp(theme: lumenTheme().copyWith(platform: platform), home: child),
      );
}

/// A tall phone-width screen (360 x 3000), so long lists are fully built.
void useTallScreen(WidgetTester tester) {
  tester.view.physicalSize = const Size(1080, 9000);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
}

/// A 360 x 780 phone with the system text size at [scale] (2.0 = 200%).
void withTextScale(WidgetTester tester, double scale) {
  tester.platformDispatcher.textScaleFactorTestValue = scale;
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  tester.view.physicalSize = const Size(1080, 2340);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
}
