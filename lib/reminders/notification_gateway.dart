import 'reminder_planner.dart';

/// The notification plugin, behind an interface so reminder logic can be tested.
abstract interface class NotificationGateway {
  /// Prepares the plugin without asking for permission. [onTap] receives a tapped notification's payload.
  Future<void> initialize(void Function(String? payload) onTap);

  /// The payload of the notification that launched the app, if any.
  Future<String?> launchPayload();

  /// Shows the system permission prompt when the OS allows one. Returns whether notifications are allowed.
  Future<bool> requestPermission();

  /// Whether the OS currently allows Lumen's notifications.
  Future<bool> notificationsAllowed();

  Future<void> cancelAll();

  Future<void> schedule(PlannedNotification notification);

  /// Opens the phone's notification settings for Lumen.
  Future<void> openSettings();

  /// The device's IANA time zone, e.g. "America/Chicago".
  Future<String> currentTimeZone();
}
