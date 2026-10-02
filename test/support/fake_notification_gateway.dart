import 'package:lumen/reminders/notification_gateway.dart';
import 'package:lumen/reminders/reminder_planner.dart';

class FakeNotificationGateway implements NotificationGateway {
  bool grant = true;
  bool allowed = true;
  String zone = 'America/New_York';
  String? launch;
  bool failSchedule = false;

  int requestCount = 0;
  int openSettingsCount = 0;
  final List<PlannedNotification> scheduled = [];
  void Function(String? payload)? onTap;

  @override
  Future<void> initialize(void Function(String? payload) onTap) async => this.onTap = onTap;

  @override
  Future<String?> launchPayload() async => launch;

  @override
  Future<bool> requestPermission() async {
    requestCount++;
    allowed = grant;
    return grant;
  }

  @override
  Future<bool> notificationsAllowed() async => allowed;

  @override
  Future<void> cancelAll() async => scheduled.clear();

  @override
  Future<void> schedule(PlannedNotification notification) async {
    if (failSchedule) throw StateError('scheduling failed');
    scheduled.add(notification);
  }

  @override
  Future<void> openSettings() async => openSettingsCount++;

  @override
  Future<String> currentTimeZone() async => zone;
}
