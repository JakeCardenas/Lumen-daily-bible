import 'package:flutter/widgets.dart';

/// Which tab is showing, plus one navigator per tab.
class ShellController extends ChangeNotifier {
  static const today = 0;
  static const bible = 1;
  static const saved = 2;

  final List<GlobalKey<NavigatorState>> navigatorKeys = List.generate(3, (_) => GlobalKey<NavigatorState>());
  int _index = today;

  int get index => _index;

  /// Choosing the current tab again returns it to its first screen.
  void select(int index) {
    if (index == _index) {
      navigatorKeys[index].currentState?.popUntil((route) => route.isFirst);
      return;
    }
    _index = index;
    notifyListeners();
  }

  /// Shows the first screen of the Today tab (used when a reminder is tapped).
  void showToday() {
    navigatorKeys[today].currentState?.popUntil((route) => route.isFirst);
    if (_index != today) {
      _index = today;
      notifyListeners();
    }
  }

  /// Handles the system back gesture. Returns false when the app should close.
  bool handleBack() {
    final navigator = navigatorKeys[_index].currentState;
    if (navigator != null && navigator.canPop()) {
      navigator.pop();
      return true;
    }
    if (_index != today) {
      _index = today;
      notifyListeners();
      return true;
    }
    return false;
  }
}
