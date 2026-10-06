import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/features/mood/mood_screen.dart';
import 'package:lumen/features/today/today_screen.dart';

import '../support/harness.dart';

void main() {
  testWidgets('shows the day, its readings and numbering notes', (tester) async {
    useTallScreen(tester);
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const TodayScreen()));
    expect(find.text('Sunday, October 4, 2026'), findsOneWidget);
    expect(find.text('27th Sunday of Ordinary Time'), findsOneWidget);
    expect(find.text('Green · Ordinary Time'), findsOneWidget);
    expect(find.text('First Reading'), findsOneWidget);
    expect(find.text('Isaiah 9:1-6'), findsOneWidget);
    expect(find.text('Douay-Rheims: Isaias 9:2-7'), findsOneWidget);
    expect(find.textContaining('For a CHILD IS BORN'), findsOneWidget);
    expect(find.text('Verses cited in part are shown in full.'), findsOneWidget);
    expect(find.text('Or: John 3:16-17'), findsOneWidget);
    expect(find.text('Alleluia'), findsOneWidget);
  });

  test('optional memorials are labeled singular or plural', () {
    expect(optionalMemorialsLine(['Saint Bruno']), 'Optional memorial: Saint Bruno');
    expect(optionalMemorialsLine(['Saint Bruno', 'Blessed Marie Rose Durocher']),
        'Optional memorials: Saint Bruno; Blessed Marie Rose Durocher');
  });

  testWidgets('moves between days and back to today', (tester) async {
    useTallScreen(tester);
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const TodayScreen()));
    await tester.tap(find.text('Previous day'));
    await tester.pump();
    expect(find.text('Saturday of the 26th Week of Ordinary Time'), findsOneWidget);
    expect(find.text('Optional memorial: Saturday Memorial of the Blessed Virgin Mary'), findsOneWidget);
    expect(tester.widget<OutlinedButton>(find.widgetWithText(OutlinedButton, 'Previous day')).onPressed, isNull);
    await tester.tap(find.text('Back to today'));
    await tester.pump();
    expect(find.text('27th Sunday of Ordinary Time'), findsOneWidget);
  });

  testWidgets('chooses between several Masses', (tester) async {
    useTallScreen(tester);
    final deps = await TestDeps.create();
    deps.today.showDate(DateTime(2026, 10, 6));
    await tester.pumpWidget(deps.wrap(const TodayScreen()));
    expect(find.text('White · Ordinary Time · Memorial'), findsOneWidget);
    expect(find.text('Mass of the day'), findsOneWidget);
    expect(find.text('John 3:1-3'), findsOneWidget);
    await tester.tap(find.text('Vigil Mass (evening)'));
    await tester.pump();
    expect(find.text('John 3:17'), findsOneWidget);
  });

  testWidgets('saving a reading bookmarks it', (tester) async {
    useTallScreen(tester);
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const TodayScreen()));
    await tester.tap(find.widgetWithText(TextButton, 'Save').first);
    await tester.pump();
    expect(deps.bookmarks.items.single.label, 'Isaias 9:2-7');
    expect(find.widgetWithText(TextButton, 'Saved'), findsOneWidget);
  });

  testWidgets('explains dates outside the bundled calendar', (tester) async {
    final deps = await TestDeps.create(now: DateTime(2036, 1, 1, 9));
    await tester.pumpWidget(deps.wrap(const TodayScreen()));
    expect(find.text('Readings for this date are not included in this version of Lumen.'), findsOneWidget);
  });

  testWidgets('the mood section opens a mood page', (tester) async {
    useTallScreen(tester);
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const TodayScreen()));
    expect(find.text('How are you feeling?'), findsOneWidget);
    await tester.tap(find.widgetWithText(OutlinedButton, 'Sad'));
    await tester.pumpAndSettle();
    expect(find.text('Feeling sad'), findsOneWidget);
  });

  testWidgets('Today and a mood page fit at 200% text', (tester) async {
    withTextScale(tester, 2);
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const TodayScreen()));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.widgetWithText(OutlinedButton, 'Sad'), 400,
        scrollable: find.byType(Scrollable).first);
    await tester.pumpAndSettle(); // lay out the final scroll position before tapping
    await tester.tap(find.widgetWithText(OutlinedButton, 'Sad'));
    await tester.pumpAndSettle();
    // The mood page builds lazily, so scroll its own list until the button exists.
    await tester.scrollUntilVisible(find.text('Show a prayer'), 300,
        scrollable: find.descendant(of: find.byType(MoodScreen), matching: find.byType(Scrollable)).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Show a prayer'));
    await tester.pumpAndSettle();
    expect(find.text('Feeling sad'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
