import 'dart:io' show Platform;

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';

import 'notification_gateway.dart';
import 'reminder_planner.dart';

/// Local notifications through flutter_local_notifications: no remote push, no exact alarms,
/// no full-screen intents, and no permission prompt until [requestPermission].
class LocalNotificationGateway implements NotificationGateway {
  LocalNotificationGateway([FlutterLocalNotificationsPlugin? plugin])
      : _plugin = plugin ?? FlutterLocalNotificationsPlugin();

  static const _channelId = 'daily_reading';
  static const _channelName = 'Daily reading';
  static const _channelDescription = "An optional daily reminder to read the day's Scripture.";

  final FlutterLocalNotificationsPlugin _plugin;

  AndroidFlutterLocalNotificationsPlugin? get _android =>
      _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();

  IOSFlutterLocalNotificationsPlugin? get _ios =>
      _plugin.resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>();

  @override
  Future<void> initialize(void Function(String? payload) onTap) async {
    await _plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('ic_stat_lumen'),
        iOS: DarwinInitializationSettings(
          requestAlertPermission: false,
          requestBadgePermission: false,
          requestSoundPermission: false,
        ),
      ),
      onDidReceiveNotificationResponse: (response) => onTap(response.payload),
    );
  }

  @override
  Future<String?> launchPayload() async {
    final details = await _plugin.getNotificationAppLaunchDetails();
    if (details == null || !details.didNotificationLaunchApp) return null;
    return details.notificationResponse?.payload;
  }

  @override
  Future<bool> requestPermission() async {
    if (Platform.isIOS) return await _ios?.requestPermissions(alert: true, sound: true) ?? false;
    final granted = await _android?.requestNotificationsPermission();
    return granted ?? await notificationsAllowed();
  }

  @override
  Future<bool> notificationsAllowed() async {
    if (Platform.isIOS) return (await _ios?.checkPermissions())?.isEnabled ?? false;
    return await _android?.areNotificationsEnabled() ?? false;
  }

  @override
  Future<void> cancelAll() => _plugin.cancelAll();

  @override
  Future<void> schedule(PlannedNotification notification) => _plugin.zonedSchedule(
        id: notification.id,
        scheduledDate: notification.when,
        title: notification.title,
        body: notification.body,
        payload: notification.payload,
        notificationDetails: const NotificationDetails(
          android: AndroidNotificationDetails(
            _channelId,
            _channelName,
            channelDescription: _channelDescription,
            importance: Importance.defaultImportance,
            priority: Priority.defaultPriority,
            visibility: NotificationVisibility.private,
            category: AndroidNotificationCategory.reminder,
          ),
          iOS: DarwinNotificationDetails(interruptionLevel: InterruptionLevel.active, threadIdentifier: _channelId),
        ),
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
        matchDateTimeComponents: notification.repeatsDaily ? DateTimeComponents.time : null,
      );

  @override
  Future<void> openSettings() async {
    await _plugin.openAppNotificationSettings();
  }

  @override
  Future<String> currentTimeZone() async => (await FlutterTimezone.getLocalTimezone()).identifier;
}
