import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/scripture_ref.dart';
import 'package:lumen/bookmarks/bookmark.dart';
import 'package:lumen/features/saved/saved_screen.dart';

import '../support/harness.dart';

void main() {
  const john = ScriptureRef('JHN', [VerseRange(3, 16, 3, 16)]);

  testWidgets('explains how to save when empty', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const SavedScreen()));
    expect(find.textContaining('Passages you save will appear here.'), findsOneWidget);
  });

  testWidgets('lists a saved passage and opens it and its chapter', (tester) async {
    final deps = await TestDeps.create();
    await deps.bookmarks.add(Bookmark.forPassage(deps.bible, john, now: DateTime(2026, 10, 1)));
    await tester.pumpWidget(deps.wrap(const SavedScreen()));
    expect(find.text('John 3:16'), findsOneWidget);
    expect(find.textContaining('Saved Oct 1, 2026'), findsOneWidget);
    await tester.tap(find.text('John 3:16'));
    await tester.pumpAndSettle();
    expect(find.textContaining('so loved the world'), findsOneWidget);
    await tester.tap(find.text('Open chapter'));
    await tester.pumpAndSettle();
    expect(find.text('John 3'), findsOneWidget);
  });

  testWidgets('removes a saved passage', (tester) async {
    final deps = await TestDeps.create();
    await deps.bookmarks.add(Bookmark.forPassage(deps.bible, john));
    await tester.pumpWidget(deps.wrap(const SavedScreen()));
    await tester.tap(find.text('Remove'));
    await tester.pump();
    expect(deps.bookmarks.items, isEmpty);
    expect(find.textContaining('Passages you save will appear here.'), findsOneWidget);
  });

  testWidgets('fits at 200% text', (tester) async {
    withTextScale(tester, 2);
    final deps = await TestDeps.create();
    await deps.bookmarks.add(Bookmark.forPassage(deps.bible, john));
    await deps.bookmarks.add(Bookmark.forPassage(deps.bible, const ScriptureRef('PSA', [VerseRange(22, 1, 22, 6)])));
    await tester.pumpWidget(deps.wrap(const SavedScreen()));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
}
