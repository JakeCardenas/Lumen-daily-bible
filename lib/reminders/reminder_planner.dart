import 'package:timezone/timezone.dart' as tz;

import '../liturgy/liturgy.dart';
import 'reminder_settings.dart';

typedef DayPreview = ({String name, String? gospel});
typedef DayPreviewLookup = DayPreview? Function(DateTime date);

const reminderTitle = 'Lumen';
const genericReminderBody = "Today's readings are ready.";

/// Opens the readings of the day the notification is tapped.
const todayPayload = 'today';

/// iOS keeps at most 64 pending notifications per app.
const detailsWindowDays = 60;

/// Opens the readings of [date], even when tapped later.
String dayPayload(DateTime date) => 'day:${dateKey(date)}';

class PlannedNotification {
  const PlannedNotification({
    required this.id,
    required this.when,
    required this.title,
    required this.body,
    required this.payload,
    required this.repeatsDaily,
  });

  final int id;
  final tz.TZDateTime when;
  final String title;
  final String body;
  final String payload;

  /// True for the single reminder that repeats daily at the same local time.
  final bool repeatsDaily;
}

/// Decides which notifications to schedule. Pure: it never calls the plugin.
List<PlannedNotification> planReminders({
  required ReminderSettings settings,
  required tz.TZDateTime now,
  required DayPreviewLookup lookup,
  int windowDays = detailsWindowDays,
}) {
  if (!settings.enabled) return const [];
  final first = nextOccurrence(now, settings.hour, settings.minute);
  if (!settings.showDetails) {
    return [
      PlannedNotification(
          id: 0, when: first, title: reminderTitle, body: genericReminderBody, payload: todayPayload, repeatsDaily: true),
    ];
  }
  return [
    for (var i = 0; i < windowDays; i++)
      _forDay(i + 1, tz.TZDateTime(first.location, first.year, first.month, first.day + i, settings.hour, settings.minute),
          lookup),
  ];
}

PlannedNotification _forDay(int id, tz.TZDateTime when, DayPreviewLookup lookup) {
  final day = DateTime(when.year, when.month, when.day);
  return PlannedNotification(
      id: id, when: when, title: reminderTitle, body: previewBody(lookup(day)), payload: dayPayload(day), repeatsDaily: false);
}

/// "27th Sunday of Ordinary Time · Gospel: Matthew 21:33-43".
String previewBody(DayPreview? preview) {
  if (preview == null) return genericReminderBody;
  final gospel = preview.gospel;
  return gospel == null ? preview.name : '${preview.name} · Gospel: $gospel';
}

/// The next [hour]:[minute] strictly after [now], in [now]'s time zone.
tz.TZDateTime nextOccurrence(tz.TZDateTime now, int hour, int minute) {
  final today = tz.TZDateTime(now.location, now.year, now.month, now.day, hour, minute);
  return today.isAfter(now) ? today : tz.TZDateTime(now.location, now.year, now.month, now.day + 1, hour, minute);
}
