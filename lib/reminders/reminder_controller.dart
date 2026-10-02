import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/timezone.dart' as tz;

import 'notification_gateway.dart';
import 'reminder_planner.dart';
import 'reminder_settings.dart';

enum NotificationAccess { unknown, allowed, blocked }

/// Owns the daily reminder: permission, scheduling, and keeping the schedule current.
class ReminderController extends ChangeNotifier {
  ReminderController({
    required SharedPreferences prefs,
    required this._gateway,
    required this._lookup,
    tz.TZDateTime Function()? clock,
  })  : _prefs = prefs,
        _clock = clock ?? (() => tz.TZDateTime.now(tz.local)),
        _settings = ReminderSettings.read(prefs);

  static const _zoneKey = 'reminder.timeZone';
  static const _throughKey = 'reminder.scheduledThrough';

  /// Individual (preview) reminders are refilled when fewer than this many days remain.
  static const refillBelowDays = 30;

  final SharedPreferences _prefs;
  final NotificationGateway _gateway;
  final DayPreviewLookup _lookup;
  final tz.TZDateTime Function() _clock;

  ReminderSettings _settings;
  NotificationAccess _access = NotificationAccess.unknown;
  bool _schedulingFailed = false;
  bool _busy = false;
  bool _disposed = false;

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }

  /// Async work (permission prompts, scheduling) can finish after the app closes.
  @override
  void notifyListeners() {
    if (!_disposed) super.notifyListeners();
  }

  ReminderSettings get settings => _settings;
  NotificationAccess get access => _access;
  bool get schedulingFailed => _schedulingFailed;

  /// True while the permission prompt is showing.
  bool get busy => _busy;

  /// True when the phone blocks Lumen's notifications after the user asked for reminders.
  bool get showPermissionHelp => _access == NotificationAccess.blocked;

  /// Call once at launch. Never prompts for permission.
  Future<void> start() async {
    await _applyTimeZone();
    if (_settings.enabled) {
      _access = await _checkAccess();
      await _reschedule();
    }
    notifyListeners();
  }

  /// Call when the app returns to the foreground.
  Future<void> onResume() async {
    final zoneChanged = await _applyTimeZone();
    if (!_settings.enabled) return;
    _access = await _checkAccess();
    if (zoneChanged || _windowLow()) await _reschedule();
    notifyListeners();
  }

  Future<void> setEnabled(bool enabled) async {
    if (!enabled) {
      _settings = _settings.copyWith(enabled: false);
      _access = NotificationAccess.unknown;
      _schedulingFailed = false;
      await _settings.write(_prefs);
      await _prefs.remove(_throughKey);
      try {
        await _gateway.cancelAll();
      } catch (_) {
        // The plugin is unavailable, so nothing was scheduled.
      }
      notifyListeners();
      return;
    }
    _busy = true;
    notifyListeners();
    final granted = await _request();
    _busy = false;
    if (!granted) {
      _access = NotificationAccess.blocked;
      notifyListeners();
      return;
    }
    _access = NotificationAccess.allowed;
    _settings = _settings.copyWith(enabled: true);
    await _settings.write(_prefs);
    await _reschedule();
    notifyListeners();
  }

  Future<void> setTime(int hour, int minute) => _update(_settings.copyWith(hour: hour, minute: minute));

  Future<void> setShowDetails(bool showDetails) => _update(_settings.copyWith(showDetails: showDetails));

  Future<void> openSystemSettings() async {
    try {
      await _gateway.openSettings();
    } catch (_) {
      // Nothing more can be done; the help text still explains the steps.
    }
  }

  Future<void> _update(ReminderSettings next) async {
    _settings = next;
    await _settings.write(_prefs);
    if (_settings.enabled) await _reschedule();
    notifyListeners();
  }

  Future<void> _reschedule() async {
    try {
      await _gateway.cancelAll();
      final plan = planReminders(settings: _settings, now: _clock(), lookup: _lookup);
      for (final notification in plan) {
        await _gateway.schedule(notification);
      }
      final last = plan.isEmpty || plan.last.repeatsDaily ? null : plan.last.when;
      if (last == null) {
        await _prefs.remove(_throughKey);
      } else {
        await _prefs.setString(_throughKey, last.toUtc().toIso8601String());
      }
      _schedulingFailed = false;
    } catch (_) {
      _schedulingFailed = true;
    }
  }

  bool _windowLow() {
    if (!_settings.showDetails) return false;
    final through = DateTime.tryParse(_prefs.getString(_throughKey) ?? '');
    return through == null || through.difference(_clock()).inDays < refillBelowDays;
  }

  /// Points tz.local at the device's zone. Returns true when the zone changed since last time.
  Future<bool> _applyTimeZone() async {
    try {
      final name = await _gateway.currentTimeZone();
      tz.setLocalLocation(tz.getLocation(name));
      final changed = _prefs.getString(_zoneKey) != name;
      await _prefs.setString(_zoneKey, name);
      return changed;
    } catch (_) {
      return false; // keep the previous zone
    }
  }

  Future<NotificationAccess> _checkAccess() async {
    try {
      return await _gateway.notificationsAllowed() ? NotificationAccess.allowed : NotificationAccess.blocked;
    } catch (_) {
      return NotificationAccess.unknown;
    }
  }

  Future<bool> _request() async {
    try {
      return await _gateway.requestPermission();
    } catch (_) {
      return false;
    }
  }
}
