import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

import '../bible/bible.dart';
import '../bible/bible_search.dart';
import '../bible/reference_parser.dart';
import '../bookmarks/bookmark_store.dart';
import '../liturgy/liturgy.dart';
import '../moods/moods.dart';
import '../reminders/reminder_controller.dart';
import '../today/today_controller.dart';
import 'shell_controller.dart';

/// Makes the app's data and controllers available to every screen.
class AppScope extends StatelessWidget {
  const AppScope({
    super.key,
    required this.bible,
    required this.calendar,
    required this.moods,
    required this.bookmarks,
    required this.today,
    required this.reminders,
    required this.shell,
    required this.child,
  });

  final Bible bible;
  final LiturgicalCalendar calendar;
  final MoodLibrary moods;
  final BookmarkStore bookmarks;
  final TodayController today;
  final ReminderController reminders;
  final ShellController shell;
  final Widget child;

  @override
  Widget build(BuildContext context) => MultiProvider(
        providers: [
          Provider<Bible>.value(value: bible),
          Provider<BibleSearch>(create: (_) => BibleSearch(bible)),
          Provider<ReferenceParser>(create: (_) => ReferenceParser(bible)),
          Provider<LiturgicalCalendar>.value(value: calendar),
          Provider<MoodLibrary>.value(value: moods),
          ChangeNotifierProvider<BookmarkStore>.value(value: bookmarks),
          ChangeNotifierProvider<TodayController>.value(value: today),
          ChangeNotifierProvider<ReminderController>.value(value: reminders),
          ChangeNotifierProvider<ShellController>.value(value: shell),
        ],
        child: child,
      );
}
