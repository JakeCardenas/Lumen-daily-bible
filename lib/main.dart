import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;

import 'app/licenses.dart';
import 'app/lumen_app.dart';
import 'bible/bible.dart';
import 'liturgy/liturgy.dart';
import 'moods/moods.dart';
import 'reminders/local_notification_gateway.dart';
import 'reminders/notification_gateway.dart';
import 'theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  tzdata.initializeTimeZones();
  registerLicenses();
  final router = NotificationRouter();
  final notifications = LocalNotificationGateway();
  try {
    final (bible, calendar, moods, prefs) =
        await (Bible.load(), LiturgicalCalendar.load(), MoodLibrary.load(), SharedPreferences.getInstance()).wait;
    await _startNotifications(notifications, router);
    runApp(LumenApp(
      services: AppServices(bible: bible, calendar: calendar, moods: moods, prefs: prefs, notifications: notifications),
      router: router,
    ));
  } catch (error, stack) {
    FlutterError.reportError(FlutterErrorDetails(exception: error, stack: stack, library: 'lumen startup'));
    runApp(const StartupErrorApp());
  }
}

/// Notifications are optional: if the plugin fails, Lumen still opens normally.
Future<void> _startNotifications(NotificationGateway gateway, NotificationRouter router) async {
  try {
    await gateway.initialize(router.open);
    router.open(await gateway.launchPayload());
  } catch (error, stack) {
    FlutterError.reportError(FlutterErrorDetails(exception: error, stack: stack, library: 'lumen notifications'));
  }
}

class StartupErrorApp extends StatelessWidget {
  const StartupErrorApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Lumen',
        theme: lumenTheme(),
        home: const Scaffold(
          body: SafeArea(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text("Lumen couldn't load its readings. Please reinstall the app."),
            ),
          ),
        ),
      );
}
