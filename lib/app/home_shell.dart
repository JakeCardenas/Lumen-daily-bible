import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../features/bible/bible_screen.dart';
import '../features/saved/saved_screen.dart';
import '../features/today/today_screen.dart';
import 'shell_controller.dart';

/// Three labeled tabs, each with its own navigation stack.
class HomeShell extends StatelessWidget {
  const HomeShell({super.key});

  @override
  Widget build(BuildContext context) {
    final shell = context.watch<ShellController>();
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) return;
        if (!shell.handleBack()) SystemNavigator.pop();
      },
      child: Scaffold(
        body: IndexedStack(
          index: shell.index,
          children: [
            _TabNavigator(navigatorKey: shell.navigatorKeys[ShellController.today], root: const TodayScreen()),
            _TabNavigator(navigatorKey: shell.navigatorKeys[ShellController.bible], root: const BibleScreen()),
            _TabNavigator(navigatorKey: shell.navigatorKeys[ShellController.saved], root: const SavedScreen()),
          ],
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: shell.index,
          onDestinationSelected: shell.select,
          destinations: const [
            NavigationDestination(icon: Icon(Icons.today_outlined), selectedIcon: Icon(Icons.today), label: 'Today'),
            NavigationDestination(
                icon: Icon(Icons.menu_book_outlined), selectedIcon: Icon(Icons.menu_book), label: 'Bible'),
            NavigationDestination(
                icon: Icon(Icons.bookmark_border), selectedIcon: Icon(Icons.bookmark), label: 'Saved'),
          ],
        ),
      ),
    );
  }
}

class _TabNavigator extends StatelessWidget {
  const _TabNavigator({required this.navigatorKey, required this.root});

  final GlobalKey<NavigatorState> navigatorKey;
  final Widget root;

  @override
  Widget build(BuildContext context) => Navigator(
        key: navigatorKey,
        onGenerateRoute: (settings) => MaterialPageRoute<void>(settings: settings, builder: (_) => root),
      );
}
