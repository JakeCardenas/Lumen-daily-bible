import 'dart:async';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../bible/bible.dart';
import '../bookmarks/bookmark_store.dart';
import '../liturgy/liturgy.dart';
import '../moods/moods.dart';
import '../reminders/notification_gateway.dart';
import '../reminders/reminder_controller.dart';
import '../reminders/reminder_planner.dart';
import '../theme.dart';
import '../today/today_controller.dart';
import 'app_scope.dart';
import 'home_shell.dart';
import 'shell_controller.dart';

class AppServices {
  const AppServices({
    required this.bible,
    required this.calendar,
    required this.moods,
    required this.prefs,
    required this.notifications,
  });

  final Bible bible;
  final LiturgicalCalendar calendar;
  final MoodLibrary moods;
  final SharedPreferences prefs;
  final NotificationGateway notifications;
}

/// Carries notification taps, which can arrive at any moment, to the app.
class NotificationRouter extends ChangeNotifier {
  NotificationRouter({String? initial}) : _pending = initial;

  String? _pending;

  void open(String? payload) {
    if (payload == null) return;
    _pending = payload;
    notifyListeners();
  }

  /// Returns the waiting payload once.
  String? take() {
    final payload = _pending;
    _pending = null;
    return payload;
  }
}

/// The date a notification payload refers to, or null if it is not one of Lumen's payloads.
DateTime? dateFromPayload(String? payload, DateTime now) {
  if (payload == null) return null;
  if (payload == todayPayload) return dateOnly(now);
  if (payload.startsWith('day:')) {
    final parsed = DateTime.tryParse(payload.substring(4));
    return parsed == null ? null : dateOnly(parsed);
  }
  return null;
}

/// What a reminder with Scripture previews says about [date].
DayPreview? previewFor(LiturgicalCalendar calendar, DateTime date) {
  final day = calendar.dayFor(date);
  return day == null ? null : (name: day.name, gospel: day.gospel?.citation);
}

class LumenApp extends StatefulWidget {
  const LumenApp({super.key, required this.services, required this.router, this.clock = DateTime.now});

  final AppServices services;
  final NotificationRouter router;
  final DateTime Function() clock;

  @override
  State<LumenApp> createState() => _LumenAppState();
}

class _LumenAppState extends State<LumenApp> {
  late final ShellController _shell = ShellController();
  late final TodayController _today = TodayController(calendar: widget.services.calendar, today: widget.clock());
  late final BookmarkStore _bookmarks = BookmarkStore(widget.services.prefs);
  late final ReminderController _reminders = ReminderController(
    prefs: widget.services.prefs,
    gateway: widget.services.notifications,
    lookup: (date) => previewFor(widget.services.calendar, date),
  );
  late final AppLifecycleListener _lifecycle;

  @override
  void initState() {
    super.initState();
    _lifecycle = AppLifecycleListener(onResume: _onResume);
    widget.router.addListener(_openFromNotification);
    _openFromNotification();
    unawaited(_reminders.start());
  }

  @override
  void dispose() {
    widget.router.removeListener(_openFromNotification);
    _lifecycle.dispose();
    _shell.dispose();
    _today.dispose();
    _bookmarks.dispose();
    _reminders.dispose();
    super.dispose();
  }

  void _onResume() {
    _today.refreshToday(widget.clock());
    unawaited(_reminders.onResume());
  }

  void _openFromNotification() {
    final date = dateFromPayload(widget.router.take(), widget.clock());
    if (date == null) return;
    _today.showDate(date);
    _shell.showToday();
  }

  @override
  Widget build(BuildContext context) => AppScope(
        bible: widget.services.bible,
        calendar: widget.services.calendar,
        moods: widget.services.moods,
        bookmarks: _bookmarks,
        today: _today,
        reminders: _reminders,
        shell: _shell,
        child: MaterialApp(
          title: 'Lumen',
          theme: lumenTheme(),
          debugShowCheckedModeBanner: false,
          home: const HomeShell(),
        ),
      );
}
