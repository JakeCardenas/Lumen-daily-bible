import 'package:flutter/foundation.dart';

import '../liturgy/liturgy.dart';

/// Which date and Mass the Today tab is showing.
class TodayController extends ChangeNotifier {
  TodayController({required this.calendar, required DateTime today})
      : _today = dateOnly(today),
        _selected = dateOnly(today);

  final LiturgicalCalendar calendar;
  DateTime _today;
  DateTime _selected;
  int _massIndex = 0;

  DateTime get today => _today;
  DateTime get selectedDate => _selected;
  int get massIndex => _massIndex;
  bool get isShowingToday => _selected == _today;
  LiturgicalDay? get day => calendar.dayFor(_selected);

  Mass? get mass {
    final masses = day?.masses ?? const <Mass>[];
    if (masses.isEmpty) return null;
    return masses[_massIndex.clamp(0, masses.length - 1)];
  }

  bool get canGoBack => calendar.covers(_shift(-1));
  bool get canGoForward => calendar.covers(_shift(1));

  void previous() {
    if (canGoBack) _select(_shift(-1));
  }

  void next() {
    if (canGoForward) _select(_shift(1));
  }

  void goToToday() => _select(_today);

  /// Shows [date], or today when [date] is outside the bundled calendar.
  void showDate(DateTime date) => _select(calendar.covers(date) ? dateOnly(date) : _today);

  void selectMass(int index) {
    _massIndex = index;
    notifyListeners();
  }

  /// Call when the app resumes. Moves to the new day only if the user was looking at "today".
  void refreshToday(DateTime now) {
    final newToday = dateOnly(now);
    if (newToday == _today) return;
    final followToday = isShowingToday;
    _today = newToday;
    if (followToday) {
      _selected = newToday;
      _massIndex = 0;
    }
    notifyListeners();
  }

  DateTime _shift(int days) => DateTime(_selected.year, _selected.month, _selected.day + days);

  void _select(DateTime date) {
    _selected = date;
    _massIndex = 0;
    notifyListeners();
  }
}
