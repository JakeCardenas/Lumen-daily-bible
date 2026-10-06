import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/features/mood/mood_screen.dart';
import 'package:lumen/moods/moods.dart';

import '../support/harness.dart';

void main() {
  testWidgets('shows a passage and reflection, and the prayer on request', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(MoodScreen(mood: deps.moods.moods.first)));
    expect(find.text('Feeling sad'), findsOneWidget);
    expect(find.text('Psalm 22:4'), findsOneWidget);
    expect(find.text('Psalm 23 in most modern Bibles'), findsOneWidget);
    expect(find.textContaining('shadow of death'), findsOneWidget);
    expect(find.text('Reflection one.'), findsOneWidget);
    expect(find.text('Prayer one.'), findsNothing);
    await tester.tap(find.text('Show a prayer'));
    await tester.pump();
    expect(find.text('Prayer one.'), findsOneWidget);
    expect(find.text('Hide prayer'), findsOneWidget);
  });

  testWidgets('offers another passage', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(MoodScreen(mood: deps.moods.moods.first)));
    await tester.tap(find.text('Another passage'));
    await tester.pump();
    expect(find.text('John 3:16'), findsOneWidget);
    expect(find.text('Reflection two.'), findsOneWidget);
  });

  testWidgets('crisis line for sad; the disclaimer on every mood', (tester) async {
    useTallScreen(tester);
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(MoodScreen(mood: deps.moods.moods.first)));
    expect(find.text(crisisMessage), findsOneWidget);
    expect(find.text(moodDisclaimer), findsOneWidget);
    await tester.pumpWidget(deps.wrap(MoodScreen(key: const ValueKey('grateful'), mood: deps.moods.moods.last)));
    expect(find.text(crisisMessage), findsNothing);
    expect(find.text(moodDisclaimer), findsOneWidget);
    expect(find.text('Another passage'), findsNothing);
  });

  testWidgets('saves the passage', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(MoodScreen(mood: deps.moods.moods.first)));
    await tester.tap(find.text('Save passage'));
    await tester.pump();
    expect(deps.bookmarks.items.single.label, 'Psalm 22:4');
    expect(find.text('Saved'), findsOneWidget);
  });
}
