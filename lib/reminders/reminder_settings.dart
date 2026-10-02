import 'package:shared_preferences/shared_preferences.dart';

/// The user's daily reminder choices, stored on the device.
class ReminderSettings {
  const ReminderSettings({this.enabled = false, this.hour = 8, this.minute = 0, this.showDetails = false});

  factory ReminderSettings.read(SharedPreferences prefs) => ReminderSettings(
        enabled: prefs.getBool(_enabledKey) ?? false,
        hour: prefs.getInt(_hourKey) ?? 8,
        minute: prefs.getInt(_minuteKey) ?? 0,
        showDetails: prefs.getBool(_detailsKey) ?? false,
      );

  static const _enabledKey = 'reminder.enabled';
  static const _hourKey = 'reminder.hour';
  static const _minuteKey = 'reminder.minute';
  static const _detailsKey = 'reminder.showDetails';

  final bool enabled;
  final int hour;
  final int minute;

  /// Whether the notification preview names the day's celebration and Gospel.
  final bool showDetails;

  ReminderSettings copyWith({bool? enabled, int? hour, int? minute, bool? showDetails}) => ReminderSettings(
        enabled: enabled ?? this.enabled,
        hour: hour ?? this.hour,
        minute: minute ?? this.minute,
        showDetails: showDetails ?? this.showDetails,
      );

  Future<void> write(SharedPreferences prefs) async {
    await prefs.setBool(_enabledKey, enabled);
    await prefs.setInt(_hourKey, hour);
    await prefs.setInt(_minuteKey, minute);
    await prefs.setBool(_detailsKey, showDetails);
  }
}
